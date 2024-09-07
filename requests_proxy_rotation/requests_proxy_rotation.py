import requests
from urllib.parse import urlparse
import threading

lock = threading.Lock()

def get_domain(url):
    if "://" in url:
        return urlparse(url).netloc
    else:
        return url

class RequestsWrapper:
    def __init__(self,proxylist: list, verify_endpoint: str, timeout=10):
        self.rotator = {}
        self.rotator_counter = {}
        self.proxylist= proxylist
        self.current_proxy = {}
        self.verify_endpoint = verify_endpoint
        if requests.get(verify_endpoint).status_code != 200:
            raise Exception("Verify endpoint is invalid: Not response 200")
        self.timeout = timeout
    
    def add_rotator(self,domain:str,limit_times: int):
        d = get_domain(domain)
        if limit_times <= 0 :
            raise Exception("Limit times number is invalid")
        with lock:
            if not d in self.rotator:
                self.rotator[d] = limit_times
                self.rotator_counter[d] = 0
                self.current_proxy[d] = 0
            elif limit_times < self.rotator[d]:
                self.rotator[d] = limit_times
    
    def remove_rotator(self,domain:str):
        d = get_domain(domain)
        try:
            del self.rotator[d]
            del self.rotator_counter[d]
            del self.current_proxy[d]
        except:
            pass
    
    def _get_proxy(self,domain):
        if not domain in self.rotator:
            return {}
        cur_pro = {"http":self.proxylist[self.current_proxy[domain]],"https":self.proxylist[self.current_proxy[domain]]}
        count = 0
        while True:
            if count == len(self.proxylist):
                raise Exception("There is no alive proxy")
            if self.rotator_counter[domain] < self.rotator[domain] and requests.get(self.verify_endpoint, timeout=3, proxies=cur_pro).status_code == 200:
                with lock:
                    self.rotator_counter[domain] += 1
                return cur_pro
            else:
                self.current_proxy[domain] = (self.current_proxy[domain] + 1) % len(self.proxylist)
                self.rotator_counter[domain] = 0
                cur_pro = {"http":self.proxylist[self.current_proxy[domain]],"https":self.proxylist[self.current_proxy[domain]]}
                count += 1

    def get(self, url, params=None, headers=None):
        proxy = self._get_proxy(get_domain(url))
        return requests.get(url,params=params,headers=headers,proxies=proxy,timeout=self.timeout)

    def post(self, url, data=None, json=None, headers=None):
        proxy = self._get_proxy(get_domain(url))
        return requests.post(url, data=data, json=json, headers=headers,proxies=proxy,timeout=self.timeout)
    
    def request(self, method, url, *args, **kwargs):
        proxy = self._get_proxy(get_domain(url))
        if "proxies" in kwargs:
            kwargs.pop('proxies')
        if "timeout" in kwargs:
            kwargs.pop('timeout')
        return requests.request(method, url, proxies=proxy,timeout=self.timeout, *args, **kwargs)