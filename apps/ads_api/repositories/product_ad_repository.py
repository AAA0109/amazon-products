from django.db.models import QuerySet

from apps.ads_api.models import ProductAd


class ProductAdRepository:
    @classmethod
    def retrieve_by_kwargs(cls, **kwargs) -> QuerySet[ProductAd]:
        return ProductAd.objects.filter(**kwargs)

    @classmethod
    def retrieve_asins_from_product_ads(
        cls, product_ads: QuerySet[ProductAd]
    ) -> list[str]:
        return list(
            product_ads.order_by("asin").values_list("asin", flat=True).distinct("asin")
        )

    @classmethod
    def create_from_kwargs(cls, **kwargs):
        return ProductAd.objects.create(**kwargs)
