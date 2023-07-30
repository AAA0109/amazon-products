import datetime

import requests

from apps.ads_api.constants import ServerLocation
from apps.ads_api.exceptions.auth.token import AuthFailed
from apps.ads_api.interfaces.auth.jwt_auth_interface import JWTAuthInterface
from apps.sp_api.constants import RefreshToken
from apps.sp_api.settings import SP_API_CLIENT_ID, SP_API_CLIENT_SECRET


class SpApiAuthenticator(JWTAuthInterface):
    def refresh_access_token(self):
        return self._auth()

    def __init__(self, server_location: ServerLocation) -> None:
        self.server_location: ServerLocation = server_location

    def get_access_token(self):
        return self._auth()

    def _auth(self):
        url = "https://api.amazon.com/auth/o2/token"
        data: dict[str, str] = {
            "grant_type": "refresh_token",
            "refresh_token": self._map_refresh_token_with_server_location(),
            "client_id": SP_API_CLIENT_ID,
            "client_secret": SP_API_CLIENT_SECRET,
        }
        try:
            response = requests.post(url, json=data, verify=False)
            response.raise_for_status()
            token_data = response.json()
            access_token = token_data["access_token"]
            refresh_token = token_data["refresh_token"]
        except requests.exceptions.RequestException as e:
            raise AuthFailed(f"Auth failed: {e}") from e

        if not access_token or not refresh_token:
            raise AuthFailed(f"Auth failed, response details - {response.json()}")

        token_exp_time = int((datetime.datetime.now() + datetime.timedelta(seconds=60 * 60)).timestamp())

        return access_token, refresh_token, token_exp_time

    def _map_refresh_token_with_server_location(self) -> str:
        return RefreshToken[self.server_location]