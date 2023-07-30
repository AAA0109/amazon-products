import logging
from typing import Optional

from django.db.models import Sum, Case, When

from apps.ads_api.constants import (
    CAMPAIGN_MAX_TARGETS_MAP,
    BiddingStrategies,
    DEFAULT_BID, SpState, MatchType,
)
from apps.ads_api.entities.amazon_ads.sponsored_products.ad_group import AdGroupEntity
from apps.ads_api.entities.amazon_ads.sponsored_products.campaign import CampaignEntity
from apps.ads_api.entities.amazon_ads.sponsored_products.keywords import KeywordEntity
from apps.ads_api.entities.amazon_ads.sponsored_products.product_ad import ProductAdEntity
from apps.ads_api.campaigns.base_campaign import BaseCampaign
from apps.ads_api.interfaces.entities.campaign.campaign_creatable_interface import (
    CampaignCreatableInterface,
)
from apps.ads_api.mixins.campaigns.filter_duplicate_keywords_mixin import FilterDuplicateKeywordsMixin
from apps.ads_api.models import Keyword, Book, CampaignPurpose, Campaign, AdGroup
from apps.utils.chunks import chunker

_logger = logging.getLogger(__name__)


class ExactScaleCampaign(
    BaseCampaign,
    CampaignCreatableInterface,
    FilterDuplicateKeywordsMixin
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
        self._keywords_to_create = []
        self._created_campaigns = []

    def create(
            self,
    ) -> list[tuple[CampaignEntity, AdGroupEntity, ProductAdEntity]]:
        self._remove_existing_keywords()
        self._fill_up_existing_campaigns_with_keywords()

        for text_keywords_batch in chunker(
                self._text_keywords, CAMPAIGN_MAX_TARGETS_MAP[CampaignPurpose.Exact_Scale]
        ):
            campaign = self.build_campaign_entity(
                book=self.book,
                bidding_strategy=BiddingStrategies.FIXED_BIDS,
                campaign_purpose=CampaignPurpose.Exact_Scale,
            )
            campaign = self.create_campaign(campaign)
            ad_group = self.create_ad_group_for_campaign(
                campaign, bid=self._default_bid
            )
            product_ad = self.create_product_ad_for_ad_group(ad_group)

            for keyword_text in text_keywords_batch:
                self._keywords_to_create.append(
                    KeywordEntity(
                        campaign_id=campaign.external_id,
                        ad_group_id=ad_group.external_id,
                        keyword_text=keyword_text,
                        bid=self._default_bid,
                        state=SpState.ENABLED,
                        match_type=MatchType.EXACT,
                    ).dict(exclude_none=True, by_alias=True))
            self._created_campaigns.append((campaign, ad_group, product_ad))

        self.create_keywords(self._keywords_to_create)
        return self._created_campaigns

    def get_existing_keywords_text(self) -> list[str]:
        return (
            Keyword.objects.filter(
                campaign__profile=self.book.profile,
                campaign__books__asin=self.book.asin,
                keyword_type="Positive",
                match_type=MatchType.EXACT.value,
            )
            .values_list("keyword_text", flat=True)
            .distinct("keyword_text")
        )

    def _fill_up_existing_campaigns_with_keywords(self):
        existing_campaigns = (
            Campaign.objects.filter(
                campaign_purpose=CampaignPurpose.Exact_Scale,
                books__asin=self.book.asin,
            )
            .exclude(campaign_name__contains="Single")
            .annotate(keywords_count=Sum(Case(When(keyword__state=SpState.ENABLED.value, then=1))))
            .annotate(ad_groups_count=Sum("ad_groups"))
            .filter(ad_groups_count=1)
            .order_by("keywords_count")
        )

        for campaign in existing_campaigns:
            for text_keywords_batch in chunker(
                    self._text_keywords,
                    CAMPAIGN_MAX_TARGETS_MAP[CampaignPurpose.Exact_Scale]
                    - campaign.keywords_count,
            ):
                ad_group_id = (
                    AdGroup.objects.filter(campaign=campaign).first().ad_group_id
                )

                for keyword in text_keywords_batch:
                    self._keywords_to_create.append(
                        KeywordEntity(
                            campaign_id=campaign.campaign_id_amazon,
                            ad_group_id=ad_group_id,
                            keyword_text=keyword,
                            bid=self._default_bid,
                            state=SpState.ENABLED,
                            match_type=MatchType.EXACT,
                        ).dict(exclude_none=True, by_alias=True))

                    self._text_keywords.remove(keyword)

