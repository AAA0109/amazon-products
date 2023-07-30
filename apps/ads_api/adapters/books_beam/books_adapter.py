import logging
from time import sleep

from pydantic import ValidationError, parse_obj_as

from apps.ads_api.adapters.books_beam.base_books_beam_adapter import (
    BaseBooksBeamAdapter,
)
from apps.ads_api.entities.books_beam.books import Book
from apps.ads_api.exceptions.books_beam.exceptions import (
    BookAlreadyTracking,
    BooksbeamServerError,
    BookStillProcessing,
    ResponseValidationException,
)

_logger = logging.getLogger(__name__)


class BooksBeamAdapter(BaseBooksBeamAdapter):
    def get_book_info(self, asin, marketplace_id, format) -> Book:
        response = self.start_tracking(asin, marketplace_id, format)
        if response.status_code == 400:
            raise BookAlreadyTracking(
                f"The book {asin}, {marketplace_id} is already being tracked."
            )
        elif response.status_code == 500:
            raise BooksbeamServerError(
                f"Got bad response from server: {response.status_code} status code."
            )

        try:
            book = Book(**response.json())
        except ValidationError:
            _logger.error("Got error while parsing response %s.", response.json())
            raise ResponseValidationException(
                f"Got error while parsing response {response.json()}."
            )

        if book.status != "SUCCESS":
            raise BookStillProcessing(
                f"Book still processing. Details: {asin}, {marketplace_id}, book status is {book.status}."
            )

        self.stop_tracking(asin, marketplace_id)

        return book

    def start_tracking(self, asin: str, marketplace_id: int, format: str):
        url = "https://app.bookbeam.io/book-tracker-service/api/v1/tracking-books"
        format = "KINDLE" if format == "Kindle" else "PAPERBACK"
        sleep(5)

        data = {"asin": asin, "marketplaceId": marketplace_id, "type": format}

        return self.send_request(url=url, data=data, method="POST")

    def stop_tracking(self, asin: str, marketplace_id: int):
        url = f"https://app.bookbeam.io/book-tracker-service/api/v1/marketplaces/{marketplace_id}/tracking-books/{asin}"
        sleep(5)
        self.send_request(url=url, method="DELETE")

    def get_tracking(self) -> list[Book]:
        url = "https://app.bookbeam.io/book-tracker-service/api/v1/tracking-books"
        sleep(5)
        response = self.send_request(url=url)
        books = parse_obj_as(list[Book], response.json())
        return books
