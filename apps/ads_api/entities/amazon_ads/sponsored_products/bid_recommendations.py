from typing import Optional, Union

from pydantic import BaseModel, Field

from apps.ads_api.constants import (
    BiddingStrategies,
    BidRecommendationType,
    SponsoredProductsPlacement,
    TargetingExpressionType,
)


class TargetingExpression(BaseModel):
    """The targeting expression. The type property specifies the targeting option. Use CLOSE_MATCH to match your auto
    targeting ads closely to the specified value. Use LOOSE_MATCH to match your auto targeting ads broadly to the
    specified value. Use SUBSTITUTES to display your auto targeting ads along with substitutable products.
    Use COMPLEMENTS to display your auto targeting ads along with affiliated products.
    Use KEYWORD_BROAD_MATCH to broadly match your keyword targeting ads with search queries.
    Use KEYWORD_EXACT_MATCH to exactly match your keyword targeting ads with search queries.
    Use KEYWORD_PHRASE_MATCH to match your keyword targeting ads with search phrases.
    """

    targeting_type: TargetingExpressionType = Field(alias="type")
    value: Optional[str] = Field(description="The targeting expression value")

    class Config:
        use_enum_values = True
        allow_population_by_field_name = True


class PlacementAdjustment(BaseModel):
    """Specifies bid adjustments based on the placement location. Use PLACEMENT_TOP for the top of the search page.
    Use PLACEMENT_PRODUCT_PAGE for a product page."""

    predicate: SponsoredProductsPlacement
    percentage: int = Field()

    class Config:
        use_enum_values = True
        allow_population_by_field_name = True


class Bidding(BaseModel):
    adjustments: Optional[list[PlacementAdjustment]] = Field(
        max_items=2, description="Placement adjustment configuration for the campaign."
    )
    strategy: Union[BiddingStrategies, str] = Field(
        description=(
            "The bidding strategy selected for the campaign. \
        Use LEGACY_FOR_SALES to lower your bid in real time when your ad may be less likely to convert to a sale. \
        Use AUTO_FOR_SALES to increase your bid in real time when your ad may be more likely to convert to a sale \
        or lower your bid when less likely to convert to a sale. \
        Use MANUAL to use your exact bid along with any manual adjustments."
        )
    )

    class Config:
        use_enum_values = True
        allow_population_by_field_name = True


class AgGroupBasedBidRecommensdationPayload(BaseModel):
    targeting_expressions: list[TargetingExpression] = Field(alias="targetingExpressions", max_items=100)
    campaign_id: str = Field(alias="campaignId", description="The campaign identifier.")
    ad_group_id: str = Field(alias="adGroupId", description="The ad group identifier.")
    recommendation_type: BidRecommendationType = Field(
        alias="recommendationType",
        default=BidRecommendationType.BIDS_FOR_EXISTING_AD_GROUP,
        description="The bid recommendation type.",
    )

    class Config:
        use_enum_values = True
        allow_population_by_field_name = True


class AsinsBasedBidRecommensdationPayload(BaseModel):
    asins: list[str] = Field(max_items=50, description="The list of ad ASINs in the ad group.")
    campaign_id: str = Field(alias="campaignId", description="The campaign identifier.")
    targeting_expressions: list[TargetingExpression] = Field(alias="targetingExpressions", max_items=100)
    bidding: Bidding = Field(description="Bidding control configuration for the campaign.")
    recommendation_type: BidRecommendationType = Field(
        alias="recommendationType",
        default=BidRecommendationType.BIDS_FOR_EXISTING_AD_GROUP,
        description="The bid recommendation type.",
    )

    class Config:
        use_enum_values = True
        allow_population_by_field_name = True
