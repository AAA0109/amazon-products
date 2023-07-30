from typing import Type

from pydantic import BaseModel

from apps.ads_api.adapters.amazon_ads.sponsored_products.base_sp_adapter import BaseSponsoredProductsAdapter
from apps.ads_api.entities.amazon_ads.sponsored_products.campaign_negative_keywords import CampaignNegativeKeywordsEntity


class CampaignNegativeKeywordsAdapter(BaseSponsoredProductsAdapter):
    HEADERS: dict = {
        "Accept": "application/vnd.spCampaignNegativeKeyword.v3+json",
        "Content-Type": "application/vnd.spCampaignNegativeKeyword.v3+json",
    }
    URL: str = "/sp/campaignNegativeKeywords"
    ENTITY: Type[BaseModel] = CampaignNegativeKeywordsEntity
    RESPONSE_DATA_KEY = "campaignNegativeKeywords"
    RESPONSE_DATA_ID = "keywordId"
