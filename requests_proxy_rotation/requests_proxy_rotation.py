import requests
from urllib.parse import urlparse
import threading
from typing import Tuple
import time
import queue

lock = threading.Lock()
GAP_TIME = 3

class RotatorExecption(Exception):
    def __init__(self, message):
        super().__init__(f"[RotatorException] {message}")

class ConfigException(RotatorExecption):
    def __init__(self, message):
        super().__init__(f"[ConfigException] {message}")

class ProxyException(RotatorExecption):
    def __init__(self, message):
        super().__init__(f"[ProxyException] {message}")
        
def get_domain(url):
    if "://" in url:
        return urlparse(url).netloc
    else:
        return url

class RequestsWrapper:
    # Mode of rotator
    ''' LIMIT BASED mode: Using each proxy to request to target domain in inited limit times. 
    No timeout or time allocation.
    Proxy will be rotate around provided proxy list one by one.
    '''
    LIMIT_BASED = 0

    ''' TIME BASED mode: Using a proxy request to limited times in an unit time with as minium as posible proxies 
    '''
    TIME_BASED = 1

    # Time unit
    UNIT_NONE = 0
    UNIT_SEC = 1
    UNIT_MIN = 60
    UNIT_HOUR = 3600
    UNIT_DAY = 86400
    
    # properities
    rotator_limit = {}                  # Limit times of a IP (during a time)
    rotator_counter = {}                # Counter of reuqested times (during a time)
    rotator_timecount = {}              # Counter time to check limit of time unit for each domain
    proxylist= []                       # List of proxies
    current_proxy = {}                  # Current using proxy of each domain
    verify_endpoint = ""                # Endpoint which is used to check living proxy or not
    time_rate = {}                      # Save the limits of time based for each domain
    mode = LIMIT_BASED                  # Rotator's mode

    def __init__(self,proxylist: list, verify_endpoint: str, mode=LIMIT_BASED , timeout=10):
        self.proxylist = proxylist
        if mode != RequestsWrapper.LIMIT_BASED and mode != RequestsWrapper.TIME_BASED:
            raise ConfigException("Invalid mode")
        else:
            self.mode = mode
        try:
            if requests.get(verify_endpoint).status_code != 200:
                raise ConfigException(f"Verify endpoint {verify_endpoint} is invalid: Not response 200")
            else:
                self.verify_endpoint = verify_endpoint
        except:
            raise ConfigException(f"Verify endpoint {verify_endpoint} is invalid: Request error")
        self.timeout = timeout
    
    def add_rotator(self,domain:str,limit_times: int=0, time_rate: Tuple[int,int]=(0,UNIT_NONE)):
        d = get_domain(domain)
        if limit_times <= 0 :
            raise ConfigException(f"Limit times: {limit_times} is invalid")
        if time_rate[0] < 0 or (time_rate[1] not in [RequestsWrapper.UNIT_NONE,RequestsWrapper.UNIT_SEC,RequestsWrapper.UNIT_MIN,RequestsWrapper.UNIT_HOUR,RequestsWrapper.UNIT_DAY]):
            raise ConfigException(f"Time rate setting: {time_rate[0] * time_rate[1]} seconds is invalid")
        with lock:
            if not d in self.rotator_limit:
                if self.mode == RequestsWrapper.LIMIT_BASED:
                    self.rotator_limit[d] = limit_times
                    self.rotator_counter[d] = 0
                    self.current_proxy[d] = 0
                elif self.mode == RequestsWrapper.TIME_BASED:
                    self.rotator_limit[d] = (limit_times , time_rate[0] * time_rate[1])
                    self.rotator_counter[d] = {}
                    self.current_proxy[d] = -1
                    self.rotator_timecount[d] = {}
            else:
                if self.mode == RequestsWrapper.LIMIT_BASED:
                    self.rotator_limit[d] = limit_times
                elif self.mode == RequestsWrapper.TIME_BASED:
                    self.rotator_limit[d] = (limit_times , time_rate[0] * time_rate[1])
    
    def remove_rotator(self,domain:str):
        if self.mode == RequestsWrapper.LIMIT_BASED:
            self._remove_rotator_limit_based(get_domain(domain))
        elif self.mode == RequestsWrapper.TIME_BASED:
            self._remove_rotator_time_based(get_domain(domain))

    def _remove_rotator_time_based(self,d:str):
        try:
            del self.rotator_limit[d]
            del self.rotator_counter[d]
            del self.current_proxy[d]
            del self.rotator_timecount[d]
        except:
            pass

    def _remove_rotator_limit_based(self,d:str):
        try:
            del self.rotator_limit[d]
            del self.rotator_counter[d]
            del self.current_proxy[d]
        except:
            pass
    
    def _get_proxy(self,domain):
        if self.mode == RequestsWrapper.LIMIT_BASED:
            return self._get_proxy_limit_based(domain)
        elif self.mode == RequestsWrapper.TIME_BASED:
            return self._get_proxy_time_based(domain)
    

    def _get_proxy_time_based(self,domain):
        if not domain in self.rotator_limit:
            return {}

        # Go through in used proxy list
        for proxy_tmp in self.rotator_counter[domain]:
            # Check time range
            while True:
                if self.rotator_counter[domain][proxy_tmp] > 0:
                    oldest_time = self.rotator_timecount[domain][proxy_tmp].queue[0]           # get the oldest time of requesting from saved queue
                else:
                    self.rotator_timecount[domain][proxy_tmp].put(time.time())
                    self.rotator_counter[domain][proxy_tmp] += 1
                    return {"http":proxy_tmp,"https":proxy_tmp}
                if time.time() - oldest_time >= self.rotator_limit[domain][1]:
                    self.rotator_timecount[domain][proxy_tmp].get()                             # Delete the oldest time becasue it is over time limit
                    self.rotator_counter[domain][proxy_tmp] -= 1
                    continue
                elif self.rotator_counter[domain][proxy_tmp] < self.rotator_limit[domain][0]:
                    self.rotator_timecount[domain][proxy_tmp].put(time.time())
                    self.rotator_counter[domain][proxy_tmp] += 1
                    return {"http":proxy_tmp,"https":proxy_tmp}
                else:
                    # If this proxy is reach limit, find the next one
                    break

        # Try with all used proxies but not enough (try a round) -> just hold in second    
        proxy_tmp = self._find_next_proxy(domain)
        # If can not find a new and unsued proxy, hold senconds
        if proxy_tmp in self.rotator_counter[domain]:
            # proxy_size = len(self.proxylist)
            # raise ProxyException(f"Proxylist: f{proxy_size} items is not enough for limit of {self.rotator_limit[domain][0]} times in {self.rotator_limit[domain][1]} seconds")
            time.sleep(GAP_TIME)
        else:
            self.rotator_counter[domain][proxy_tmp] = 1
            self.rotator_timecount[domain][proxy_tmp] = queue.Queue()
            self.rotator_timecount[domain][proxy_tmp].put(time.time())
            return {"http":proxy_tmp,"https":proxy_tmp}

    def _get_proxy_limit_based(self,domain):
        if not domain in self.rotator_limit:
            return {}
        proxy = self.proxylist[self.current_proxy[domain]]
        if self.rotator_counter[domain] < self.rotator_limit[domain]:
            with lock:
                self.rotator_counter[domain] += 1
            return {"http":proxy,"https":proxy}
        else:
            proxy = self._find_next_proxy(domain)
            self.rotator_counter[domain] = 1
            return {"http":proxy,"https":proxy}

    def _find_next_proxy(self,domain):
        if not domain in self.rotator_limit:
            return {}
        count = 0
        index_tmp = (self.current_proxy[domain] + 1) % len(self.proxylist)
        while True:
            if count >= len(self.proxylist):
                raise ConfigException("There is no alive proxy")
            try:
                cur_pro = {"http":self.proxylist[index_tmp],"https":self.proxylist[index_tmp]}
                if requests.get(self.verify_endpoint, timeout=(self.timeout/2), proxies=cur_pro).status_code == 200:
                    with lock:
                        self.current_proxy[domain] = index_tmp
                    return self.proxylist[index_tmp]
                else:
                    index_tmp= (index_tmp + 1) % len(self.proxylist)
                    count += 1
            except:
                index_tmp= (index_tmp + 1) % len(self.proxylist)
                count += 1

    def get(self, url, *args, **kwargs):
        proxy = self._get_proxy(get_domain(url))
        if "proxies" in kwargs:
            kwargs.pop('proxies')
        if "timeout" in kwargs:
            kwargs.pop('timeout')
        return requests.get(url, proxies=proxy,timeout=self.timeout, *args, **kwargs)

    def post(self, url, *args, **kwargs):
        proxy = self._get_proxy(get_domain(url))
        if "proxies" in kwargs:
            kwargs.pop('proxies')
        if "timeout" in kwargs:
            kwargs.pop('timeout')
        return requests.post(url, proxies=proxy,timeout=self.timeout, *args, **kwargs)
    
    def request(self, method, url, *args, **kwargs):
        proxy = self._get_proxy(get_domain(url))
        if "proxies" in kwargs:
            kwargs.pop('proxies')
        if "timeout" in kwargs:
            kwargs.pop('timeout')
        return requests.request(method, url, proxies=proxy,timeout=self.timeout, *args, **kwargs)