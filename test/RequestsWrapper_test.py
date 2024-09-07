import unittest
import sys
import os
import logging

if os.name == "nt":
    sys.path.append (f'{os.path.dirname(__file__) }\\..\\requests-proxy-rotation')
else:
    sys.path.append (f'{os.path.dirname(__file__) }/..')

from requests_proxy_rotation.requests_proxy_rotation import RequestsWrapper

logging.basicConfig()
log = logging.getLogger("LOG")

class Test_RequestsWrapper(unittest.TestCase):
    def setUp(self):
        # Need setup proxy on 192,168,0.103 first
        proxy_list = ["socks5://192.168.0.103:30000","socks5://192.168.0.103:30001","socks5://192.168.0.103:30002"]
        self.rq = RequestsWrapper(proxylist=proxy_list,verify_endpoint="http://example.com/")
        
    def test_get(self):
        self.rq.remove_rotator("https://api.ipify.org?format=json")
        self.rq.add_rotator("https://api.ipify.org?format=json",2)
        for i in range(5):
            self.rq.get("https://api.ipify.org?format=json").json()
        self.assertEqual({"api.ipify.org":1},self.rq.rotator_counter)
        self.assertEqual(2,self.rq.current_proxy["api.ipify.org"])
        
    def test_post(self):
        self.rq.remove_rotator("http://ip-api.com/batch")
        self.rq.add_rotator("http://ip-api.com/batch",2)
        for i in range(7):
            self.rq.post("http://ip-api.com/batch",data='[{"query": "208.80.152.201", "fields": "country"}, "8.8.8.8"]').json()
        self.assertEqual({"ip-api.com":1},self.rq.rotator_counter)
        self.assertEqual(0,self.rq.current_proxy["ip-api.com"])

    def test_request(self):
        self.rq.remove_rotator("https://api.ipify.org?format=json")
        self.rq.add_rotator("https://api.ipify.org?format=json",2)
        for i in range(5):
            self.rq.request("get","https://api.ipify.org?format=json").json()
        self.assertEqual({"api.ipify.org":1},self.rq.rotator_counter)
        self.assertEqual(2,self.rq.current_proxy["api.ipify.org"])


if __name__ == '__main__':
    unittest.main()