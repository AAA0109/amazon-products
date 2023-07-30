import logging

from apps.ads_api.adapters.amazon_ads.sponsored_products.product_ad_adapter import (
    ProductAdAdapter,
)
from apps.ads_api.entities.amazon_ads.sponsored_products.ad_group import AdGroupEntity
from apps.ads_api.entities.amazon_ads.sponsored_products.product_ad import (
    ProductAdEntity,
)
from apps.ads_api.exceptions.ads_api.base import ObjectNotCreatedError
from apps.ads_api.exceptions.ads_api.product_ads import ProductAdIneligible
from apps.ads_api.models import Book

_logger = logging.getLogger(__name__)


class SyncCreateProductAdsService:
    def __init__(self, book: Book) -> None:
        self.book = book

    def create_product_ad(self, ad_group: AdGroupEntity) -> ProductAdEntity:
        """Create a product ad for the given ad group in the Amazon Advertising API.

        Args:
            ad_group (AdGroupEntity): A `AdGroupEntity` instance containing the details of the
                ad group for which to create a product ad.

        Returns:
            ProductAdEntity: A `ProductAdEntity` instance representing the created product ad.

        Raises:
            ProductAdIneligible: If the product is not eligible to be advertised in the given ad group.
                This exception is raised if the 'ObjectNotCreatedError' exception was raised with an
                'adEligibilityError'.

        """
        product_ad_adapter = ProductAdAdapter(self.book.profile)
        product_ad = ProductAdEntity(
            campaign_id=ad_group.campaign_id,
            ad_group_id=ad_group.external_id,
            asin=self.book.asin,
        )
        _logger.info(
            "Creating product ad for campaign %s, ad group %s.", ad_group.campaign_id, ad_group.external_id
        )

        try:
            product_ad.external_id = product_ad_adapter.create(
                product_ad.dict(by_alias=True, exclude_none=True)
            )
            _logger.info("Product with id %s ad created.", product_ad.external_id)
        except ObjectNotCreatedError as e:
            if "adEligibilityError" in e.errors[0].values():
                raise ProductAdIneligible(self.book.asin) from e

            _logger.warning("External errors: %s.", e.errors[0].values())

        return product_ad
