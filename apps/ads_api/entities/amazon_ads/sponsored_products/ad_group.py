from typing import Optional

from pydantic import BaseModel, Field

from apps.ads_api.constants import DEFAULT_BID, SpState
from apps.ads_api.entities.amazon_ads.sponsored_products.extended_data import ExtendedData


class AdGroupEntity(BaseModel):
    name: str
    campaign_id: str = Field(alias="campaignId")
    state: SpState = Field(default=SpState.ENABLED)
    bid: float = Field(alias="defaultBid", default=DEFAULT_BID)
    external_id: Optional[str] = Field(alias="adGroupId")
    internal_id: Optional[str]
    extended_data: Optional[ExtendedData] = Field(alias="extendedData")

    class Config:
        use_enum_values = True
        allow_population_by_field_name = True
