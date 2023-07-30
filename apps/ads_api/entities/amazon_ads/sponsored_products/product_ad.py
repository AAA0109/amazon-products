from typing import Optional

from pydantic import BaseModel, Field

from apps.ads_api.constants import SpState
from apps.ads_api.entities.amazon_ads.sponsored_products.extended_data import ExtendedData


class ProductAdEntity(BaseModel):
    external_id: Optional[str] = Field(alias="adId")
    ad_group_id: str = Field(alias="adGroupId")
    campaign_id: str = Field(alias="campaignId")
    state: SpState = Field(default=SpState.ENABLED)
    asin: Optional[str]
    sku: Optional[str]
    text: Optional[str] = Field(alias="customText")
    extended_data: Optional[ExtendedData] = Field(alias="extendedData")

    class Config:
        use_enum_values = True
        allow_population_by_field_name = True
