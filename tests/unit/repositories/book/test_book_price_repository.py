import datetime

import pytest

from apps.ads_api.models import DateBookPrice
from apps.ads_api.repositories.book.price_repository import BookPriceRepository


@pytest.mark.django_db
def test_set_price_creates_date_book_price_row(book):
    book_price_repo = BookPriceRepository(book_id=book.id)
    date = datetime.datetime(2023, 2, 3)
    book_price_repo.set_book_price_for_date(for_date=date, price=10.5)
    price_updated = book_price_repo.get_book_price_for_date(for_date=date)
    assert price_updated == 10.5


@pytest.mark.django_db
def test_get_book_price_returns_actual_price_correctly(book):
    book_price_repo = BookPriceRepository(book_id=book.id)
    book_price_repo.set_book_price_for_date(
        for_date=datetime.datetime(2023, 1, 15), price=10.0
    )
    book_price_repo.set_book_price_for_date(
        for_date=datetime.datetime(2023, 1, 18), price=15.0
    )
    book_price_repo.set_book_price_for_date(
        for_date=datetime.datetime(2023, 1, 20), price=17.0
    )

    price_for_16s = book_price_repo.get_book_price_for_date(
        for_date=datetime.datetime(2023, 1, 16)
    )
    assert price_for_16s == 10.0

    price_for_18s = book_price_repo.get_book_price_for_date(
        for_date=datetime.datetime(2023, 1, 18)
    )
    assert price_for_18s == 15.0


@pytest.mark.django_db
def test_actual_book_price_is_correct_if_today_updated(book):
    book_price_repo = BookPriceRepository(book_id=book.id)
    book_price_repo.set_book_price_for_date(
        for_date=datetime.datetime.today(), price=10.0
    )
    actual_price = book_price_repo.get_actual_price()
    assert actual_price == 10.0


@pytest.mark.django_db
def test_actual_book_price_is_correct_if_yesterday_updated(book):
    # deleting default book price
    DateBookPrice.objects.filter(book__pk=book.id, date=datetime.datetime.today(), price=9.99).delete()

    book_price_repo = BookPriceRepository(book_id=book.id)
    book_price_repo.set_book_price_for_date(
        for_date=datetime.datetime.today() - datetime.timedelta(days=1), price=10.0
    )

    actual_price = book_price_repo.get_actual_price()

    assert actual_price == 10.0


@pytest.mark.django_db
def test_set_book_price_updates_price_correctly(book):
    book_price_repo = BookPriceRepository(book_id=book.id)
    today_date = datetime.datetime.today()

    book_price_repo.set_book_price_for_date(for_date=today_date, price=15.99)

    assert 15.99 == book_price_repo.get_book_price_for_date(datetime.datetime.today())
