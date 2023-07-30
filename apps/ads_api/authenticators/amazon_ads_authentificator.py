import datetime

import requests

from adsdroid.settings import ADS_API_CLIENT_ID, ADS_API_CLIENT_SECRET
from apps.ads_api.constants import ServerLocation, RefreshToken, AuthURL
from apps.ads_api.exceptions.auth.token import AuthFailed
from apps.ads_api.interfaces.auth.jwt_auth_interface import JWTAuthInterface


class AmazonAuthenticator(JWTAuthInterface):
    def __init__(self, server: ServerLocation):
        self.server = server

    def get_access_token(self):
        return self._auth()

    def refresh_access_token(self):
        return self._auth()

    def _auth(self):
        refresh_token = RefreshToken[self.server]
        url = AuthURL[self.server]
        payload = f"charset=UTF-8&grant_type=refresh_token&refresh_token={refresh_token}&client_id={ADS_API_CLIENT_ID}&client_secret={ADS_API_CLIENT_SECRET}"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        try:
            response = requests.request("POST", url, headers=headers, data=payload)
            response.raise_for_status()
            token_data = response.json()
            access_token = token_data["access_token"]
            refresh_token = token_data["refresh_token"]
            expires_in = token_data["expires_in"]
        except requests.exceptions.RequestException as e:
            raise AuthFailed(f"Auth failed: {e}") from e

        if not access_token or not refresh_token or not expires_in:
            raise AuthFailed(f"Auth failed, response details - {response.json()}")

        token_exp_time = int(
            (
                datetime.datetime.now() + datetime.timedelta(seconds=expires_in)
            ).timestamp()
        )
        return access_token, refresh_token, token_exp_time
