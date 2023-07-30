import logging

from apps.ads_api.adapters.amazon_ads.sponsored_products.ad_group_adapter import (
    AdGroupAdapter,
)
from apps.ads_api.adapters.amazon_ads.sponsored_products.campaigns_adapter import (
    CampaignAdapter,
)
from apps.ads_api.adapters.amazon_ads.sponsored_products.product_ad_adapter import (
    ProductAdAdapter,
)
from apps.ads_api.entities.amazon_ads.sponsored_products.search_filters import (
    AdGroupSearchFilter,
    CampaignSearchFilter,
    IdFilter,
    ProductAdSearchFilter,
)
from apps.ads_api.models import AdGroup, Campaign, ProductAd, Profile

_logger = logging.getLogger()


class SyncDeleteCampaignService:
    def __init__(self, profile: Profile):
        self._profile = profile

    def _sync_delete_campaigns(self, campaign_external_ids: list[int]):
        """
        Batch archive the given campaigns in the Amazon Advertising API and delete them from the database.

        Args:
            campaigns_external_ids (List[str]): A list of campaign external IDs to archive and delete.

        Returns:
            None

        """
        _logger.info("Delete campaigns ith external ids: [%s]", campaign_external_ids)
        campaign_adapter = CampaignAdapter(self._profile)

        campaigns_db = Campaign.objects.filter(campaign_id_amazon__in=campaign_external_ids)

        if campaign_external_ids:
            success, errors = campaign_adapter.delete(
                CampaignSearchFilter(campaign_id_filter=IdFilter(include=campaign_external_ids))
            )
            _logger.info("Campaigns updated: %s", success)
            _logger.error("Campaigns update errors: %s", errors)

        campaigns_deleted = campaigns_db.delete()

        _logger.info(
            "Campaigns deleted: %s, ad groups deleted: %s, product ads deleted: %s", campaigns_deleted
        )
