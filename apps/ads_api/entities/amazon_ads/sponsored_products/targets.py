from typing import Optional, Union

from pydantic import BaseModel, Field

from apps.ads_api.constants import (
    SpExpressionType,
    SpState,
    TargetingExpressionPredicateType,
)
from apps.ads_api.entities.amazon_ads.sponsored_products.extended_data import (
    ExtendedData,
)


class Expression(BaseModel):
    type: Optional[Union[TargetingExpressionPredicateType, str]]
    value: Optional[str]

    class Config:
        use_enum_values = True
        allow_population_by_field_name = True


class TargetEntity(BaseModel):
    expression: Optional[list[Expression]] = Field(max_items=1000)
    resolved_expression: Optional[list[Expression]] = Field(alias="resolvedExpression", max_items=1000)
    external_id: Optional[str] = Field(alias="targetId")
    expression_type: Optional[SpExpressionType] = Field(alias="expressionType")
    state: Optional[SpState]
    bid: Optional[float]
    ad_group_id: Optional[str] = Field(alias="adGroupId")
    campaign_id: Optional[str] = Field(alias="campaignId")
    extended_data: Optional[ExtendedData] = Field(alias="extendedData")

    class Config:
        use_enum_values = True
        allow_population_by_field_name = True
