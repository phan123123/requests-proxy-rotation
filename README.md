# requests-proxy-rotation
A wrapped version of requests. Allow automatic rotate proxy with limit of each endpoint

## How to install
`pip install git+https://github.com/phan123123/requests_proxy_rotation`

## How to use
```python
from requests_proxy_rotation import RequestsWrapper

proxylist = ["socks5://123.123.123.123:8080","socks4://1.2.3.4:1234"]
verify_endpoint = "http://example.com" # using this endpoint to check proxy is alive or not
requests = RequestsWrapper(proxylist=proxy_list,verify_endpoint=verify_endpoint)

requests.add_rotator("domain_01",limit_times = 5) # domain_01 API with limit 5 times for each IP.
response = requests.get("http://domain_01/get_endpoint")
response = requests.post("http://domain_01/post_endpoint", data="test")
response = requests.request("method","http://domain_01", ...)
```