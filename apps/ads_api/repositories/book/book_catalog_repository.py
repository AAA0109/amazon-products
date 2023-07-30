from datetime import datetime
from decimal import Decimal

from apps.ads_api.entities.amazon_ads.books import BookCatalog
from apps.ads_api.models import Profile, Book
from apps.ads_api.repositories.book.price_repository import BookPriceRepository


class BookCatalogRepository:
    def __init__(self, book_profile: Profile, book_catalog: BookCatalog):
        self._book_catalog = book_catalog
        self._book_profile = book_profile

    def save_books_to_profile(self):
        for book_from_catalog in self._book_catalog:
            book, created = Book.objects.update_or_create(
                profile=self._book_profile,
                asin=book_from_catalog.asin,
                defaults={
                    "title": book_from_catalog.title,
                    "format": book_from_catalog.book_format,
                    "price": Decimal(book_from_catalog.price),
                    "reviews": book_from_catalog.reviews,
                    "in_catalog": True,
                    "eligible": book_from_catalog.eligible,
                },
            )

            book_price_repo = BookPriceRepository(book.id)
            if created:
                book_price_repo.set_book_price_for_date(
                    for_date=datetime.today(), price=book_from_catalog.price
                )
            elif book_price_repo.get_actual_price() != book_from_catalog.price:
                book_price_repo.set_book_price_for_date(
                    for_date=datetime.today(), price=book_from_catalog.price
                )
