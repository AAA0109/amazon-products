import datetime

import pytest

from apps.ads_api.repositories.book.book_repository import BookRepository
from apps.ads_api.repositories.book.price_repository import BookPriceRepository


@pytest.mark.django_db
def test_update_from_dict(book):
    BookRepository.update_from_dict(book, **{"title": "new test title"})
    book.refresh_from_db()
    assert book.title == "new test title"


@pytest.mark.django_db
def test_book_creates_with_default_price():
    book = BookRepository.create(
        **{
            "title": "test title",
            "asin": "testasin",
        }
    )
    book_price_repo = BookPriceRepository(book_id=book.id)

    assert 9.99 == book_price_repo.get_book_price_for_date(datetime.datetime.today())