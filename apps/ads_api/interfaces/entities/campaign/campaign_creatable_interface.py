import abc

from apps.ads_api.entities.amazon_ads.sponsored_products.ad_group import AdGroupEntity
from apps.ads_api.entities.amazon_ads.sponsored_products.campaign import CampaignEntity
from apps.ads_api.entities.amazon_ads.sponsored_products.product_ad import ProductAdEntity


class CampaignCreatableInterface(abc.ABC):
    @abc.abstractmethod
    def create(self) -> list[tuple[CampaignEntity, AdGroupEntity, ProductAdEntity]]:
        pass
