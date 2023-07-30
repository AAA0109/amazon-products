from typing import Type

from pydantic import BaseModel

from apps.ads_api.adapters.amazon_ads.sponsored_products.base_sp_adapter import BaseSponsoredProductsAdapter
from apps.ads_api.entities.amazon_ads.sponsored_products.negative_keyword import NegativeKeywordEntity


class NegativeKeywordsAdapter(BaseSponsoredProductsAdapter):
    HEADERS: dict = {
        "Accept": "application/vnd.spNegativeKeyword.v3+json",
        "Content-Type": "application/vnd.spNegativeKeyword.v3+json",
    }
    URL: str = "/sp/negativeKeywords"
    ENTITY: Type[BaseModel] = NegativeKeywordEntity
    RESPONSE_DATA_KEY = "negativeKeywords"
    RESPONSE_DATA_ID = "negativeKeywordId"
