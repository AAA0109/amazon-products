import json
import logging
from typing import Optional

from pydantic import ValidationError
from requests import Response

from apps.ads_api.entities.google.books import BookInfo, SearchResult
from apps.ads_api.exceptions.google_api.books_api import NoBookInfoRetrieved
from apps.ads_api.services.google.google_request_service import GoogleRequestService


_logger = logging.getLogger(__name__)


class GoogleBooksAdapter:
    def __init__(self):
        self.google_request_service = GoogleRequestService()
        self.base_url = "https://www.googleapis.com/books/v1/volumes"

    def retrieve_book_info(self, asin: str) -> Optional[BookInfo]:
        url = f"{self.base_url}?q={asin}"
        response = self.google_request_service.request(url=url)
        if not response:
            raise NoBookInfoRetrieved()
        try:
            book_info = self._parse_book_info_from_response(response)
        except ValidationError:
            raise NoBookInfoRetrieved()

        return book_info

    @staticmethod
    def _parse_book_info_from_response(response: Response):
        search_result = SearchResult.parse_obj(json.loads(response.text))
        return search_result.items[0].book_info
