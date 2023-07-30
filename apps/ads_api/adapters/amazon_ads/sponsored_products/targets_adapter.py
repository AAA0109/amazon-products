from typing import Type

from apps.ads_api.adapters.amazon_ads.sponsored_products.base_sp_adapter import BaseSponsoredProductsAdapter
from apps.ads_api.entities.amazon_ads.sponsored_products.targets import TargetEntity
from apps.utils.models import BaseModel


class TargetsAdapter(BaseSponsoredProductsAdapter):
    HEADERS: dict = {
        "Accept": "application/vnd.spTargetingClause.v3+json",
        "Content-Type": "application/vnd.spTargetingClause.v3+json",
    }
    URL: str = "/sp/targets"
    ENTITY: Type[BaseModel] = TargetEntity
    RESPONSE_DATA_KEY = "targetingClauses"
    RESPONSE_DATA_ID = "targetId"
