import logging
from typing import Union, Iterable

import requests
from requests import Response

from apps.ads_api.adapters.amazon_ads.base_amazon_ads_adapter import (
    BaseAmazonAdsAdapter,
)
from apps.ads_api.constants import ServerLocation
from apps.ads_api.entities.amazon_ads.profiles import ProfilesListEntity, ProfileEntity
from apps.ads_api.interfaces.adapters.profiles_adapter_interface import (
    ProfilesAdapterInterface,
)

from pydantic import ValidationError


_logger = logging.getLogger(__name__)


class AccountAdapter(BaseAmazonAdsAdapter, ProfilesAdapterInterface):
    def __init__(self, server: Union[ServerLocation, str]):
        super().__init__(server)

    def get_all_profiles(self) -> ProfilesListEntity:
        profiles = self._retrieve_profiles()
        return profiles

    def get_all_profiles_iterator(self) -> Iterable[ProfileEntity]:
        profiles = self._retrieve_profiles()
        for profile in profiles:
            yield profile

    def _retrieve_profiles(self) -> ProfilesListEntity:
        response = self.send_request("/v2/profiles")
        profiles = self._parse_profiles_from_response(response)
        return profiles

    def _parse_profiles_from_response(self, response: Response) -> ProfilesListEntity:
        profiles = []
        try:
            profiles = ProfilesListEntity.parse_obj(response.json())
        except ValidationError as e:
            _logger.error(e.json())
        except requests.exceptions.JSONDecodeError as e:
            _logger.error("Failed to get profiles on server: %s, %s", self.server, e)
        return profiles
