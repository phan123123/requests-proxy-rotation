# requests-proxy-rotation
A wrapped version of requests. Help bypassing limitation of API by automatic rotating proxy.

## How to install
```bash
pip install requests_proxy_rotation
```
or
```bash
pip install git+https://github.com/phan123123/requests_proxy_rotation
```

## How to use
### Limit based mode
Requests will be sent with proxies one by one with a limit number
```python
from requests_proxy_rotation import RequestsWrapper

proxylist = ["socks5://123.123.123.123:8080","socks4://1.2.3.4:1234"]
verify_endpoint = "http://example.com" # using this endpoint to check proxy is alive or not
requests = RequestsWrapper(proxylist=proxy_list,verify_endpoint=verify_endpoint, mode = RequestsWrapper.LIMIT_BASED)

requests.add_rotator("domain_01",limit_times = 5) # domain_01 API with limit 5 times for each IP.
response = requests.get("http://domain_01/get_endpoint")
response = requests.post("http://domain_01/post_endpoint", data="test")
response = requests.request("method","http://domain_01", ...)
```
### Time based mode
Requests will be sent a limit of number with each limit times during a number of unit time.
```python
from requests_proxy_rotation import RequestsWrapper

proxylist = ["socks5://123.123.123.123:8080","socks4://1.2.3.4:1234"]
verify_endpoint = "http://example.com"
requests = RequestsWrapper(proxylist=proxy_list,verify_endpoint=verify_endpoint, mode = RequestsWrapper.TIME_BASED)

requests.add_rotator("domain_01",limit_times = 5, time_rate=(2,RequestsWrapper.UNIT_MIN)) # domain_01 API with limit 5 times for each IP in 2 minutes.
response = requests.get("http://domain_01/get_endpoint")
response = requests.post("http://domain_01/post_endpoint", data="test")
response = requests.request("method","http://domain_01", ...)
```
