from typing import Optional

from apps.ads_api.campaigns.base_campaign import BaseCampaign
from apps.ads_api.constants import (
    CAMPAIGN_MAX_TARGETS_MAP,
    DEFAULT_BID,
    BiddingStrategies,
    SpExpressionType,
    SpState,
)
from apps.ads_api.entities.amazon_ads.sponsored_products.ad_group import AdGroupEntity
from apps.ads_api.entities.amazon_ads.sponsored_products.campaign import CampaignEntity
from apps.ads_api.entities.amazon_ads.sponsored_products.product_ad import (
    ProductAdEntity,
)
from apps.ads_api.entities.amazon_ads.sponsored_products.targets import (
    Expression,
    TargetEntity,
)
from apps.ads_api.interfaces.entities.campaign.campaign_creatable_interface import (
    CampaignCreatableInterface,
)
from apps.ads_api.mixins.campaigns.filter_duplicate_targets_mixin import (
    FilterDuplicateTargetsMixin,
)
from apps.ads_api.models import Book, Target, AdGroup, ProductAd, Campaign
from apps.utils.chunks import chunker


class BaseProductCampaign(
    BaseCampaign,
    CampaignCreatableInterface,
    FilterDuplicateTargetsMixin,
):
    CAMPAIGN_PURPOSE = None
    RESOLVED_EXPRESSION_TYPE = None

    def __init__(
        self,
        book: Book,
        text_targets: list[str],
        default_bid: Optional[float] = DEFAULT_BID,
    ):
        super().__init__(book)
        self._default_bid = default_bid
        self._text_targets: set = set(
            self.clean_keywords(keywords=text_targets, is_asins=True, singularize=False)
        )
        self._created_campaigns = []

    def _create_target_entity(self, campaign_id: str, ad_group_id: str, text_target: str):
        return TargetEntity(
            campaign_id=campaign_id,
            ad_group_id=ad_group_id,
            bid=self._default_bid,
            state=SpState.ENABLED,
            expression=[
                Expression(
                    type=self.RESOLVED_EXPRESSION_TYPE,
                    value=text_target,
                )
            ],
            expression_type=SpExpressionType.MANUAL,
        ).dict(exclude_none=True, by_alias=True)
    
    def create(self) -> list[tuple[CampaignEntity, AdGroupEntity, ProductAdEntity]]:
        targets_to_create = []

        self._remove_existing_targeted_asins()

        for text_targets_batch in chunker(
            self._text_targets, CAMPAIGN_MAX_TARGETS_MAP[self.CAMPAIGN_PURPOSE]
        ):
            campaign = self.build_campaign_entity(
                book=self.book,
                campaign_purpose=self.CAMPAIGN_PURPOSE,
                bidding_strategy=BiddingStrategies.DOWN_ONLY,
            )

            campaign = self.create_campaign(campaign)
            ad_group = self.create_ad_group_for_campaign(campaign, bid=self._default_bid)
            product_ad = self.create_product_ad_for_ad_group(ad_group)

            for text_target in text_targets_batch:
                targets_to_create.append(
                    self._create_target_entity(campaign.external_id, ad_group.external_id, text_target)
                )
            self._created_campaigns.append((campaign, ad_group, product_ad))

        self.create_targets(targets_to_create)
        return self._created_campaigns
    
    def update(self, campaign: Campaign, books: list[Book]):
        targets_to_create = []

        campaign_entity = CampaignEntity(
            external_id=campaign.campaign_id_amazon,
            internal_id=campaign.id,
            name=campaign.campaign_name
        )

        ad_group = AdGroup.objects.filter(campaign=campaign).first()
        if ad_group is None:
            ad_group_entity=self.create_ad_group_for_campaign(campaign_entity, bid=self._default_bid)
        else:
            ad_group_entity=AdGroupEntity(
                campaign_id=campaign.campaign_id_amazon,
                external_id=ad_group.ad_group_id,
                internal_id=ad_group.id,
                name=campaign.campaign_name,
                bid=ad_group.default_bid
            )
        
        for book in books:
            product_ad = ProductAd.objects.filter(campaign=campaign, asin=book.asin).first()
            if product_ad is None:
                product_ad = self.create_product_ad_for_ad_group(ad_group_entity, book)

        for text_target in self._text_targets:
            targets_to_create.append(
                self._create_target_entity(campaign_entity.external_id, ad_group_entity.external_id, text_target)
            )

        self.create_targets(targets_to_create)

    def get_existing_targeted_asins(self):
        return (
            Target.objects.filter(
                campaign__campaign_name__contains=self.CAMPAIGN_PURPOSE,
                campaign__profile=self.book.profile,
                campaign__books__asin=self.book.asin,
                keyword_type="Positive",
                resolved_expression_type=self.RESOLVED_EXPRESSION_TYPE,
            )
            .values_list("resolved_expression_text", flat=True)
            .distinct("resolved_expression_text")
        )
