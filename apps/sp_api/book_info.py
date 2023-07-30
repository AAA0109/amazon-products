print("Entered Book Info")

import decimal
import logging
import time
from typing import Optional

from django.db.models import Q

from apps.ads_api.constants import (
    BOOK_ROYALTY_RATE,
    DEFAULT_BE_ACOS,
    DEFAULT_BOOK_LENGTH,
    EU_VAT_PERCENTAGES,
    KDP_HIGHER_ROYALTY,
    KDP_LOWER_ROYALTY,
    MAX_SHORT_BOOK_LENGTH,
    MIN_BE_ACOS,
    RATES,
)
from apps.ads_api.models import Book, Profile
from apps.sp_api.rapidapi import RapidAPI
from apps.sp_api.settings import LOG_LEVEL

logging.basicConfig(level=LOG_LEVEL)
_logger = logging.getLogger(__name__)


def get_rapid_book_details():
    rapid_api = RapidAPI()
    rapidapi_book_details = rapid_api.get_book_details(book_asin="1507212305", marketplace="CA")
    bool(rapidapi_book_details)


# get info for book break even ACOS calc
def fill_out_book_info(profile: Optional[Profile] = None, force: Optional[bool] = False):
    """Queries the Amazon SP API to get book info"""

    if profile and force == True:
        book_filter = Book.objects.filter(profile=profile, in_catalog=True)
    elif profile and force == False:
        book_filter = Book.objects.filter(
            Q(reviews__isnull=True) | Q(reviews=0) | Q(title=""), profile=profile
        )
    elif profile == None and force == True:
        book_filter = Book.objects.all()
    else:
        book_filter = Book.objects.filter(in_catalog=True, pages=DEFAULT_BOOK_LENGTH).exclude(
            format="Kindle"
        )  # be_acos=DEFAULT_BE_ACOS

    books_per_marketplace = {
        marketplace: book_filter.filter(profile__country_code=marketplace)
        for marketplace in ["US", "CA", "UK"]
        if book_filter.filter(profile__country_code=marketplace).exists()
    }

    if len(books_per_marketplace) == 0:
        return
    rapid_api = RapidAPI()

    for marketplace, books in books_per_marketplace.items():
        # catalog_api = CatalogAPI(marketplace=Marketplaces[marketplace.label])  # type: ignore
        if marketplace == "UK":
            marketplace = "GB"
        for book in books:
            # book_details = rapid_api.get_book_details(book_asin=book.asin, marketplace=marketplace)
            book_length = rapid_api.get_book_length(book_asin=book.asin, marketplace=marketplace)
            # TODO: ensure error handling is adequate
            if not book_length:
                continue
            be_acos = _get_be_acos(book=book, book_length=book_length, country=book.profile.country_code)
            # book.price = (
            #     decimal.Decimal(book_details.price) if book_details.price else decimal.Decimal(DEFAULT_BOOK_PRICE)
            # )
            book.pages = book_length
            book.be_acos = decimal.Decimal(be_acos)
            # book.title = book_details.title
            # book.author = book_details.author
            # book.format = book_details.book_format
            # book.reviews = book_details.reviews
            # book.current_bsr = book_details.sales_rank
            book.save()
            time.sleep(1)


def _get_be_acos(book: Book, book_length: int, country: str) -> float:
    """Calculates Break Even ACOS from Book Details received from Amazon SP API"""
    if book.price is not None and book_length is not None:
        book_price = float(book.price)
        pages = float(book_length)
        # bsr = float(book.sales_rank)
    else:
        _logger.error(
            "Book price or length not received from Amazon SP API for asin: %s, setting default Break Even ACOS of %s",
            book.asin,
            DEFAULT_BE_ACOS,
        )
        return DEFAULT_BE_ACOS
    if book_price > 0 and pages > 0:
        book_format = book.format if book.format else "Paperback"
        royalty = _calculate_royalty(
            country=country, book_format=book_format, pages=pages, book_price=book_price
        )
    else:
        _logger.error(
            "Error in book price or length number for asin: %s, setting default Break Even ACOS of %s",
            book.asin,
            DEFAULT_BE_ACOS,
        )
        return DEFAULT_BE_ACOS
    be_acos = royalty / book_price
    if be_acos < MIN_BE_ACOS:
        be_acos = MIN_BE_ACOS
    return be_acos


def _calculate_royalty(
    country: str,
    book_format: str,
    pages: float,
    book_price: float,
    colour: str = "Black",
    trim: str = "Regular",
) -> float:
    """Calculates the royalty per book"""
    # Royalty = 70% Royalty Rate x (List Price – applicable VAT - Delivery Costs)
    book_length = "Long"
    if pages < MAX_SHORT_BOOK_LENGTH:
        book_length = "Short"
    vat = 0.0
    if country in EU_VAT_PERCENTAGES.keys():
        vat = EU_VAT_PERCENTAGES[country]
    kindle_format = "Kindle"
    if book_format not in RATES.keys() or book_format == kindle_format:
        if book_price >= RATES[kindle_format]["higher_royalty_threshold"][country]:  # type: ignore
            royalty = KDP_HIGHER_ROYALTY * ((1 - vat) * book_price - 3 * RATES[kindle_format]["Delivery"][country])  # type: ignore
            return royalty
        else:
            royalty = KDP_LOWER_ROYALTY * ((1 - vat) * book_price)
            return royalty
    printing_per_page = 0
    if book_length == "Long":
        printing_per_page = RATES[book_format][colour][book_length][trim]["Per_Page"][country]  # type: ignore
    printing_fixed = RATES[book_format][colour][book_length][trim]["Fixed"][country]  # type: ignore
    # royalty = (Royalty rate x list price) – printing costs
    royalty = BOOK_ROYALTY_RATE * (1 - vat) * book_price - (printing_fixed + pages * printing_per_page)
    return royalty


def get_new_releases(keyword: str, region: str):
    """Convenience connection function to get new releases using Parazun"""
    rapid_api = RapidAPI()
    new_releases = rapid_api.get_new_releases(keyword=keyword, region=region)
    return new_releases
