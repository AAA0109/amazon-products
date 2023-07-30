import datetime

import requests

from adsdroid.settings import (
    BOOKS_BEAM_EMAIL,
    BOOKS_BEAM_PASSWORD,
    BOOKS_BEAM_ACCESS_TOKEN_EXP_TIME,
)
from apps.ads_api.exceptions.auth.token import AuthFailed
from apps.ads_api.interfaces.auth.jwt_auth_interface import JWTAuthInterface


class BooksbeamAuthenticator(JWTAuthInterface):
    def get_access_token(self):
        return self._auth()

    def refresh_access_token(self):
        return self._auth()

    @classmethod
    def _auth(cls):
        url = "https://app.bookbeam.io/user-service/api/v1/auth/sign-in"
        data = {
            "email": BOOKS_BEAM_EMAIL,
            "password": BOOKS_BEAM_PASSWORD,
            "returnUrl": "/",
        }
        try:
            response = requests.post(url, json=data, verify=False)
            response.raise_for_status()
            token_data = response.json()
            access_token = token_data["accessToken"]
            refresh_token = token_data["refreshToken"]
        except requests.exceptions.RequestException as e:
            raise AuthFailed(f"Auth failed: {e}") from e

        if not access_token or not refresh_token:
            raise AuthFailed(f"Auth failed, response details - {response.json()}")

        token_exp_time = int(
            (
                datetime.datetime.now()
                + datetime.timedelta(seconds=BOOKS_BEAM_ACCESS_TOKEN_EXP_TIME)
            ).timestamp()
        )

        return access_token, refresh_token, token_exp_time
