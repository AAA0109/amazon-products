import logging
from typing import Optional

from django.db.models import Q

from apps.ads_api.adapters.amazon_ads.bid_recomendations_adapter import (
    BidRecommendationsAdapter,
)
from apps.ads_api.campaigns.base_campaign import BaseCampaign
from apps.ads_api.constants import (
    DEFAULT_BID,
    TOS_SINGLE_KEYWORD_CAMPAIGNS,
    BiddingStrategies,
    MatchType,
    SpEndpoint,
    SpState,
    TargetingExpressionType,
)
from apps.ads_api.entities.amazon_ads.sponsored_products.ad_group import AdGroupEntity
from apps.ads_api.entities.amazon_ads.sponsored_products.campaign import CampaignEntity
from apps.ads_api.entities.amazon_ads.sponsored_products.keywords import KeywordEntity
from apps.ads_api.entities.amazon_ads.sponsored_products.product_ad import (
    ProductAdEntity,
)
from apps.ads_api.interfaces.entities.campaign.campaign_creatable_interface import (
    CampaignCreatableInterface,
)
from apps.ads_api.mixins.campaigns.filter_duplicate_keywords_mixin import (
    FilterDuplicateKeywordsMixin,
)
from apps.ads_api.models import Book, CampaignPurpose, Keyword
from apps.ads_api.services.keywords.cleaner_service import KeywordsCleanerService

_logger = logging.getLogger(__name__)


class ExactScaleSingleCampaign(
    BaseCampaign,
    CampaignCreatableInterface,
    FilterDuplicateKeywordsMixin,
):
    def __init__(
        self,
        book: Book,
        text_keywords: list[str],
        default_bid: Optional[float] = DEFAULT_BID,
    ):
        super().__init__(book)
        self._text_keywords: set = set(self.clean_keywords(text_keywords))
        self._default_bid = default_bid
        self.book = book
        self._keywords_to_create = []
        self._created_campaigns = []

    def create(
        self,
    ) -> list[tuple[CampaignEntity, AdGroupEntity, ProductAdEntity]]:
        self._remove_existing_keywords()

        for keyword_text in self._text_keywords:
            campaign = self.build_campaign_entity(
                book=self.book,
                bidding_strategy=BiddingStrategies.FIXED_BIDS,
                campaign_purpose=CampaignPurpose.Exact_Scale_Single,
                tos=TOS_SINGLE_KEYWORD_CAMPAIGNS,
            )

            campaign = self.create_campaign(campaign)
            ad_group = self.create_ad_group_for_campaign(campaign, bid=self._default_bid)
            product_ad = self.create_product_ad_for_ad_group(ad_group)

            if self._default_bid:
                bid = self._default_bid
            else:
                bid = self.get_bid_recommendation(
                    campaign_external_id=campaign.external_id,
                    ad_group_external_id=ad_group.external_id,
                    keyword_text=keyword_text,
                )

            self._keywords_to_create.append(
                KeywordEntity(
                    campaign_id=campaign.external_id,
                    ad_group_id=ad_group.external_id,
                    keyword_text=keyword_text,
                    bid=bid,
                    state=SpState.ENABLED,
                    match_type=MatchType.EXACT,
                ).dict(exclude_none=True, by_alias=True)
            )
            self._created_campaigns.append((campaign, ad_group, product_ad))

        self.create_keywords(self._keywords_to_create)
        return self._created_campaigns

    def get_existing_keywords_text(self) -> list[str]:
        return (
            Keyword.objects.filter(
                Q(campaign__campaign_name__contains=MatchType.EXACT.lower())
                & Q(campaign__campaign_name__contains="Single"),
                campaign__profile=self.book.profile,
                campaign__books__asin=self.book.asin,
                keyword_type="Positive",
            )
            .exclude(campaign__state=SpState.ARCHIVED.value)
            .values_list("keyword_text", flat=True)
            .distinct("keyword_text")
        )

    def get_bid_recommendation(
        self, campaign_external_id: str, ad_group_external_id: str, keyword_text: str
    ) -> float:
        adapter = BidRecommendationsAdapter(self.book.profile)
        (
            start_recommended_value,
            mid_recommended_value,
            end_recommended_value,
        ) = adapter.get_bid_recommendations(
            campaign_id=campaign_external_id,
            ad_group_id=ad_group_external_id,
            value=keyword_text,
            type_=TargetingExpressionType.KEYWORD_EXACT_MATCH,
        )

        if mid_recommended_value != 0.0:
            if mid_recommended_value > DEFAULT_BID * 2:
                bid = DEFAULT_BID * 2
            elif mid_recommended_value < DEFAULT_BID:
                bid = DEFAULT_BID
            else:
                bid = mid_recommended_value
        else:
            bid = DEFAULT_BID
        return bid
