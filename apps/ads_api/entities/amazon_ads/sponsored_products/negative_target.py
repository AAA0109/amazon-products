from typing import Optional

from pydantic import BaseModel, Field

from apps.ads_api.constants import SpState, NegativeTargetingExpressionPredicateType
from apps.ads_api.entities.amazon_ads.sponsored_products.extended_data import ExtendedData


class Expression(BaseModel):
    type: Optional[NegativeTargetingExpressionPredicateType]
    value: Optional[str]

    class Config:
        use_enum_values = True
        allow_population_by_field_name = True


class NegativeTargetEntity(BaseModel):
    external_id: Optional[str] = Field(alias="targetId")
    expression: Optional[list[Expression]] = Field(max_items=1000)
    resolved_expression: Optional[list[Expression]] = Field(alias="resolvedExpression", max_items=1000)
    campaign_id: Optional[str] = Field(alias="campaignId")
    state: Optional[SpState]
    ad_group_id: str = Field(alias="adGroupId")
    extended_data: Optional[ExtendedData] = Field(alias="extendedData")

    class Config:
        use_enum_values = True
        allow_population_by_field_name = True
