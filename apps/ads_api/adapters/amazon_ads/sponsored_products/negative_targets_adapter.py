from typing import Type

from apps.ads_api.adapters.amazon_ads.sponsored_products.base_sp_adapter import BaseSponsoredProductsAdapter
from apps.ads_api.entities.amazon_ads.sponsored_products.negative_target import NegativeTargetEntity
from apps.utils.models import BaseModel


class NegativeTargetsAdapter(BaseSponsoredProductsAdapter):
    HEADERS: dict = {
        "Accept": "application/vnd.spNegativeTargetingClause.v3+json",
        "Content-Type": "application/vnd.spNegativeTargetingClause.v3+json",
    }
    URL: str = "/sp/negativeTargets"
    ENTITY: Type[BaseModel] = NegativeTargetEntity
    RESPONSE_DATA_KEY = "negativeTargetingClauses"
    RESPONSE_DATA_ID = "targetId"
