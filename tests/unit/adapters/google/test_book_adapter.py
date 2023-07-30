import datetime
import json
import logging

import mock
import pytest

from apps.ads_api.entities.google.books import SearchResult
from apps.ads_api.adapters.google.books_adapter import GoogleBooksAdapter
from apps.ads_api.exceptions.google_api.books_api import NoBookInfoRetrieved

_logger = logging.getLogger(__name__)


def test_entities_can_parse_response(google_books_api_response):
    search_result = SearchResult.parse_obj(json.loads(google_books_api_response.text))
    book_info = search_result.items[0].book_info
    _assert_book_info_with_expected(book_info)


@mock.patch(
    "apps.ads_api.services.google.google_request_service.GoogleRequestService.request"
)
def test_retrieve_book_service_returns_book_info(
        request_method_mock, google_books_api_response
):
    request_method_mock.return_value = google_books_api_response
    google_adapter = GoogleBooksAdapter()
    book_info = google_adapter.retrieve_book_info("asincode123")
    _assert_book_info_with_expected(book_info)


@mock.patch(
    "apps.ads_api.services.google.google_request_service.GoogleRequestService.request"
)
def test_retrieve_book_service_with_no_search_results(
        request_method_mock, response_with_no_results
):
    request_method_mock.return_value = response_with_no_results
    google_adapter = GoogleBooksAdapter()
    with pytest.raises(NoBookInfoRetrieved):
        google_adapter.retrieve_book_info("asincode123")


def _assert_book_info_with_expected(book_info):
    assert book_info.pages == 144
    assert book_info.title == "Campfire Stories for Kids Part II"
    assert book_info.authors == [
        "Johnny Nelson",
    ]
    assert book_info.publish_date == datetime.date(2020, 12, 20)
