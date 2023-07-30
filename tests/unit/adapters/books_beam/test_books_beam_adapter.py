from datetime import datetime

import pytest
import requests
from mock.mock import MagicMock
from requests import HTTPError

from apps.ads_api.authenticators.booksbeam_authenticator import BooksbeamAuthenticator
from apps.ads_api.entities.books_beam.books import Book
from pydantic import parse_obj_as

from apps.ads_api.exceptions.auth.token import AuthFailed


@pytest.fixture(scope="module")
def books_beam_sample_response():
    return [
        {
            "asin": "1953555446",
            "marketplaceId": 1,
            "author": "Connect, E2M Chef",
            "title": "Eager 2 Cook, Healthy Recipes for Healthy Living: Seafood & Salads",
            "imageUrl": "https://m.media-amazon.com/images/I/517VhFPSh2L.jpg,61Kj97T0t8L.jpg",
            "type": "PAPERBACK",
            "rating": 4.4,
            "numberOfPages": 146,
            "reviewsQuantity": 13,
            "bestsellerRank": 174,
            "price": 35.0,
            "monthlyRoyalty": 112273,
            "dailyRoyalty": 7341,
            "numOfLastReviews": 3,
            "publicationDate": 1677369600000,
            "acquisitionStatus": "SUCCESS"
        },
        {
            "asin": "1943451524",
            "marketplaceId": 1,
            "author": "Stephanie Middleberg MS RD CDN",
            "title": "The Big Book of Organic Baby Food: Baby Purées, Finger Foods, and Toddler Meals For Every Stage",
            "imageUrl": "https://m.media-amazon.com/images/I/8159zkXT-lL._AC_UY218_.jpg",
            "type": "PAPERBACK",
            "rating": 4.7,
            "numberOfPages": 296,
            "reviewsQuantity": 12523,
            "bestsellerRank": 511,
            "price": 14.49,
            "monthlyRoyalty": 28298,
            "dailyRoyalty": 999,
            "numOfLastReviews": 4,
            "publicationDate": 1476748800000,
            "acquisitionStatus": "SUCCESS"
        },
        {
            "asin": "1940352649",
            "marketplaceId": 1,
            "author": "America",
            "title": "The Complete Mediterranean Cookbook: 500 Vibrant, Kitchen-Tested Recipes for Living and Eating Well Every Day (The Complete ATK Cookbook Series)",
            "imageUrl": "https://m.media-amazon.com/images/I/61PTr4ZT0nL._SX258_BO1,204,203,200_.jpg",
            "type": "PAPERBACK",
            "rating": 4.5,
            "numberOfPages": 440,
            "reviewsQuantity": 17446,
            "bestsellerRank": 298,
            "price": 18.8,
            "monthlyRoyalty": 48094,
            "dailyRoyalty": 1642,
            "numOfLastReviews": 18,
            "publicationDate": 1482796800000,
            "acquisitionStatus": "SUCCESS"
        }
    ]


def test_parse_books_beem_response(books_beam_sample_response):
    books: list[Book] = parse_obj_as(list[Book], books_beam_sample_response)
    assert len(books) == 3
    assert books[0].asin == "1953555446"
    assert books[0].price == 35.0
    assert books[0].publication_date == datetime(2023, 2, 26).date()
    assert books[0].pages == 146


def test_auth_success(monkeypatch):
    expected_access_token = "access_token"
    expected_refresh_token = "refresh_token"
    mock_response = {
        "accessToken": expected_access_token,
        "refreshToken": expected_refresh_token,
    }
    mock_post = MagicMock(return_value=MagicMock(json=lambda: mock_response))
    monkeypatch.setattr(requests, "post", mock_post)

    actual_result = BooksbeamAuthenticator._auth()
    assert actual_result[0] == expected_access_token
    assert actual_result[1] == expected_refresh_token


def test_auth_failure(monkeypatch):
    raise_for_status_mock = MagicMock()
    raise_for_status_mock.raise_for_status = MagicMock(side_effect=HTTPError("401 Client Error: Unauthorized"))
    mock_post = MagicMock(return_value=raise_for_status_mock)
    monkeypatch.setattr(requests, "post", mock_post)

    with pytest.raises(AuthFailed):
        BooksbeamAuthenticator._auth()
