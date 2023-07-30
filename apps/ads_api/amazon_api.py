import gzip
import io
import json
import logging
import os
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, NamedTuple, Optional

import requests
from django.core.serializers.json import DjangoJSONEncoder

# from adsdroid.celery import app
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry  # type: ignore

from apps.ads_api.constants import (
    AuthURL,
    BaseURL,
    RefreshToken,
    ServerLocation,
    SpEndpoint,
)
from apps.ads_api.exceptions.ads_api.campaigns import CampaignDoesNotCreated
from apps.utils.chunks import chunker

_logger = logging.getLogger(__name__)


def get_new_retry_session():
    """Creates a new retry session for request"""
    session = requests.Session()
    retry = Retry(connect=5, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def refresh_token(get_access_token_fn):
    def refresh_token_wrapper(decorated):
        @wraps(decorated)
        def wrapper(cls, *args, **kwargs):
            get_access_token_fn.__func__(cls, *args, **kwargs)
            return decorated(cls, *args, **kwargs)

        return wrapper

    return refresh_token_wrapper


class Token(NamedTuple):
    value: str
    expires_in: datetime


def extract_gzip(resp):
    with io.BytesIO() as buf:
        buf.write(resp.content)
        buf.seek(0)
        with gzip.open(buf, "rt") as compressed_report:
            try:
                report_content = compressed_report.read()
                report_content_array = json.loads(report_content)
            except gzip.BadGzipFile:
                _logger.info("Regualr text passed to extract_gzip")
                report_content_array = json.loads(resp.text)
    return report_content_array


class AdsAPI:

    ACCESS_TOKEN_PER_REGION: Dict[str, Optional[Token]] = {
        ServerLocation.NORTH_AMERICA: None,
        ServerLocation.EUROPE: None,
        ServerLocation.FAR_EAST: None,
    }

    @staticmethod
    def fetch_new_token(server):
        try:
            refresh_token = RefreshToken[server]
            url = AuthURL[server]
            client_id = os.environ.get("ADS_API_CLIENT_ID")
            client_secret = os.environ.get("ADS_API_CLIENT_SECRET")
            payload = f"charset=UTF-8&grant_type=refresh_token&refresh_token={refresh_token}&client_id={client_id}&client_secret={client_secret}"
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            # request an access token
            request = requests.request("POST", url, headers=headers, data=payload)
            # optional: raise exception for status code
            request.raise_for_status()
        except Exception as e:
            _logger.error("Failed to get new access token: %s", e)
            return None
        else:
            return request.json()["access_token"]

    @classmethod
    def get_access_token(cls, server, *args, **kwargs):
        token = cls.ACCESS_TOKEN_PER_REGION[server]
        if not token or datetime.now() > token.expires_in:
            new_token_value = cls.fetch_new_token(server)
            if new_token_value == None:
                _logger.error("Failed to get new access token")
                return
            new_token = Token(
                value=new_token_value,
                expires_in=datetime.now() + timedelta(seconds=3500),
            )
            cls.ACCESS_TOKEN_PER_REGION[server] = new_token

    @classmethod
    @refresh_token(get_access_token)
    def _do_request(
        cls,
        url: str,
        server: ServerLocation,
        method: str = "GET",
        extra_headers=None,
        payload: Optional[str] = None,
        params: Optional[Dict[str, str]] = None,
    ):
        if "http" in url:
            base_url = url
        else:
            base_url = BaseURL[server] + url
        api_client_id = os.environ.get("ADS_API_CLIENT_ID")

        if hasattr(cls.ACCESS_TOKEN_PER_REGION[server], "value"):
            access_token = cls.ACCESS_TOKEN_PER_REGION[server].value  # type: ignore
        else:
            _logger.error("Token is missing on server: %s", server)
            return None

        headers = {
            "Amazon-Advertising-API-ClientId": api_client_id,
            "Authorization": "Bearer " + access_token,
        }

        if extra_headers:
            headers.update(extra_headers)

        try:
            if method == "GET":
                session = get_new_retry_session()
                resp = session.get(base_url, headers=headers, params=params)
                # resp = requests.get(base_url, headers=headers, params=params)
            elif method in ["POST", "PUT"]:
                resp = requests.post(base_url, data=payload, headers=headers)
            else:
                raise NotImplementedError("Request method not implemented")
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            _logger.error("Failed to connect to Amazon API error: %s", e.response.text)
            try:
                error_body = e.response.json()
                code_cody = error_body.get("code")
                try:
                    code = int(code_cody)
                except:
                    code = code_cody
                details = error_body.get("details")
                secs = 10
                if code == 429 and details == "Too Many Requests":
                    _logger.error("Too many requests so sleeping for %s seconds", secs)
                    time.sleep(secs)
                else:
                    _logger.error(
                        "Error code: %s. Detail: %s. Sleeping for %s seconds. Payload: %s, url: %s",
                        code,
                        details,
                        secs,
                        payload,
                        url,
                    )
                    time.sleep(secs)
                return
            except json.JSONDecodeError:
                _logger.info("We got empty response: %s", e.response)
            return
        else:
            if resp.encoding == "utf-8" or resp.apparent_encoding == "ascii":
                resp_obj = resp.json()
            else:
                resp_obj = extract_gzip(resp)
            return resp_obj

    ########################################################################################
    # Campaigns & Keyword & Targets (ASINs / Categories) Functions
    ########################################################################################

    @classmethod
    def get_sp_data(
        cls, server, profile_id, endpoint: SpEndpoint, params: Optional[Dict] = None
    ):
        # TODO: replace extended
        # possible endpoints:
        # - /v2/sp/keywords
        # - /v2/sp/negativeKeywords
        # - /v2/sp/campaignNegativeKeywords
        # - /v2/sp/targets
        # - /v2/sp/negativeTargets
        """Gets all keywords, targets, campaigns available on the specified server"""
        url = f"{endpoint}/extended"
        headers = {"Amazon-Advertising-API-Scope": str(profile_id)}
        # ensure that the dictionary conforms to the requests library requirement of Dict[str,str] for params
        if params:
            params_str = {}
            for key in params:
                params_str[str(key)] = params[key]
            response = cls._do_request(
                url=url,
                server=server,
                method="GET",
                extra_headers=headers,
                params=params_str,
            )
        else:
            response = cls._do_request(
                url=url, server=server, method="GET", extra_headers=headers
            )
        if response == None:
            _logger.error(
                "Failed to get data for profile: %s on server: %s", profile_id, server
            )
            return
        return response

    @classmethod
    def update_sp_data(
        cls, server, profile_id, data_dicts_array: list, endpoint: SpEndpoint
    ):
        """
        Updates up to 1,000 keywords or targets etc on the specified server
        data_dicts_array would look like: [{},{},{}]
        the content of the {} varies based on the endpoint: keywords, targets, campaigns etc
        """
        timeout = 10
        headers = {
            "Amazon-Advertising-API-Scope": str(profile_id),
            "Content-Type": "application/json",
        }
        max_items = 100 if endpoint == SpEndpoint.CAMPAIGNS else 1000
        for group in chunker(data_dicts_array, max_items):
            keywords = json.dumps(group, cls=DjangoJSONEncoder)
            retry = 0
            while retry < timeout:
                try:
                    cls._do_request(
                        url=endpoint,
                        server=server,
                        method="PUT",
                        extra_headers=headers,
                        payload=keywords,
                    )
                except requests.exceptions.ConnectionError:
                    time.sleep(60)  # 1 minute
                    retry += 1
                else:
                    break

            if retry >= timeout:
                _logger.error(
                    "To match retries %s(timeout - %s) while getting ConnectionError",
                    retry,
                    timeout,
                )
                raise CampaignDoesNotCreated()

    @classmethod
    def add_sp_data(
        cls, server, profile_id, data_dicts_array: list, endpoint: SpEndpoint
    ):
        """Adds up to 1,000 keywords or targets etc on the specified server"""
        headers = {
            "Amazon-Advertising-API-Scope": str(profile_id),
            "Content-Type": "application/json",
        }
        max_items = (
            100 if endpoint in [SpEndpoint.CAMPAIGNS, SpEndpoint.AD_GROUPS] else 1000
        )
        timeout = 10
        response = None
        if isinstance(data_dicts_array, list):
            for group in chunker(data_dicts_array, max_items):
                data = json.dumps(group, cls=DjangoJSONEncoder)
                retry = 0
                while retry < timeout:
                    try:
                        response = cls._do_request(
                            url=endpoint,
                            server=server,
                            method="POST",
                            extra_headers=headers,
                            payload=data,
                        )
                    except requests.exceptions.ConnectionError:
                        time.sleep(60)  # 1 minute
                        retry += 1
                    else:
                        break

                if retry >= timeout:
                    _logger.error(
                        "To match retries %s while getting ConnectionError", retry
                    )
                    raise CampaignDoesNotCreated()

        # this is currently used exclusively for the bid recommendation function
        else:
            data = json.dumps(data_dicts_array, cls=DjangoJSONEncoder)
            retry = 0
            while retry < timeout:
                try:
                    response = cls._do_request(
                        url=endpoint,
                        server=server,
                        method="POST",
                        extra_headers=headers,
                        payload=data,
                    )
                except requests.exceptions.ConnectionError:
                    time.sleep(60)  # 1 minute
                    retry += 1
                else:
                    break

            if retry >= timeout:
                _logger.error(
                    "To match retries %s while getting ConnectionError", retry
                )
                raise CampaignDoesNotCreated()

        return response  # type: ignore
