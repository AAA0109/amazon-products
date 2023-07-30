from typing import Type

from pydantic import BaseModel

from apps.ads_api.adapters.amazon_ads.sponsored_products.base_sp_adapter import BaseSponsoredProductsAdapter
from apps.ads_api.entities.amazon_ads.sponsored_products.campaign_negative_targets import CampaignNegativeTargetsEntity


class CampaignNegativeTargetsAdapter(BaseSponsoredProductsAdapter):
    HEADERS: dict = {
        "Accept": "application/vnd.spCampaignNegativeTargetingClause.v3+json",
        "Content-Type": "application/vnd.spCampaignNegativeTargetingClause.v3+json",
    }
    URL: str = "/sp/campaignNegativeTargets"
    ENTITY: Type[BaseModel] = CampaignNegativeTargetsEntity
    RESPONSE_DATA_KEY = "campaignNegativeTargetingClauses"
    RESPONSE_DATA_ID = "targetId"
