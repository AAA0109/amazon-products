import logging
from typing import Optional

from apps.ads_api.adapters.amazon_ads.sponsored_products.keywords_adapter import (
    KeywordsAdapter,
)
from apps.ads_api.adapters.amazon_ads.sponsored_products.targets_adapter import (
    TargetsAdapter,
)
from apps.ads_api.constants import DEFAULT_BID, BiddingStrategies
from apps.ads_api.entities.amazon_ads.sponsored_products.ad_group import AdGroupEntity
from apps.ads_api.entities.amazon_ads.sponsored_products.campaign import CampaignEntity
from apps.ads_api.entities.amazon_ads.sponsored_products.product_ad import (
    ProductAdEntity,
)
from apps.ads_api.exceptions.ads_api.base import ObjectNotCreatedError
from apps.ads_api.models import Book, CampaignPurpose
from apps.ads_api.services.ad_groups.sync_create_service import SyncCreateAdGroupService
from apps.ads_api.services.campaigns.build_campaign_entity_service import (
    BuildCampaignEntityService,
)
from apps.ads_api.services.campaigns.sync_create_service import (
    SyncCreateCampaignService,
)
from apps.ads_api.services.keywords.cleaner_service import KeywordsCleanerService
from apps.ads_api.services.product_ads.sync_create_product_ads import (
    SyncCreateProductAdsService,
)

_logger = logging.getLogger(__name__)


class BaseCampaign:
    def __init__(self, book: Book):
        self._created_campaigns = None
        self.book = book

    def create_campaign(self, campaign: CampaignEntity) -> CampaignEntity:
        sync_create_service = SyncCreateCampaignService(self.book)
        return sync_create_service.create_campaign(campaign)

    def create_ad_group_for_campaign(
        self, campaign: CampaignEntity, bid: float = DEFAULT_BID
    ) -> AdGroupEntity:
        sync_create_service = SyncCreateAdGroupService(self.book)
        return sync_create_service.create_ad_group(campaign, bid)

    def create_product_ad_for_ad_group(self, ad_group: AdGroupEntity, book) -> ProductAdEntity:
        sync_create_service = SyncCreateProductAdsService(self.book if book is None else book)
        return sync_create_service.create_product_ad(ad_group)

    def create_keywords(self, keywords: list[dict]):
        """
        Creates keywords for the given book profile on Amazon Ads.

        Args:
            keywords (list): A list of keyword dicts to be created.

        Returns:
            tuple: A tuple containing a keywords ids, and a dict of any errors that occurred during creation.

        Raises:
            KeywordNotCreatedError: If any of the keywords could not be created on Amazon Ads side.
        """
        keywords_adapter = KeywordsAdapter(self.book.profile)
        _logger.info("Keywords to create(%s), %s", len(keywords), keywords)
        created, errors = keywords_adapter.batch_create(keywords)
        _logger.info("Created keywords(%s) %s", len(created), created)

        # refreshed_keywords: list[KeywordEntity] = keywords_adapter.list(
        #     KeywordSearchFilter(keyword_id_filter=IdFilter(include=created))
        # )

        # KeywordsRepository.save_keywords_from_amazon(refreshed_keywords, keywords)

        if errors:
            _logger.info("External errors %s", errors)
            if "duplicateValueError" not in errors[0].values():
                raise ObjectNotCreatedError(errors)

    @staticmethod
    def clean_keywords(
        keywords: list[str], is_asins: Optional[bool] = False, singularize: Optional[bool] = True, marketplace: Optional[str] = "US"
    ):
        cleaner = KeywordsCleanerService(keywords)
        cleaned_keywords = cleaner.clean_keywords(is_asins=is_asins, singularize=singularize, marketplace=marketplace)
        return cleaned_keywords

    def create_targets(self, targets: list[dict]):
        targets_adapter = TargetsAdapter(self.book.profile)
        _, errors = targets_adapter.batch_create(targets)
        if errors:
            if (
                "duplicateValueError" not in errors[0].values()
                or "targetingClauseSetupError" not in errors[0].values()
            ):
                raise ObjectNotCreatedError(errors)

    def build_campaign_entity(
        self,
        campaign_purpose: CampaignPurpose,
        book: Book,
        bidding_strategy: BiddingStrategies,
        tos: Optional[int] = None,
        pp: Optional[int] = None,
    ) -> CampaignEntity:
        build_campaign_service = BuildCampaignEntityService(
            campaign_purpose=campaign_purpose,
            book=book,
            bidding_strategy=bidding_strategy,
            tos=tos,
            pp=pp,
            created_campaigns=self._created_campaigns,
        )
        return build_campaign_service.build()
