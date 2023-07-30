import logging
from datetime import datetime

from django.db import IntegrityError

from apps.ads_api.models import Book
from apps.ads_api.repositories.book.price_repository import BookPriceRepository

_logger = logging.getLogger(__name__)


class PriceTransfererService:
    """
    Transfare old price field into DateBookPriceModel
    """

    @staticmethod
    def transfer():
        today = datetime.today()
        books_proccessed = 0
        _logger.info("Transfer is started")
        for book in Book.objects.iterator():
            book_price_repo = BookPriceRepository(book.id)
            try:
                try:
                    actual_price = book_price_repo.get_actual_price()
                except AttributeError:
                    book_price_repo.set_book_price_for_date(today, book.price)
                else:
                    if book.price != actual_price:
                        book_price_repo.set_book_price_for_date(today, book.price)
            except IntegrityError:
                pass
            books_proccessed += 1

            if books_proccessed % 1000 == 0:
                _logger.info("Books have proccessed - %s", books_proccessed)

        _logger.info("Books have proccessed - %s", books_proccessed)
        _logger.info("Transfer is complete")
