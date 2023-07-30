import requests
from requests import Response

from apps.ads_api.authenticators.booksbeam_authenticator import BooksbeamAuthenticator
from apps.ads_api.entities.internal.token import Token

from apps.ads_api.interfaces.auth.authenticatable_interface import (
    AuthenticatableInterface,
)
from apps.ads_api.interfaces.auth.token_id_interface import TokenIdInterface
from apps.utils.jwt_auth import JWTAuth


class BaseBooksBeamAdapter(AuthenticatableInterface, TokenIdInterface):
    @property
    def token_id(self):
        return "booksbeam"

    @property
    def authenticator(self) -> BooksbeamAuthenticator:
        return BooksbeamAuthenticator()

    @JWTAuth.auth_required()
    def send_request(
        self,
        url,
        headers=None,
        data=None,
        method: str = "GET",
        access_token: Token = None,
    ) -> Response:
        if not data:
            data = {}

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/110.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-GB,en;q=0.5",
            "Authorization": access_token.value,
            "Content-Type": "application/json",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "referrer": "https://app.bookbeam.io/",
        }

        response = requests.request(
            url=url, method=method, json=data, headers=headers, verify=False
        )
        return response
