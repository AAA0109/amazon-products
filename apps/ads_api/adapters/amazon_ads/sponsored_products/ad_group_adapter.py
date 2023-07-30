import logging
from typing import Type

from pydantic import BaseModel

from apps.ads_api.adapters.amazon_ads.sponsored_products.base_sp_adapter import BaseSponsoredProductsAdapter
from apps.ads_api.entities.amazon_ads.sponsored_products.ad_group import AdGroupEntity

_logger = logging.getLogger(__name__)


class AdGroupAdapter(BaseSponsoredProductsAdapter):
    HEADERS: dict = {
        "Accept": "application/vnd.spAdGroup.v3+json",
        "Content-Type": "application/vnd.spAdGroup.v3+json",
    }
    URL: str = "/sp/adGroups"
    ENTITY: Type[BaseModel] = AdGroupEntity
    RESPONSE_DATA_KEY: str = "adGroups"
    RESPONSE_DATA_ID: str = "adGroupId"
