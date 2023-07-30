import logging
import time
from decimal import Decimal
from typing import List

from dateutil.parser import parse
from sp_api.api import CatalogItems
from sp_api.base import Marketplaces

from apps.ads_api.constants import (
    DEFAULT_BE_ACOS,
    DEFAULT_BE_ACOS_KINDLE,
    DEFAULT_BOOK_LENGTH,
    DEFAULT_BOOK_PRICE,
    DEFAULT_EBOOK_PRICE,
    REGIONS,
)
from apps.ads_api.models import Book, Profile
from apps.sp_api.credentials import credentials

_logger = logging.getLogger(__name__)


def get_server_location(country_code: str):
    """
    Returns the server location based on a given country code.

    This function iterates over a predefined global dictionary `REGIONS` which contains server
    locations as keys and a list of country codes as values. For a given country code, the function
    returns the corresponding server location. If the country code is not found, the function returns None.

    Parameters:
    country_code (str): The country code for which to find the server location.

    Returns:
    str: The server location if the country code is found in the `REGIONS` dictionary.
         If not found, None is returned.
    """
    for location, countries in REGIONS.items():
        if country_code in countries:
            return location
    return None


def add_custom_book_to_profile(asins: List[str], profile: Profile):
    """
    Adds custom book details to a given profile.

    For each provided ASIN (Amazon Standard Identification Number), the function fetches
    the book details from Amazon's Selling Partner API (SP-API). The book details include
    attributes such as title, publication date, author, format, price, be_acos, and pages.
    The function then adds or updates the fetched book details in the profile's book catalog.

    Parameters:
    asins (List[str]): List of ASINs for the books to be added to the profile.
    profile (Profile): The profile to which the books will be added.

    Notes:
    The function handles various book formats, including paperback and Kindle, and uses default
    values for price, be_acos and pages for certain formats when this information is not available
    from the SP-API. The function also handles potential missing format information and logs an error.
    The function enforces a 1 second delay between requests to the SP-API to respect rate limits.

    Raises:
    Exception: Any exceptions raised during the fetching of book details or addition to the catalog
    should be handled by the caller.
    """
    marketplace = Marketplaces[profile.country_code]
    server_credentials = credentials[get_server_location(profile.country_code)]
    catalog_items = CatalogItems(credentials=server_credentials, marketplace=marketplace)
    # take ASIN(s) and market parameters to find books details
    for asin in asins:
        book_details_response = catalog_items.get_catalog_item(
            asin=asin, includedData=["attributes,summaries"], marketplaceIds=marketplace.marketplace_id
        )
        # get individual book details from SP_API
        attributes = book_details_response.payload["attributes"]
        summaries = book_details_response.payload["summaries"][0]

        title = attributes["item_name"][0]["value"]
        publication_date = attributes["publication_date"][0]["value"]
        # publication_date e.g. "value": "2000-09-01T00:00:00.000Z",
        # convert publication_date to DateField
        publication_date = parse(publication_date).date()

        author = ""
        for contributor in summaries.get("contributors", []):
            if contributor["role"]["value"] == "author":
                author = str(contributor["value"]).strip()

        format = summaries.get("websiteDisplayGroupName")
        if format is None:
            format = attributes["binding"][0]["value"]  # default: paperback
        if format in ["Book", "paperback"]:
            format = "Paperback"
            price = attributes["list_price"][0].get("value_with_tax")
            if not price:
                price = attributes["list_price"][0].get("value", DEFAULT_BOOK_PRICE)
            be_acos = DEFAULT_BE_ACOS
            pages = attributes["pages"][0]["value"]
        elif format == "eBooks":
            format = "Kindle"
            price = DEFAULT_EBOOK_PRICE
            be_acos = DEFAULT_BE_ACOS_KINDLE
            pages = DEFAULT_BOOK_LENGTH
        else:
            _logger.error(
                "Book info not on SP API. ASIN: %s. Response: %s", asin, book_details_response.payload
            )

        time.sleep(1)

        # add books to Book catalog of profile
        Book.objects.update_or_create(
            profile=profile,
            asin=asin,
            defaults={
                "title": title,
                "publication_date": publication_date,
                "author": author,
                "format": format,
                "price": Decimal(price),
                "be_acos": Decimal(be_acos),
                "pages": pages,
            },
        )
