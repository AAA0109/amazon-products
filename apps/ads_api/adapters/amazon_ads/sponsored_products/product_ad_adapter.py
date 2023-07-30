import logging
from typing import Type

from apps.ads_api.adapters.amazon_ads.sponsored_products.base_sp_adapter import BaseSponsoredProductsAdapter
from apps.ads_api.entities.amazon_ads.sponsored_products.product_ad import ProductAdEntity
from apps.utils.models import BaseModel

_logger = logging.getLogger(__name__)


class ProductAdAdapter(BaseSponsoredProductsAdapter):
    HEADERS: dict = {
        "Accept": "application/vnd.spProductAd.v3+json",
        "Content-Type": "application/vnd.spProductAd.v3+json",
    }
    URL: str = "/sp/productAds"
    ENTITY: Type[BaseModel] = ProductAdEntity
    RESPONSE_DATA_KEY = "productAds"
    RESPONSE_DATA_ID = "adId"
