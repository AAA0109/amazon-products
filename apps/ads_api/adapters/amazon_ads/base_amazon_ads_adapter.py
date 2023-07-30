import logging
import time
from typing import Optional

import requests
from requests import Session, Response
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from adsdroid.settings import ADS_API_CLIENT_ID
from apps.ads_api.authenticators.amazon_ads_authentificator import AmazonAuthenticator
from apps.ads_api.constants import BaseURL, ServerLocation
from apps.ads_api.entities.internal.token import Token
from apps.ads_api.exceptions.ads_api.base import BaseAmazonAdsException
from apps.ads_api.exceptions.auth.token import AuthFailed
from apps.ads_api.interfaces.auth.authenticatable_interface import (
    AuthenticatableInterface,
)
from apps.ads_api.interfaces.auth.token_id_interface import TokenIdInterface
from apps.utils.jwt_auth import JWTAuth
from apps.utils.retry_wrapper import retry_auth_failed

_logger = logging.getLogger(__name__)


class BaseAmazonAdsAdapter(AuthenticatableInterface, TokenIdInterface):
    def __init__(self, server: ServerLocation):
        self.server = server

    @property
    def authenticator(self) -> AmazonAuthenticator:
        return AmazonAuthenticator(self.server)

    @property
    def token_id(self):
        return self._map_token_id_with_region()

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
        url = self._resolve_url(url)
        headers = {
            "Amazon-Advertising-API-ClientId": ADS_API_CLIENT_ID,
            "Authorization": "Bearer " + access_token.value,
        }

        if extra_headers:
            headers.update(extra_headers)

        try:
            if method == "GET":
                session = self._create_http_session()
                response = session.get(url, headers=headers, params=params)
            elif method == "POST":
                response = requests.post(url, json=body, headers=headers)
            elif method == "PUT":
                response = requests.put(url, json=body, headers=headers)
            else:
                raise NotImplementedError("Request method not implemented")
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            if e.response.status_code == 401:
                raise AuthFailed(f"Auth failed: {e.response.json()}")
            elif e.response.status_code == 429:
                secs = 10
                time.sleep(secs)
                _logger.error("Too many requests so sleeping for %s seconds", secs)
            elif e.response.status_code == 400:
                logging.error(f"Error {e.response.json()}, body {body}, url {url}, method {method}")
                raise BaseAmazonAdsException(f"Error {e.response.json()['code']}: {e.response.json()['message']}")
            else:
                _logger.error(
                    "Error code: %s. Details: %s, payload: %s, url: %s, method: %s, parameters: %s",
                    e.response.status_code,
                    e.response.json(),
                    body,
                    url,
                    method,
                    params,
                )
        else:
            return response

    def _resolve_url(self, url) -> str:
        if "http" in url:
            base_url = url
        else:
            base_url = BaseURL[self.server] + url
        return base_url

    def _map_token_id_with_region(self):
        token_id = {
            ServerLocation.NORTH_AMERICA: f"amazon_ads_{ServerLocation.NORTH_AMERICA}",
            ServerLocation.EUROPE: f"amazon_ads_{ServerLocation.EUROPE}",
            ServerLocation.FAR_EAST: f"amazon_ads_{ServerLocation.FAR_EAST}",
        }
        return token_id[self.server]

    @staticmethod
    def _create_http_session() -> Session:
        """Creates a new retry session for request"""
        session = Session()
        retry = Retry(connect=5, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
