import logging

from apps.ads_api.adapters.amazon_ads.sponsored_products.product_ad_adapter import (
    ProductAdAdapter,
)
from apps.ads_api.constants import TimeUnit
from apps.ads_api.entities.amazon_ads.sponsored_products.product_ad import (
    ProductAdEntity,
)
from apps.ads_api.entities.amazon_ads.sponsored_products.search_filters import (
    ProductAdSearchFilter,
)
from apps.ads_api.models import AdGroup, Campaign, ProductAd, Profile
from apps.utils.iso_to_epoch_converter import IsoToEpochConverter


_logger = logging.getLogger(__name__)


class SyncProductAdsService:
    def __init__(self, profile: Profile):
        self._profile = profile

    def sync(self):
        product_ad_adapter = ProductAdAdapter(self._profile)
        product_ads: list[ProductAdEntity] = product_ad_adapter.list(ProductAdSearchFilter())
        converter = IsoToEpochConverter()
        synced_count = 0

        campaign_ids: dict[int, int] = {
            campaign_id_amazon: id_
            for id_, campaign_id_amazon in Campaign.objects.filter(
                profile=self._profile,
                sponsoring_type="sponsoredProducts",
            ).values_list("id", "campaign_id_amazon")
        }
        ad_group_ids: dict[int, int] = {
            ad_group_id: id_
            for id_, ad_group_id in AdGroup.objects.filter(campaign__profile=self._profile).values_list(
                "id", "ad_group_id"
            )
        }

        for product_ad in product_ads:
            if not (
                int(product_ad.campaign_id)
                in campaign_ids.keys()
                and int(product_ad.ad_group_id) in ad_group_ids.keys()
            ):
                continue

            ProductAd.objects.update_or_create(
                campaign_id=campaign_ids[int(product_ad.campaign_id)],
                ad_group_id=ad_group_ids[int(product_ad.ad_group_id)],
                product_ad_id=int(product_ad.external_id),
                defaults={
                    "asin": self._get_asin(product_ad),
                    "state": product_ad.state,
                    "serving_status": product_ad.extended_data.serving_status,
                    "last_updated_date_on_amazon": converter.iso_to_epoch(
                        product_ad.extended_data.last_update_date_time,
                        convert_to=TimeUnit.MILLISECOND,
                    ),
                },
            )
            synced_count += 1
        _logger.info(f"Synced product ads for profile {self._profile} count: {synced_count}")

    @staticmethod
    def _get_asin(product_ad: ProductAdEntity):
        asin = ""
        if product_ad.asin is not None:
            asin = product_ad.asin
        elif product_ad.sku is not None:
            asin = product_ad.sku
        return asin
