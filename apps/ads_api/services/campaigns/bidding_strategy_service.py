from typing import Optional

from apps.ads_api.constants import BiddingStrategies, SponsoredProductsPlacement
from apps.ads_api.entities.amazon_ads.sponsored_products.campaign import PlacementBidding, DynamicBidding


class BiddingStrategyService:
    def __init__(
        self,
        bidding_strategy: BiddingStrategies,
        pp: Optional[int] = None,
        tos: Optional[int] = None,
    ):
        self.pp = pp
        self.tos = tos
        self.bidding_strategy = bidding_strategy

    def get_bidding_strategy(self) -> DynamicBidding:
        """Add placement multipliers if specified"""
        bidding = DynamicBidding(strategy=self.bidding_strategy, placement_bidding=[])
        if self.tos is not None or self.pp is not None:
            bidding.placement_bidding = list(
                filter(
                    None,
                    [
                        PlacementBidding(percentage=self.tos, placement=SponsoredProductsPlacement.PLACEMENT_TOP)
                        if self.tos is not None
                        else None,
                        PlacementBidding(
                            percentage=self.pp, placement=SponsoredProductsPlacement.PLACEMENT_PRODUCT_PAGE
                        )
                        if self.pp is not None
                        else None,
                    ],
                )
            )
        return bidding
