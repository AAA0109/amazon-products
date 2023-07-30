from typing import Optional

from pydantic import Field, BaseModel

from apps.ads_api.constants import SpState
from apps.ads_api.entities.amazon_ads.sponsored_products.extended_data import ExtendedData
from apps.ads_api.entities.amazon_ads.sponsored_products.negative_target import Expression


class CampaignNegativeTargetsEntity(BaseModel):
    expression: Optional[list[Expression]] = Field(max_items=1000)
    external_id: Optional[str] = Field(alias="targetId")
    resolved_expression: Optional[list[Expression]] = Field(alias="resolvedExpression", max_items=1000)
    campaign_id: Optional[str] = Field(alias="campaignId")
    state: Optional[SpState]
    extended_data: Optional[ExtendedData] = Field(alias="extendedData")

    class Config:
        use_enum_values = True
        allow_population_by_field_name = True
