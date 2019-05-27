import warnings
import robinhood_api.urls as urls
from six.moves.urllib.request import getproxies
from six.moves import input
import requests
import time
import random
import hmac, base64, struct, hashlib
from robinhood_api import exceptions as RH_exception

class Robinhood:
    """Wrapper class for fetching/parsing Robinhood endpoints """

    session = None
    username = None
    password = None
    headers = None
    auth_token = None
    refresh_token = None


    client_id = "c82SH0WZOsabOXGP2sxqcj34FxkvfnWRZBKlBjFS"

    ###########################################################################
    #                       Logging in and initializing
    ###########################################################################

    def __init__(self):
        self.session = requests.session()
        self.session.proxies = getproxies()
        self.headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en;q=1, fr;q=0.9, de;q=0.8, ja;q=0.7, nl;q=0.6, it;q=0.5",
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
            "X-Robinhood-API-Version": "1.0.0",
            "Connection": "keep-alive",
            "User-Agent": "Robinhood/823 (iPhone; iOS 7.1.2; Scale/2.00)"
        }
        self.session.headers = self.headers
        self.device_token = ""
        self.challenge_id = ""

    def login_required(function):  # pylint: disable=E0213
        """ Decorator function that prompts user for login if they are not logged in already. Can be applied to any function using the @ notation. """

        def wrapper(self, *args, **kwargs):
            if 'Authorization' not in self.headers:
                self.auth_method()
            return function(self, *args, **kwargs)  # pylint: disable=E1102

        return wrapper

    def GenerateDeviceToken(self):
        rands = []
        for i in range(0, 16):
            r = random.random()
            rand = 4294967296.0 * r
            rands.append((int(rand) >> ((3 & i) << 3)) & 255)

        hexa = []
        for i in range(0, 256):
            hexa.append(str(hex(i + 256)).lstrip("0x").rstrip("L")[1:])

        id = ""
        for i in range(0, 16):
            id += hexa[rands[i]]

            if (i == 3) or (i == 5) or (i == 7) or (i == 9):
                id += "-"

        self.device_token = id

    def get_mfa_token(self, secret):
        intervals_no = int(time.time()) // 30
        key = base64.b32decode(secret, True)
        msg = struct.pack(">Q", intervals_no)
        h = hmac.new(key, msg, hashlib.sha1).digest()
        o = h[19] & 15
        h = '{0:06d}'.format((struct.unpack(">I", h[o:o + 4])[0] & 0x7fffffff) % 1000000)
        return h

    def login(self,
              username,
              password,
              qr_code=None):
        """Save and test login info for Robinhood accounts
        Args:
            username (str): username
            password (str): password
            qr_code (str): QR code that will be used to generate mfa_code (optional but recommended)
            To get QR code, set up 2FA in Security, get Authentication App, and click "Can't Scan It?"
        Returns:
            (bool): received valid auth token
        """
        self.username = username
        self.password = password

        if self.device_token == "":
            self.GenerateDeviceToken()

        if qr_code:
            self.qr_code = qr_code
            payload = {
                'password': self.password,
                'username': self.username,
                'grant_type': 'password',
                'client_id': "c82SH0WZOsabOXGP2sxqcj34FxkvfnWRZBKlBjFS",
                'scope': 'internal',
                'device_token': self.device_token,
                'mfa_code': self.get_mfa_token(self.qr_code)
            }

            try:
                res = self.session.post(urls.login_url(), data=payload, timeout=15)
                data = res.json()

                if 'access_token' in data.keys() and 'refresh_token' in data.keys():
                    self.auth_token = data['access_token']
                    self.refresh_token = data['refresh_token']
                    self.headers['Authorization'] = 'Bearer ' + self.auth_token
                    return True

            except requests.exceptions.HTTPError:
                raise RH_exception.LoginFailed()

        else:
            payload = {
                'password': self.password,
                'username': self.username,
                'grant_type': 'password',
                'client_id': "c82SH0WZOsabOXGP2sxqcj34FxkvfnWRZBKlBjFS",
                'expires_in': '86400',
                'scope': 'internal',
                'device_token': self.device_token,
                'challenge_type': 'sms'
            }

            try:
                res = self.session.post(urls.login_url(), data=payload, timeout=15)
                response_data = res.json()
                if self.challenge_id == "" and "challenge" in response_data.keys():
                    self.challenge_id = response_data["challenge"]["id"]
                self.headers[
                    "X-ROBINHOOD-CHALLENGE-RESPONSE-ID"] = self.challenge_id  # has to add this to stay logged in
                sms_challenge_endpoint = "https://api.robinhood.com/challenge/{}/respond/".format(self.challenge_id)
                print("No 2FA Given")
                print("SMS Code:")
                self.sms_code = input()
                challenge_res = {"response": self.sms_code}
                res2 = self.session.post(sms_challenge_endpoint, data=challenge_res, timeout=15)
                res2.raise_for_status()
                # gets access token for final response to stay logged in
                res3 = self.session.post(urls.login_url(), data=payload, timeout=15)
                res3.raise_for_status()
                data = res3.json()

                if 'access_token' in data.keys() and 'refresh_token' in data.keys():
                    self.auth_token = data['access_token']
                    self.refresh_token = data['refresh_token']
                    self.headers['Authorization'] = 'Bearer ' + self.auth_token
                    return True

            except requests.exceptions.HTTPError:
                raise RH_exception.LoginFailed()

        return False

    def auth_method(self):

        if self.qr_code:
            payload = {
                'password': self.password,
                'username': self.username,
                'grant_type': 'password',
                'client_id': "c82SH0WZOsabOXGP2sxqcj34FxkvfnWRZBKlBjFS",
                'scope': 'internal',
                'device_token': self.device_token,
                'mfa_code': self.get_mfa_token(self.qr_code)
            }

            try:
                res = self.session.post(urls.login_url(), data=payload, timeout=15)
                data = res.json()

                if 'access_token' in data.keys() and 'refresh_token' in data.keys():
                    self.auth_token = data['access_token']
                    self.refresh_token = data['refresh_token']
                    self.headers['Authorization'] = 'Bearer ' + self.auth_token
                    return True

            except requests.exceptions.HTTPError:
                raise RH_exception.LoginFailed()

        else:
            payload = {
                'password': self.password,
                'username': self.username,
                'grant_type': 'password',
                'client_id': "c82SH0WZOsabOXGP2sxqcj34FxkvfnWRZBKlBjFS",
                'expires_in': '86400',
                'scope': 'internal',
                'device_token': self.device_token,
            }

            try:
                res = self.session.post(urls.login_url(), data=payload, timeout=15)
                res.raise_for_status()
                data = res.json()

                if 'access_token' in data.keys() and 'refresh_token' in data.keys():
                    self.auth_token = data['access_token']
                    self.refresh_token = data['refresh_token']
                    self.headers['Authorization'] = 'Bearer ' + self.auth_token
                    return True

            except requests.exceptions.HTTPError:
                raise RH_exception.LoginFailed()

        return False

    def logout(self):
        """Logout from Robinhood
        Returns:
            (:obj:`requests.request`) result from logout endpoint
        """

        try:
            payload = {
                'client_id': self.client_id,
                'token': self.refresh_token
            }
            req = self.session.post(urls.logout_url(), data=payload, timeout=15)
            req.raise_for_status()
        except requests.exceptions.HTTPError as err_msg:
            warnings.warn('Failed to log out ' + repr(err_msg))

        self.headers['Authorization'] = None
        self.auth_token = None

        return req

    def investment_profile(self):
        """Fetch investment_profile """

        res = self.session.get(urls.investment_profile(), timeout=15)
        res.raise_for_status()  # will throw without auth
        data = res.json()

        return data


