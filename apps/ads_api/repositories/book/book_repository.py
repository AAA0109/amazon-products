import datetime
import logging
from typing import Iterable, List

from django.db.models import QuerySet, Q, Count, Case, When

from apps.ads_api.constants import DEFAULT_BOOK_PRICE, CAMPAIGN_VALID_STATUSES
from apps.ads_api.models import Book, Profile
from apps.ads_api.repositories.book.price_repository import BookPriceRepository
from apps.ads_api.repositories.campaign_repository import CampaignRepository
from apps.ads_api.repositories.profile_repository import ProfileRepository


_logger = logging.getLogger(__name__)


class BookRepository:
    model = Book
    profile_repository = ProfileRepository()
    campaign_repository = CampaignRepository()

    @classmethod
    def update_books_eligibility_for_profiles(
        cls, profiles: QuerySet
    ) -> tuple[int, int]:
        """Update books eligibility for profiles and return eligible and ineligible books count."""
        from apps.ads_api.data_exchange import get_catalog

        eligible_count = 0
        ineligible_count = 0

        for profile in profiles:
            try:
                books_on_amazon = get_catalog(
                    entity_id=profile.entity_id, country_code=profile.country_code
                )
            except ConnectionError:
                _logger.warning("Failed to get catalog for profile %s", profile)
                continue

            if books_on_amazon is None:
                continue
            for book in books_on_amazon:
                asin = book.get("asin")
                eligibility_status = book.get("eligibilityStatus")
                eligible = Book.get_eligibility(eligibility_status)

                if eligible:
                    eligible_count += 1
                else:
                    ineligible_count += 1

                Book.objects.filter(asin=asin, profile=profile).update(
                    eligible=eligible
                )

        return eligible_count, ineligible_count

    @classmethod
    def get_managed_books_with_default_pages_count(cls) -> QuerySet[Book]:
        return Book.objects.filter(managed=True, pages=150)

    @classmethod
    def update_from_dict(cls, book: Book, **kwargs) -> Book:
        for field, value in kwargs.items():
            setattr(book, field, value)
        book.save()
        return book

    @classmethod
    def batch_update_from_kwargs(cls, books: Iterable[Book], **kwargs):
        books = Book.objects.filter(id__in=[book.id for book in books])
        books.update(**kwargs)

    @classmethod
    def create(cls, **kwargs) -> Book:
        book = Book.objects.create(**kwargs)
        book_price_repo = BookPriceRepository(book_id=book.id)
        book_price_repo.set_book_price_for_date(
            for_date=datetime.datetime.today(), price=DEFAULT_BOOK_PRICE
        )
        return book

    @classmethod
    def get_books_to_be_managed(cls) -> QuerySet[Book]:
        books = (
            Book.objects.annotate(
                running_campaigns_count=Count(
                    Case(
                        When(
                            campaigns__serving_status__in=CAMPAIGN_VALID_STATUSES,
                            then=1,
                        )
                    )
                )
            )
            .filter(
                Q(reviews__gt=5)
                and Q(eligible=True)
                and Q(profile__managed=True)
                and Q(running_campaigns_count__gt=3)
            )
            .exclude(Q(managed=True) and Q(title__exact=""))
        )
        return books

    @classmethod
    def retrieve_by_kwargs(cls, **kwargs) -> QuerySet[Book]:
        return Book.objects.filter(**kwargs)

    @classmethod
    def set_managed_false_for_profiles(cls, profile_pks: List[int]):
        Book.objects.filter(managed=True, profile__id__in=profile_pks).update(
            managed=False
        )
