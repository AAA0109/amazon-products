import datetime
from datetime import date

from apps.ads_api.constants import DEFAULT_BOOK_PRICE
from apps.ads_api.interfaces.repositories.book.price_repository_interface import (
    BookPriceRepositoryInterface,
)
from apps.ads_api.models import DateBookPrice


class BookPriceRepository(BookPriceRepositoryInterface):
    def __init__(self, book_id):
        self._book_id = book_id

    def get_book_price_for_date(self, for_date) -> float:
        price = (
            DateBookPrice.objects.filter(book_id=self._book_id, date__lte=for_date)
            .order_by("-date")
            .first()
            .price
        )
        return float(price)

    def set_book_price_for_date(self, for_date: date, price: float):
        DateBookPrice.objects.update_or_create(
            book_id=self._book_id, date=for_date, defaults={"price": price}
        )

    def get_actual_price(self):
        date_book_price = (
            DateBookPrice.objects.filter(
                book_id=self._book_id, date__lte=datetime.datetime.today()
            )
            .order_by("-date")
            .first()
        )

        try:
            price = date_book_price.price
        except AttributeError:
            self.set_book_price_for_date(datetime.datetime.today(), DEFAULT_BOOK_PRICE)
            price = DEFAULT_BOOK_PRICE

        return float(price)
