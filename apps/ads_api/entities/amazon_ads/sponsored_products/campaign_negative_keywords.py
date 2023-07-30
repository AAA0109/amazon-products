from typing import Optional

from pydantic import Field, BaseModel

from apps.ads_api.constants import NegativeMatchType, SpState
from apps.ads_api.entities.amazon_ads.sponsored_products.extended_data import ExtendedData


class CampaignNegativeKeywordsEntity(BaseModel):
    external_id: Optional[str] = Field(alias="keywordId")
    campaign_id: Optional[str] = Field(alias="campaignId")
    match_type: Optional[NegativeMatchType] = Field(alias="matchType")
    state: Optional[SpState]
    keyword_text: str = Field(alias="keywordText")
    extended_data: Optional[ExtendedData] = Field(alias="extendedData")

    class Config:
        allow_population_by_field_name = True
        use_enum_values = True
