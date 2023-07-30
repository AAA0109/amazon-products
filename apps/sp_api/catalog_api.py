import itertools
import logging
from sp_api.api import Catalog, CatalogItems
from sp_api.base import Marketplaces
from typing import Dict, List, Optional

from apps.ads_api.models import MarketplaceIdChoice
from apps.sp_api import settings
from apps.sp_api.constants import BOOK_DISPLAY_ON_WEBSITE, BOOK_PRODUCT_CATEGORY_ID
from apps.sp_api.sp_models import (
    BookDetails,
    BookItem,
    BookItemSummary,
    BookSearchResult,
)

_logger = logging.getLogger(__name__)


class CredentialsMixin:
    def __init__(self):
        self.credentials = dict(
            refresh_token=settings.SP_API_REFRESH_TOKEN_NA,
            lwa_app_id=settings.APP_ID,
            lwa_client_secret=settings.SP_API_CLIENT_SECRET,
            aws_access_key=settings.AWS_ACCESS_KEY,
            aws_secret_key=settings.AWS_SECRET_KEY,
            role_arn=settings.ROLE_ARN,
        )


class CatalogAPI(CredentialsMixin):
    PRODUCT_CATEGORY_ID_BOOK = "book_display_on_website"

    def __init__(self, marketplace: Marketplaces):
        super().__init__()
        self.catalog = Catalog(credentials=self.credentials, marketplace=marketplace)

    def _get_product_category(self, sales_rankings: Dict) -> Optional[str]:  # type: ignore
        """Get the category with the lowest rank.

        Params:
            sales_rankings (Dict): The sales rankings object of the book.
        """

        # Ignore the sales rank with category book
        sales_rankings_without_category_book = [
            sales_rank
            for sales_rank in sales_rankings
            if sales_rank["ProductCategoryId"] != self.PRODUCT_CATEGORY_ID_BOOK
        ]

        if sales_rankings_without_category_book:
            sales_rankings_without_category_book.sort(key=lambda rank: rank["Rank"])

            return sales_rankings_without_category_book[0]["ProductCategoryId"]

    def _get_best_sales_ranking(self, sales_rankings: Dict) -> Optional[int]:
        """Get the best sales rank for a book

        The best rank is the one with the category id book_display_on_website

        Params:
            sales_rankings (Dict): The sales rankings object of the book.
        """

        best_sales_ranking = None
        for sales_rank in sales_rankings:

            # We are interested on the book display on website category
            # to get the BSR
            if sales_rank["ProductCategoryId"] == BOOK_DISPLAY_ON_WEBSITE:
                return sales_rank["Rank"]

        return best_sales_ranking

    def _parse_book_details(self, book_details: Dict, search_term: str, asin: str) -> BookDetails:
        """Parses the book details we are interested in from the catalog API response.

        Params:
            book_details (Dict): The book details from the catalog API response.
        """

        attribute_sets = book_details.get("AttributeSets", [])

        if len(attribute_sets) == 0:
            _logger.error("Amazon returned an empty response for: %s", asin)
            return  # type: ignore

        # We'll keep the first set and ignore the rest
        attribute_set = attribute_sets[0]

        best_sales_rank = self._get_best_sales_ranking(book_details["SalesRankings"])
        product_category = self._get_product_category(book_details["SalesRankings"])

        book = BookDetails(
            title=attribute_set["Title"],
            author=",".join(attribute_set.get("Author", "")),
            book_format=attribute_set.get("Binding"),
            ASIN=book_details["Identifiers"]["MarketplaceASIN"]["ASIN"],
            publication_date=attribute_set.get("PublicationDate", ""),
            price=attribute_set.get("ListPrice", {}).get("Amount"),
            currency=attribute_set.get("ListPrice", {}).get("CurrencyCode", ""),
            sales_rank=best_sales_rank,
            category=product_category,
            reviews=0,
            length=attribute_set.get("NumberOfPages", 0),
            search_term=search_term,
            qualifies=False,
        )

        return book

    def get_book_details(
        self,
        book_asin: str,
        search_term: str,
        marketplace: Optional[str] = None,  # temporarily removed: MarketplaceIdChoice
    ) -> BookDetails:
        """Get details for a single book.

        Param:
            book_asin: The asin of the book to get details for.
        """

        _logger.info("Getting book details for: %s from Amazon API", book_asin)
        if marketplace:
            book_details_response = self.catalog.get_item(asin=book_asin, MarketplaceId=marketplace)
        else:
            book_details_response = self.catalog.get_item(asin=book_asin)
        book_details = self._parse_book_details(book_details_response.payload, search_term, asin=book_asin)

        return book_details


class CatalogItemsAPI(CredentialsMixin):

    RESULTS_PER_PAGE = 20
    PRODUCT_CATEGORY_NAME_BOOK = "Books"

    def __init__(self):
        super().__init__()

        self.catalog_items = CatalogItems(credentials=self.credentials)

    def _parse_book_search_summaries(self, summaries: Dict) -> List[BookItemSummary]:
        """Parse the book search summaries into a Book object.

        Param:
            book_search_result: The book search result to parse.
        """

        book_summaries = []
        for summary in summaries:
            book_summaries.append(
                BookItemSummary(
                    marketplace_id=summary["marketplaceId"],
                    brand_name=summary.get("brandName", ""),
                    item_name=summary["itemName"],
                    manufacturer=summary["manufacturer"] if "manufacturer" in summary else "",
                    browse_node_id=summary.get("browseNodeId", ""),
                )
            )

        return book_summaries

    def _parse_book_search_response(self, book_search_response: Dict) -> BookSearchResult:
        """Parse the book search result into a Book object.

        Param:
            book_search_result: The book search result to parse.
        """

        book_results = []
        for item in book_search_response.get("items", []):
            book_item = BookItem(
                asin=item.get("asin"),
                summaries=self._parse_book_search_summaries(item.get("summaries", [])),
            )
            book_results.append(book_item)

        return BookSearchResult(results=book_results)

    def search_books(self, search_term: str) -> BookSearchResult:
        """Search for books in the catalog.
        We are filtering by the books category
        and only returning the first 20 results.

        Param:
            search_term: The search term to use for the search.
        """

        # Amazon receives a string of comma separated words
        # https://github.com/saleweaver/python-amazon-sp-api/issues/178
        keywords = search_term.replace(" ", ",")

        # TODO: filter by paperback
        books_response = self.catalog_items.search_catalog_items(
            keywords=[keywords],
            classificationIds=[BOOK_PRODUCT_CATEGORY_ID],
            pageSize=self.RESULTS_PER_PAGE,
        )

        book_search_response = books_response.payload
        books_response = self._parse_book_search_response(book_search_response=book_search_response)

        return books_response

    def _get_product_category(self, sales_rankings: Dict) -> Optional[str]:  # type: ignore
        """Get the category with the lowest rank.

        Params:
            sales_rankings (Dict): The sales rankings object of the book.
        """
        flatten_ranks = list(itertools.chain(*[sales_rank["ranks"] for sales_rank in sales_rankings]))

        # Ignore the sales rank with category book
        sales_rankings_without_category_book = [
            sales_rank for sales_rank in flatten_ranks if sales_rank["title"] != self.PRODUCT_CATEGORY_NAME_BOOK
        ]

        if sales_rankings_without_category_book:
            sales_rankings_without_category_book.sort(key=lambda rank: rank["value"])

            return sales_rankings_without_category_book[0]["title"]

    def get_book_category(self, book_asin: str) -> Optional[str]:

        """Get details for a single book.

        Param:
            book_asin: The asin of the book to get details for.
        """
        _logger.info("Getting book cateogry for: %s from Amazon API", book_asin)
        book_details_response = self.catalog_items.get_catalog_item(
            asin=book_asin,
            includedData="salesRanks",
        )
        book_details = book_details_response.payload
        product_category = self._get_product_category(book_details["salesRanks"])

        return product_category
