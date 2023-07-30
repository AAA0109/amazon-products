import logging
from typing import Type

from pydantic import BaseModel

from apps.ads_api.adapters.amazon_ads.sponsored_products.base_sp_adapter import BaseSponsoredProductsAdapter
from apps.ads_api.entities.amazon_ads.sponsored_products.keywords import KeywordEntity

_logger = logging.getLogger(__name__)


class KeywordsAdapter(BaseSponsoredProductsAdapter):
    HEADERS: dict = {
                "Accept": "application/vnd.spKeyword.v3+json",
                "Content-Type": "application/vnd.spKeyword.v3+json",
            }
    URL: str = "/sp/keywords"
    ENTITY: Type[BaseModel] = KeywordEntity
    RESPONSE_DATA_KEY = "keywords"
    RESPONSE_DATA_ID = "keywordId"
