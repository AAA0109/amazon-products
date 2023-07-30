import datetime
from typing import Optional

import requests
from IPython.utils.tz import utcnow
from requests import Response

from apps.ads_api.constants import ServerLocation
from apps.ads_api.entities.internal.token import Token
from apps.ads_api.interfaces.auth.authenticatable_interface import (
    AuthenticatableInterface,
)
from apps.ads_api.interfaces.auth.token_id_interface import TokenIdInterface
from apps.sp_api.auth import SpApiAuthenticator
from apps.sp_api.constants import BaseSpApiUrls
from apps.utils.jwt_auth import JWTAuth
from apps.utils.retry_wrapper import retry_auth_failed


class BaseSpApiAdapter(AuthenticatableInterface, TokenIdInterface):
    def __init__(self, server_location: ServerLocation):
        self.server_location = server_location

    @property
    def authenticator(self):
        return SpApiAuthenticator(self.server_location)
    @property
    def token_id(self):
        return self._map_token_id_with_marketplace()

    @retry_auth_failed(max_retries=5)
    @JWTAuth.auth_required()
    def send_request(
        self,
        url: str,
        method: str = "GET",
        extra_headers=None,
        body: Optional[dict] = None,
        params: Optional[dict] = None,
        access_token: Token = None,
    ) -> Optional[Response]:
        if not body:
            body = {}

        headers = {
            "x-amz-access-token": access_token.value,
            "x-amz-date": utcnow().strftime("%Y%m%dT%H%M%SZ"),
            "host": BaseSpApiUrls[self.server_location],
            "Authorization": "AWS4-HMAC-SHA256",

        }
        if extra_headers:
            headers.update(extra_headers)

        response = requests.request(
            url=url, method=method, params=params, json=body, headers=headers, verify=False
        )
        return response

    def _map_token_id_with_marketplace(self) -> str:
        token_id = {
            ServerLocation.NORTH_AMERICA: f"sp-api-token-{ServerLocation.NORTH_AMERICA}",
            ServerLocation.EUROPE: f"sp-api-token-{ServerLocation.EUROPE}",
            ServerLocation.FAR_EAST: f"sp-api-token-{ServerLocation.FAR_EAST}",
        }
        return token_id[self.server_location]
