from typing import Optional

from pydantic import BaseModel, Field

from apps.ads_api.constants import (
    DEFAULT_DAILY_BUDGET,
    BiddingStrategies,
    CampaignTargetingType,
    SponsoredProductsPlacement,
    SpState,
)
from apps.ads_api.entities.amazon_ads.sponsored_products.extended_data import (
    ExtendedData,
)


class PlacementBidding(BaseModel):
    percentage: int
    placement: SponsoredProductsPlacement

    class Config:
        use_enum_values = True
        allow_population_by_field_name = True


class DynamicBidding(BaseModel):
    strategy: Optional[BiddingStrategies]
    placement_bidding: Optional[list[PlacementBidding]] = Field(alias="placementBidding")

    class Config:
        use_enum_values = True
        allow_population_by_field_name = True


class Budget(BaseModel):
    budget: float = Field(default=DEFAULT_DAILY_BUDGET)
    budget_type: str = Field(alias="budgetType")

    class Config:
        allow_population_by_field_name = True


class CampaignEntity(BaseModel):
    name: Optional[str]
    targeting_type: Optional[CampaignTargetingType] = Field(alias="targetingType")
    budget: Optional[Budget]
    start_date: Optional[str] = Field(alias="startDate")
    dynamic_bidding: Optional[DynamicBidding] = Field(alias="dynamicBidding")
    state: Optional[SpState] = Field(default=SpState.ENABLED)
    campaign_purpose: Optional[str]
    end_date: Optional[str] = Field(alias="endDate")
    external_id: Optional[str] = Field(alias="campaignId")
    internal_id: Optional[str]
    bid_adjustment: Optional[bool] = Field(alias="premiumBidAdjustment")
    portfolio_id: Optional[str] = Field(alias="portfolioId")
    extended_data: Optional[ExtendedData] = Field(alias="extendedData")

    class Config:
        use_enum_values = True
        allow_population_by_field_name = True
