import logging
from decimal import Decimal
from typing import Optional, Iterator

from apps.ads_api.adapters.amazon_ads.sponsored_products.campaigns_adapter import (
    CampaignAdapter,
)
from apps.ads_api.constants import SponsoredProductsPlacement, BiddingStrategies, TimeUnit
from apps.ads_api.entities.amazon_ads.sponsored_products.campaign import (
    CampaignEntity,
)
from apps.ads_api.entities.amazon_ads.sponsored_products.search_filters import (
    CampaignSearchFilter,
)
from apps.ads_api.models import Profile, Campaign
from apps.ads_api.services.campaigns.identify_campaign_purpose_service import (
    IdentifyCampaignPurpose,
)
from apps.utils.iso_to_epoch_converter import IsoToEpochConverter

_logger = logging.getLogger(__name__)


class SyncCampaignsService:
    def __init__(self, profile_ids: Optional[list[int]] = None):
        """
        :param profile_ids: primary keys of profiles. If no IDs
            were given, all managed profiles would be taken to process.
        """
        self._profile_ids = profile_ids

    def sync(self):
        """Sync high level campaign data for managed profiles."""
        converter = IsoToEpochConverter()

        for profile in self.profiles_iterator():
            campaigns = self.get_campaigns_from_adapter(profile)

            for campaign in campaigns:
                placement_top, placement_product_pages = self.get_placements(campaign)
                Campaign.objects.update_or_create(
                    campaign_id_amazon=campaign.external_id,
                    defaults=dict(
                        profile=profile,
                        portfolio_id=campaign.portfolio_id,
                        targeting_type=campaign.targeting_type,
                        serving_status=campaign.extended_data.serving_status,
                        last_updated_date_on_amazon=
                        converter.iso_to_epoch(
                            campaign.extended_data.last_update_date_time,
                            convert_to=TimeUnit.MILLISECOND
                        ),
                        campaign_name=campaign.name,
                        state=campaign.state,
                        placement_tos_mult=placement_top,
                        placement_pp_mult=placement_product_pages,
                        bidding_strategy=campaign.dynamic_bidding.strategy
                        if campaign.dynamic_bidding.strategy
                        else BiddingStrategies.DOWN_ONLY.value,
                        premium_bid_adjustment=campaign.bid_adjustment
                        if campaign.bid_adjustment
                        else False,
                        daily_budget=Decimal(campaign.budget.budget),
                        campaign_purpose=IdentifyCampaignPurpose.identify_campaign_purpose(
                            campaign.name
                        ),
                    )
                )

            _logger.info(
                f"{len(campaigns)} campaigns synced for profile: {profile.nickname} [{profile.country_code}]"
            )

    def profiles_iterator(self) -> Iterator[Profile]:
        """
        Retrieves profiles from db by given ids. If no IDs
        were given, all managed profiles would be taken to process.

        :return: iterator of Django Profile models
        """
        if self._profile_ids:
            profiles = Profile.objects.filter(id__in=self._profile_ids)
        else:
            profiles = Profile.objects.filter(managed=True)

        for profile in profiles:
            yield profile

    @classmethod
    def get_campaigns_from_adapter(cls, profile: Profile) -> list[CampaignEntity]:
        """
        Retrieves campaigns from amazon API by using adapter.

        :param profile: Django ORM Profile model
        :return: list of CampaignEntity objects
        """
        adapter = CampaignAdapter(profile)

        profile_campaigns = adapter.list(CampaignSearchFilter())
        return profile_campaigns

    @classmethod
    def get_placements(cls, campaign: CampaignEntity) -> tuple[int, int]:
        """
        Extract the placement multiplier numbers from JSON & lists structure of Amazon API response
        If adjustments does not exist then the variable adjustments will be NoneType
        Must make sure that Amazon doesn't respond with an empty list as it will not be NoneType

        :param campaign: campaign from amazon response API v3
        :return: tuple containing count of top placement positions and count of product pages
        """
        placement_top = 0
        placement_product_pages = 0
        if campaign.dynamic_bidding:
            for placement in campaign.dynamic_bidding.placement_bidding:
                if (
                        placement.placement
                        == SponsoredProductsPlacement.PLACEMENT_TOP.value
                ):
                    placement_top = placement.percentage
                elif (
                        placement.placement
                        == SponsoredProductsPlacement.PLACEMENT_PRODUCT_PAGE.value
                ):
                    placement_product_pages = placement.percentage
        return placement_top, placement_product_pages
