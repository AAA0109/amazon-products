import logging
from typing import List


from apps.ads_api.constants import (
    BiddingStrategies,
    DEFAULT_MIN_BID,
    SpState, MatchType,
)
from apps.ads_api.entities.amazon_ads.sponsored_products.ad_group import AdGroupEntity
from apps.ads_api.entities.amazon_ads.sponsored_products.campaign import CampaignEntity
from apps.ads_api.entities.amazon_ads.sponsored_products.keywords import KeywordEntity
from apps.ads_api.entities.amazon_ads.sponsored_products.product_ad import ProductAdEntity
from apps.ads_api.campaigns.base_campaign import BaseCampaign
from apps.ads_api.exceptions.ads_api.campaigns import CampaignAlreadyExists
from apps.ads_api.interfaces.entities.campaign.campaign_creatable_interface import (
    CampaignCreatableInterface,
)
from apps.ads_api.models import CampaignPurpose, Book, Campaign
from apps.ads_api.repositories.campaign_repository import CampaignRepository

_logger = logging.getLogger(__name__)


class GPCampaign(BaseCampaign, CampaignCreatableInterface):
    def __init__(self, book: Book, text_keywords: List[str]):
        super().__init__(book)
        self._text_keywords = self.clean_keywords(text_keywords)
        self._created_campaigns = []
        self._keywords_to_create = []

    def create(
            self,
    ) -> list[tuple[CampaignEntity, AdGroupEntity, ProductAdEntity]]:
        self._raise_exception_if_campaign_already_exists()

        campaign = self.build_campaign_entity(
            book=self.book,
            campaign_purpose=CampaignPurpose.GP,
            bidding_strategy=BiddingStrategies.FIXED_BIDS,
        )
        campaign = self.create_campaign(campaign)
        ad_group = self.create_ad_group_for_campaign(campaign)
        product_ad = self.create_product_ad_for_ad_group(ad_group)

        self._created_campaigns.append((campaign, ad_group, product_ad))

        self._add_keywords_to_campaign(campaign.external_id, ad_group.external_id)
        return self._created_campaigns

    def _raise_exception_if_campaign_already_exists(self):
        gp_campaign_exists = CampaignRepository.exists_by(
            books=self.book,
            campaign_purpose=CampaignPurpose.GP,
            state__iexact=SpState.ENABLED,
            bidding_strategy=BiddingStrategies.FIXED_BIDS,
        )
        if gp_campaign_exists:
            same_campaigns_ids = Campaign.objects.filter(
                books=self.book,
                campaign_purpose=CampaignPurpose.GP,
                state__iexact=SpState.ENABLED,
                bidding_strategy=BiddingStrategies.FIXED_BIDS,
            ).values_list("id", flat=True)
            _logger.error(
                "GP Campaign already exists for Book: %s, same campaigns - %s",
                self.book.asin,
                list(same_campaigns_ids),
            )
            raise CampaignAlreadyExists()

    def _add_keywords_to_campaign(self, campaign_id: str, ad_group_id: str):
        for keyword_text in self._text_keywords:
            if len(keyword_text) == 0:
                continue

            self._keywords_to_create.append(
                KeywordEntity(
                    campaign_id=campaign_id,
                    ad_group_id=ad_group_id,
                    keyword_text=keyword_text,
                    bid=DEFAULT_MIN_BID,
                    state=SpState.ENABLED,
                    match_type=MatchType.BROAD,
                ).dict(exclude_none=True, by_alias=True))

        self.create_keywords(self._keywords_to_create)
