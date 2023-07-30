import logging

from apps.ads_api.constants import BiddingStrategies, DEFAULT_MIN_BID, SpState
from apps.ads_api.entities.amazon_ads.sponsored_products.ad_group import AdGroupEntity
from apps.ads_api.entities.amazon_ads.sponsored_products.campaign import CampaignEntity
from apps.ads_api.entities.amazon_ads.sponsored_products.product_ad import ProductAdEntity
from apps.ads_api.campaigns.base_campaign import BaseCampaign
from apps.ads_api.exceptions.ads_api.campaigns import CampaignAlreadyExists
from apps.ads_api.interfaces.entities.campaign.campaign_creatable_interface import (
    CampaignCreatableInterface,
)
from apps.ads_api.models import CampaignPurpose, Book, Campaign
from apps.ads_api.repositories.campaign_repository import CampaignRepository

_logger = logging.getLogger(__name__)


class AutoGPCampaign(BaseCampaign, CampaignCreatableInterface):
    def __init__(self, book: Book):
        super().__init__(book)
        self._created_campaigns = []

    def create(
            self,
    ) -> list[tuple[CampaignEntity, AdGroupEntity, ProductAdEntity]]:
        """Creates Auto GP campaign with low bids"""
        self._raise_exception_if_campaign_already_exists()

        campaign = self.build_campaign_entity(
            book=self.book,
            campaign_purpose=CampaignPurpose.Auto_GP,
            bidding_strategy=BiddingStrategies.FIXED_BIDS,
        )

        campaign = self.create_campaign(campaign)
        ad_group = self.create_ad_group_for_campaign(campaign, bid=DEFAULT_MIN_BID)
        product_ad = self.create_product_ad_for_ad_group(ad_group)
        self._created_campaigns.append((campaign, ad_group, product_ad))

        return self._created_campaigns

    def _raise_exception_if_campaign_already_exists(self):
        gp_campaign_exists = CampaignRepository.exists_by(
            books=self.book,
            campaign_purpose=CampaignPurpose.Auto_GP,
            state__iexact=SpState.ENABLED,
            bidding_strategy=BiddingStrategies.FIXED_BIDS,
        )
        if gp_campaign_exists:
            same_campaigns_ids = Campaign.objects.filter(
                books=self.book,
                campaign_purpose=CampaignPurpose.Auto_GP,
                state__iexact=SpState.ENABLED,
                bidding_strategy=BiddingStrategies.FIXED_BIDS,
            ).values_list("id", flat=True)
            _logger.error(
                "AutoGP Campaign already exists for Book: %s, same campaigns - %s",
                self.book.asin,
                list(same_campaigns_ids),
            )
            raise CampaignAlreadyExists()
