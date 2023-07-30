import logging

from apps.ads_api.adapters.amazon_ads.sponsored_products.targets_adapter import (
    TargetsAdapter,
)
from apps.ads_api.campaigns.base_campaign import BaseCampaign
from apps.ads_api.constants import (
    DEFAULT_BID,
    TOS_SINGLE_KEYWORD_CAMPAIGNS,
    BiddingStrategies,
    SpEndpoint,
    SpState,
    TargetingExpressionPredicateType,
)
from apps.ads_api.entities.amazon_ads.sponsored_products.ad_group import AdGroupEntity
from apps.ads_api.entities.amazon_ads.sponsored_products.campaign import CampaignEntity
from apps.ads_api.entities.amazon_ads.sponsored_products.product_ad import (
    ProductAdEntity,
)
from apps.ads_api.entities.amazon_ads.sponsored_products.targets import TargetEntity
from apps.ads_api.interfaces.entities.campaign.campaign_creatable_interface import (
    CampaignCreatableInterface,
)
from apps.ads_api.models import Book, CampaignPurpose, Profile, Target, Campaign
from apps.ads_api.services.campaigns.format_negatives_craetion_service import (
    FormatNegativesCreationService,
)

_logger = logging.getLogger(__name__)


class DiscoveryCampaign(BaseCampaign, CampaignCreatableInterface):
    def __init__(self, book: Book, bid: float = DEFAULT_BID):
        super().__init__(book)
        self._bid = bid
        self._created_campaigns: list[tuple[CampaignEntity, AdGroupEntity, ProductAdEntity]] = []

    def create(
        self,
    ) -> list[tuple[CampaignEntity, AdGroupEntity, ProductAdEntity]]:
        """Creates 4 Auto campaigns with one targeting group enabled in each"""
        # create 4 new campaigns for book
        targets_adapter = TargetsAdapter(self.book.profile)

        for purpose, placement in [
            (CampaignPurpose.Discovery_Loose_Match, dict(tos=TOS_SINGLE_KEYWORD_CAMPAIGNS / 2)),
            (CampaignPurpose.Discovery_Close_Match, dict(tos=TOS_SINGLE_KEYWORD_CAMPAIGNS / 2)),
            (CampaignPurpose.Discovery_Substitutes, dict(pp=TOS_SINGLE_KEYWORD_CAMPAIGNS / 2)),
            (CampaignPurpose.Discovery_Complements, dict(pp=TOS_SINGLE_KEYWORD_CAMPAIGNS / 2)),
        ]:
            campaign_exists = Campaign.objects.filter(
                books=self.book,
                campaign_purpose=purpose,
                state__iexact=SpState.ENABLED,
                campaign_name__contains=purpose,
            ).exists()
            if campaign_exists:
                continue
            campaign = self.build_campaign_entity(
                book=self.book,
                bidding_strategy=BiddingStrategies.DOWN_ONLY,
                campaign_purpose=purpose,
                **placement,
            )

            campaign = self.create_campaign(campaign)
            ad_group = self.create_ad_group_for_campaign(campaign, bid=self._bid)
            product_ad = self.create_product_ad_for_ad_group(ad_group)

            self._created_campaigns.append((campaign, ad_group, product_ad))

        # sync newly created campaign targets
        _logger.info("created campaigns locally - [%s]", self._created_campaigns)

        campaign_external_ids = [campaign.external_id for campaign, _, _ in self._created_campaigns]
        _logger.info("Created campaigns ids - [%s]", campaign_external_ids)
        from apps.ads_api.data_exchange import sync_keywords

        sync_keywords(
            endpoint=SpEndpoint.TARGETS,
            profile_ids=Profile.objects.filter(profile_id=self.book.profile.profile_id).values_list("id"),
            campaign_id_amazon_list=[str(c) for c in campaign_external_ids],
        )
        # pause other 3 targeting groups in each campaign
        # get the targets
        new_targets = Target.objects.filter(campaign__campaign_id_amazon__in=campaign_external_ids)
        _logger.info("New targets - [%s], count[%s]", new_targets, len(new_targets))

        auto_purpose_exp_type_map = {
            "Loose-Match": [
                TargetingExpressionPredicateType.QUERY_HIGH_REL_MATCHES.value,
                TargetingExpressionPredicateType.ASIN_SUBSTITUTE_RELATED.value,
                TargetingExpressionPredicateType.ASIN_ACCESSORY_RELATED.value,
            ],  # QUERY_BROAD_REL_MATCHES
            "Close-Match": [
                TargetingExpressionPredicateType.QUERY_BROAD_REL_MATCHES.value,
                TargetingExpressionPredicateType.ASIN_SUBSTITUTE_RELATED.value,
                TargetingExpressionPredicateType.ASIN_ACCESSORY_RELATED.value,
            ],  # QUERY_HIGH_REL_MATCHES
            "Substitutes": [
                TargetingExpressionPredicateType.QUERY_BROAD_REL_MATCHES.value,
                TargetingExpressionPredicateType.QUERY_HIGH_REL_MATCHES.value,
                TargetingExpressionPredicateType.ASIN_ACCESSORY_RELATED.value,
            ],  # ASIN_SUBSTITUTE_RELATED
            "Complements": [
                TargetingExpressionPredicateType.QUERY_BROAD_REL_MATCHES.value,
                TargetingExpressionPredicateType.QUERY_HIGH_REL_MATCHES.value,
                TargetingExpressionPredicateType.ASIN_SUBSTITUTE_RELATED.value,
            ],  # ASIN_ACCESSORY_RELATED
        }
        targets_to_update = []
        for target in new_targets:
            purpose = str(target.campaign.campaign_purpose).replace("Auto-Discovery-", "")
            exp_types_to_pause = auto_purpose_exp_type_map[purpose]
            expression_type = target.resolved_expression_type
            if expression_type in exp_types_to_pause:
                targets_to_update.append(
                    TargetEntity(
                        external_id=target.target_id,
                        state=SpState.PAUSED,
                    ).dict(exclude_none=True, by_alias=True)
                )
        _logger.info("Targets to update - %s", targets_to_update)

        targets_adapter.batch_update(targets_to_update)

        self.add_format_negatives_to_created_campaigns()

        return self._created_campaigns

    def add_format_negatives_to_created_campaigns(self) -> tuple[list, list]:
        service = FormatNegativesCreationService(book=self.book)
        return service.add_format_negatives_to_campagins([campaign for campaign, _, _ in self._created_campaigns])
