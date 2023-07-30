import logging
from typing import Iterable, List

from django.db.models import QuerySet

from apps.ads_api.constants import AdStatus
from apps.ads_api.interfaces.repositories.campaign_repository_interface import (
    CampaignRepositoryInterface,
)
from apps.ads_api.models import Book, Campaign, ProductAd, Profile

_logger = logging.getLogger(__name__)


class CampaignRepository(CampaignRepositoryInterface):
    @classmethod
    def exists_by(cls, **kwargs) -> bool:
        return Campaign.objects.filter(**kwargs).exists()

    @classmethod
    def retrieve_by_kwargs(cls, **kwargs) -> QuerySet[Campaign]:
        return Campaign.objects.filter(**kwargs)

    @classmethod
    def create_from_dict(cls, **kwargs) -> Campaign:
        return Campaign.objects.create(**kwargs)

    @classmethod
    def add_books_for_campaign(cls, campaign: Campaign, books: Iterable[Book]) -> Campaign:
        for book in books:
            if book not in campaign.books.all():
                campaign.books.add(book)
        campaign.save()
        campaign.refresh_from_db()
        return campaign

    @classmethod
    def set_books_for_campaign(cls, campaign: Campaign, books_to_be_set: Iterable[Book]):
        already_related_books = campaign.books.all()
        for book in books_to_be_set:
            if book not in already_related_books:
                campaign.books.add(book)

        for book in already_related_books:
            if book not in books_to_be_set:
                campaign.books.remove(book)

        campaign.save()
        campaign.refresh_from_db()
        return campaign

    @classmethod
    def retrieve_related_books(cls, campaign: Campaign) -> QuerySet[Book]:
        return campaign.books.all()

    @classmethod
    def update_books_by_contained_product_ads_for_profiles(cls, profiles_ids: list[int]):
        BookCampaign = Book.campaigns.through
        for profile in (
            Profile.objects.filter(id__in=profiles_ids).prefetch_related("campaigns").iterator(chunk_size=20)
        ):
            book_campaign_to_create = []
            for campaign in profile.campaigns.filter(sponsoring_type="sponsoredProducts").prefetch_related(
                "books"
            ):
                campaign_books_asins = campaign.books.values_list("asin", flat=True)
                product_ad_asins = (
                    campaign.product_ads.filter(state__iexact=AdStatus.ENABLED)
                    .order_by("asin")
                    .distinct("asin")
                    .values_list("asin", flat=True)
                )
                books = profile.book_set.filter(asin__in=product_ad_asins)
                if set(campaign_books_asins) != set(product_ad_asins):
                    for book in books:
                        if book not in campaign.books.all():
                            book_campaign_to_create.append(BookCampaign(book=book, campaign=campaign))

                    for book in campaign.books.all():
                        if book not in books:
                            campaign.books.remove(book)

                    campaign.asins = list(product_ad_asins)
                    campaign.save()

            BookCampaign.objects.bulk_create(book_campaign_to_create, ignore_conflicts=True)
            book_campaign_to_create.clear()

    @classmethod
    def save(cls, campaign: Campaign) -> None:
        campaign.save()

    @classmethod
    def set_product_ads_for_campaign(cls, campaign: Campaign, product_ads: Iterable[ProductAd]):
        product_ads_ids = [product_ad.id for product_ad in product_ads]
        product_ads = ProductAd.objects.filter(id__in=product_ads_ids)
        product_ads.update(campaign=campaign)

    @classmethod
    def set_managed_false_for_profiles(cls, profile_pks: List[int]):
        Campaign.objects.filter(managed=True, profile__id__in=profile_pks).update(managed=False)
