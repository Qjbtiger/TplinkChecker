import requests
import json5
from encrypt import encrypt
from urllib.parse import quote

def encodeData(data):
    return quote('data=' + json5.dumps(data, separators=(',', ':'), quote_keys=True), safe='=')


class Checker(object):
    def __init__(self, config):
        self.ip = config['ip']
        self.username = config['username']
        self.password = config['password']
        self.session = requests.session()
        self.default_headers = {
            "User-Agent": config['headers']['User-Agent'],
            'Content-Type': config['headers']['Content-Type'],
        }
        self.isLogin = False
        self.stok = ''

    def login(self):
        # get public keys
        url = 'http://{}/cgi-bin/luci/;stok=/login?form=login'.format(self.ip)
        headers = self.default_headers
        headers['Referer'] = 'http://{}/webpages/login.html'.format(self.ip)
        data = {
            "method": "get"
        }
        response = self.session.post(url, headers = headers, data=encodeData(data))
        response = json5.loads(response.text)
        n = response['result']['password'][0]
        e = response['result']['password'][1]
        n = n.lower()
        e = int(e, 16)
        encrypted_message = encrypt(self.password, n, e)

        # send message
        data = {
            "method": "login",
            "params": {
                "username": self.username,
                "password": encrypted_message
            }
        }
        response = self.session.post(url, data=encodeData(data), headers=headers)
        response = json5.loads(response.text)
        if response['error_code'] == '0':
            self.stok = response['result']['stok']
            self.isLogin = True
            print('Login Success!')
        else:
            print('Login Fails!')

    def get_system_state(self):
        if not self.isLogin:
            print('You have not login yet!')
            return
        
        url = 'http://{}/cgi-bin/luci/;stok={}/admin/system_state?form=system_state'.format(self.ip, self.stok)
        headers = self.default_headers
        headers['Referer'] = 'http://{}/webpages/index.html'.format(self.ip)
        data = {
            "method": "get"
        }
        response = self.session.post(url, data=encodeData(data), headers=headers)
        return json5.loads(response.text)

    def get_ip_states(self):
        if not self.isLogin:
            print('You have not login yet!')
            return

        url = 'http://{}/cgi-bin/luci/;stok={}/admin/ipstats?form=list'.format(self.ip, self.stok)
        headers = self.default_headers
        headers['Referer'] = 'http://{}/webpages/index.html'.format(self.ip)
        data = {
            "method": "get",
            "params": {}
        }
        response = self.session.post(url, data=encodeData(data), headers=headers)
        return json5.loads(response.text)

    def logout(self):
        if not self.isLogin:
            print('You have not login yet!')
            return

        url = 'http://{}/cgi-bin/luci/;stok={}/admin/system?form=logout'.format(self.ip, self.stok)
        headers = self.default_headers
        headers['Referer'] = 'http://{}/webpages/index.html'.format(self.ip)
        data = {
            "method": "set",
        }
        response = self.session.post(url, data=encodeData(data), headers=headers)
        response = json5.loads(response.text)
        if response['error_code'] == '0':
            self.isLogin = False
            print('Logout Success!')
        else:
            print('Logout Fails!')
    