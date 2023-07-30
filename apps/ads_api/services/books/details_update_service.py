import logging
from time import sleep

from apps.ads_api.adapters.books_beam.books_adapter import BooksBeamAdapter
from apps.ads_api.adapters.google.books_adapter import GoogleBooksAdapter
from apps.ads_api.constants import BOOKS_BEAM_MARKETPLACES_IDS, DEFAULT_BOOK_LENGTH
from apps.ads_api.exceptions.books_beam.exceptions import (
    BaseBooksBeamException,
    BooksbeamServerError,
)
from apps.ads_api.exceptions.google_api.books_api import NoBookInfoRetrieved
from apps.ads_api.models import Book
from apps.ads_api.services.books.eligibility_service import BookElgibilityService

_logger = logging.getLogger(__name__)


class BooksDetailsService:
    def __init__(self, books_ids: list[int] = None):
        self._books_ids = books_ids

    def update_books_details(self):
        """Gets book page numbers from Amazon by scraping pages using ScrapeStack"""
        books_updated_with_booksbeam = 0
        books_updated_with_googlebook = 0

        if self._books_ids:
            books = Book.objects.filter(id__in=self._books_ids)
        else:
            books = Book.objects.filter(
                in_catalog=True,
                pages_updated=False,
                profile__managed=True,
                eligible=True,
            )

        for book in books:
            book_eligibility = BookElgibilityService(book)
            book_eligibility.refresh()
            if not book.eligible:
                continue

            updated = self._update_with_books_beam(book)
            if updated:
                books_updated_with_booksbeam += 1

            if not updated:
                self._update_with_google_books(book)
                if updated:
                    books_updated_with_googlebook += 1
            else:
                book.pages = DEFAULT_BOOK_LENGTH - 1

            book.save()

        _logger.info(
            "Books updated with booksbeam count: %, googlebooks: %s",
            books_updated_with_booksbeam,
            books_updated_with_googlebook,
        )

    @staticmethod
    def _update_with_books_beam(book: Book) -> bool:
        books_beam_adapter = BooksBeamAdapter()
        updated = False
        asin = book.asin
        format = book.format
        country_code = book.profile.country_code
        unavailable_country_codes = ["AU"]

        if country_code not in unavailable_country_codes:
            try:
                marketplace_id = BOOKS_BEAM_MARKETPLACES_IDS[country_code]
            except KeyError as e:
                _logger.error(
                    "Unuvailable country code for booksbeam %s. %s", country_code, e
                )
            else:
                try:
                    beam_book = books_beam_adapter.get_book_info(
                        asin, marketplace_id, format
                    )
                except BooksbeamServerError:
                    sleep(60 * 10)
                except BaseBooksBeamException as e:
                    books_beam_adapter.stop_tracking(asin, marketplace_id)
                    _logger.info(
                        "Error to get details. Details: %s, %s. Error details: %s.",
                        asin,
                        marketplace_id,
                        e,
                    )
                else:
                    book.publication_date = beam_book.publication_date
                    book.pages = beam_book.pages
                    book.pages_updated = True
                    updated = True

        return updated

    @staticmethod
    def _update_with_google_books(book: Book) -> True:
        google_book_adapter = GoogleBooksAdapter()
        updated = True

        try:
            google_book_info = google_book_adapter.retrieve_book_info(book.asin)
        except NoBookInfoRetrieved:
            pass
        else:
            book.pages = google_book_info.pages
            book.publication_date = google_book_info.publish_date
            book.pages_updated = True
            updated = True

        return updated
