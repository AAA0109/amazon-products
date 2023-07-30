import logging
from time import sleep
from typing import Union

from sp_api.api import Catalog
from sp_api.base import Marketplaces

from apps.ads_api.constants import ServerLocation
from apps.ads_api.models import Book
from apps.openai_api.suggesters.title_asins_suggester import (
    TitleAsinsSuggester,
)
from apps.sp_api.book_cache import cached_title
from apps.sp_api.book_search import BookSearch
from apps.sp_api.constants import MAX_BOOK_BSR_TRESHOLD, classificationIds
from apps.sp_api.credentials import credentials

_logger = logging.getLogger(__name__)


class ASINFinder:
    def __init__(self, server_location: Union[ServerLocation, str]):
        self.server_location = server_location

    def search_similar_books_asins(self, keywords: list[str], book: Book):
        marketplace = getattr(Marketplaces, book.profile.country_code)
        book_format = "Kindle" if book.format.lower() == "kindle" else "Books"
        classification_id = classificationIds[book.profile.country_code][book_format]
        _logger.info("Searching ASINs by given keywords %s", keywords)

        asins = BookSearch(self.server_location).search_books(
            keywords=keywords, classification_id=classification_id, marketplace=marketplace
        )
        _logger.info("ASINs collected %s", asins)

        book_title2asin_map = self._collect_book_titles(asins=asins, marketplace=marketplace)
        _logger.info("Book title2asin maps: %s", book_title2asin_map)

        filtered_asins = TitleAsinsSuggester.suggest_asins(
            book_title=book.title, title2asin_map=book_title2asin_map
        )
        _logger.info("Finally filtered asins %s", filtered_asins)

        return filtered_asins

    def _collect_book_titles(self, asins: list[str], marketplace: Marketplaces) -> dict[str, str]:
        book_title2asin_map = {}

        for asin in asins:
            book_title, bsr = self.retrieve_book_info(marketplace=marketplace, asin=asin)
            if bsr < MAX_BOOK_BSR_TRESHOLD:
                book_title2asin_map.update({book_title: asin})

        return book_title2asin_map

    @cached_title
    def retrieve_book_info(self, marketplace: Marketplaces, asin: str) -> tuple[str, float]:
        """Retrieve the title of a book given its ASIN and marketplace.

        Args:
            marketplace: An instance of the Marketplaces Enum representing the marketplace to search in.
            asin: A string representing the ASIN of the book to retrieve the title for.

        Returns:
            A string representing the title of the book.

        Raises:
            BookHasHighBSRException: If the book's Best Seller Rank (BSR) exceeds the optimal threshold.

        """
        book_details_response = Catalog(credentials=credentials[self.server_location], marketplace=marketplace).get_item(
            asin=asin, MarketplaceId=marketplace.marketplace_id
        )
        sleep(1)

        bsr = MAX_BOOK_BSR_TRESHOLD
        for rank in book_details_response.payload["SalesRankings"]:
            if rank["ProductCategoryId"] == "book_display_on_website":
                bsr = rank["Rank"]
                continue

        title = book_details_response.payload["AttributeSets"][0]["Title"]

        return title, bsr
