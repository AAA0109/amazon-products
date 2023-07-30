from apps.ads_api.adapters.amazon_ads.base_amazon_ads_adapter import (
    BaseAmazonAdsAdapter,
)
from apps.ads_api.constants import TargetingExpressionType
from apps.ads_api.entities.amazon_ads.sponsored_products.bid_recommendations import (
    AgGroupBasedBidRecommensdationPayload,
    TargetingExpression,
)
from apps.ads_api.models import Profile


class BidRecommendationsAdapter(BaseAmazonAdsAdapter):
    def __init__(self, profile: Profile):
        super().__init__(profile.profile_server)
        self.profile = profile

    def get_bid_recommendations(
        self,
        campaign_id: str,
        ad_group_id: str,
        value: str,
        type_: TargetingExpressionType,
    ) -> tuple[float, float, float]:
        """
        Retrieves bid recommendations for the specified ad group and targeting expression.

        Args:
            campaign_id (str): The identifier of the campaign that contains the ad group.
            ad_group_id (str): The identifier of the ad group that the bid recommendations are being requested for.
            value (str): The value of the targeting expression.
            type_ (TargetingExpressionType): The type of the targeting expression.

        Returns:
            tuple[float, float, float]: A tuple containing three suggested bid values.
            The first value represents the lowest suggested bid,
            the second value represents the median suggested bid,
            and the third value represents the highest suggested bid.

        """
        suggested_bids = (0.0, 0.0, 0.0)

        payload = AgGroupBasedBidRecommensdationPayload(
            campaign_id=campaign_id,
            ad_group_id=ad_group_id,
            targeting_expressions=[TargetingExpression(value=value, type=type_)],
        ).dict(by_alias=True, exclude_none=True)

        response = self.send_request(
            url="/sp/targets/bid/recommendations",
            method="POST",
            body=payload,
            extra_headers={
                "Amazon-Advertising-API-Scope": str(self.profile.profile_id),
                "Content-Type": "application/json",
            },
        )
        if "suggestedBid" in str(response.json()):
            for bid_recommendation in response.json()["bidRecommendations"]:
                for bid_recommendation_for_targeting_expression in bid_recommendation[
                    "bidRecommendationsForTargetingExpressions"
                ]:
                    (
                        start_bid_value,
                        mid_bid_value,
                        end_bid_value,
                    ) = bid_recommendation_for_targeting_expression["bidValues"]

                    suggested_bids = (
                        start_bid_value["suggestedBid"],
                        mid_bid_value["suggestedBid"],
                        end_bid_value["suggestedBid"],
                    )

        return suggested_bids
