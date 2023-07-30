import logging
import requests
from requests.exceptions import RequestException
from typing import Dict, List, NamedTuple, Optional

from apps.ads_api.models import Book
from apps.sp_api import settings
from apps.sp_api.constants import BOOK_PRODUCT_CATEGORY_ID
from apps.sp_api.sp_models import BookDetails

_logger = logging.getLogger(__name__)


class BookFormat(NamedTuple):
    book_format: str
    num_pages: int


class RapidAPI:
    def __init__(self):
        self.rapidapi_key = settings.RAPIDAPI_KEY
        self.rapidapi_host = settings.RAPIDAPI_HOST

        if not self.rapidapi_key:
            raise Exception("RAPIDAPI_KEY not set")

        if not self.rapidapi_host:
            raise Exception("RAPIDAPI_HOST not set")

        self.rapidapi_api_baseurl = f"https://{self.rapidapi_host}"

    def _get_headers(self) -> Dict[str, str]:
        """Returns the headers for the requests to the RapidAPI"""
        headers = {
            "x-rapidapi-host": self.rapidapi_host,
            "x-rapidapi-key": self.rapidapi_key,
        }
        return headers

    def _get_endpoint_url(self, endpoint: str) -> str:
        """Get the endpoint url for the RapidAPI"""
        return f"{self.rapidapi_api_baseurl}{endpoint}/"

    def _get_book_format(self, extra_info: List):
        """Get the book format from the extra info"""

        for item in extra_info:
            if item["name"] in ["Paperback", "Hardcover"]:
                # Since the num pages comes as a string like "158 pages"
                # we have to split the value
                return (item["name"], int(item["value"].split(" ")[0]))

        return "", 0

    def get_book_details(self, book_asin: str, marketplace: str, search_term: str = "") -> Optional[BookDetails]:
        """Get the book details for a book from RapidAPI

        Params:
            asin (str): The Amazon Standard Identification Number (ASIN)
            search_term (str): The search term used to find the book
        """

        url = self._get_endpoint_url("/product")
        headers = self._get_headers()
        querystring = {"asin": book_asin, "region": marketplace}

        try:
            _logger.info("Getting book details for %s [%s] from RapidAPI", book_asin, marketplace)
            response = requests.request("GET", url, headers=headers, params=querystring)
            response.raise_for_status()
        except RequestException as err:
            _logger.error("Error requesting data from RapidAPI: %s", err)
            status_code = response.status_code  # type: ignore
            if status_code == 404:
                response_json = response.json()  # type:ignore
                server_message = response_json.get("message")
                if server_message == "Product with ASIN cannot be found.":
                    error_note = "Book not found on Amazon"
                    return _non_existent_book(title=error_note, asin=book_asin)
            elif status_code == 500:
                if response.text == "Internal Server Error":  # type:ignore
                    return _non_existent_book(title="", asin=book_asin)
                response_json = response.json()  # type:ignore
                server_message = response_json.get("message")
                if server_message == "Network Read Error. Please try again.":
                    error_note = "Check if book series"
                    return _non_existent_book(title=error_note, asin=book_asin)
            return None

        response_json = response.json()

        format, length = self._get_book_format(response_json.get("extra_info", []) or [])
        if format == "" and "Kindle" in response_json["subtitle"]:
            format = "Kindle Edition"
        author = response_json.get("author", "")
        price = response_json.get("price")
        reviews = response_json.get("reviews").get("num_ratings") if response_json.get("reviews") else 0

        book = BookDetails(
            title=response_json["title"],
            author=author.get("name") if author else None,
            book_format=format,
            ASIN=book_asin,
            publication_date=None,
            price=price.get("amount") if price else None,
            currency=price.get("currency") if price else None,
            sales_rank=None,
            category=None,
            reviews=reviews,
            length=length,
            search_term=search_term,
        )

        return book

    def get_book_length(self, book_asin: str, marketplace: str) -> Optional[int]:
        """Get the book length for a book from RapidAPI"""

        url = self._get_endpoint_url("/product")
        headers = self._get_headers()
        querystring = {"asin": book_asin, "region": marketplace}

        try:
            _logger.info("Getting book details for %s [%s] from RapidAPI", book_asin, marketplace)
            response = requests.request("GET", url, headers=headers, params=querystring)
            response.raise_for_status()
        except RequestException as err:
            _logger.error("Error requesting data from RapidAPI: %s", err)
            status_code = response.status_code  # type: ignore
            if status_code == 404:
                response_json = response.json()  # type:ignore
                server_message = response_json.get("message")
                if server_message == "Product with ASIN cannot be found.":
                    error_note = "Book not found on Amazon"
                    return 0
            elif status_code == 500:
                if response.text == "Internal Server Error":  # type:ignore
                    return 0
                response_json = response.json()  # type:ignore
                server_message = response_json.get("message")
                if server_message == "Network Read Error. Please try again.":
                    error_note = "Check if book series"
                    return 0
            return 0

        response_json = response.json()
        format, length = self._get_book_format(response_json.get("extra_info", []) or [])
        return length

    def get_new_releases_page(self, keyword: str, region: str, page: int):
        """Gets 1 page of new releases in the last 30 days from Parazun"""
        url = "https://parazun-amazon-data.p.rapidapi.com/search/"
        querystring = {
            "keywords": f"{keyword}",
            "region": f"{region}",
            "page": f"{str(page)}",
            "node_id": BOOK_PRODUCT_CATEGORY_ID,
            "books_new": "last-30-days",
        }
        headers = self._get_headers()
        try:
            response = requests.request("GET", url, headers=headers, params=querystring)
            response.raise_for_status()
        except RequestException as err:
            _logger.error("Error requesting new releases from RapidAPI: %s", err)
            return None, None
        response_json = response.json()
        results = response_json.get("results")
        pages = int(response_json.get("num_pages"))
        asins = []
        for book in results:
            format = book.get("variants")[0].get("label")
            asins.append(book.get("asin"))
        return asins, pages

    def get_new_releases(self, keyword: str, region: str):
        """Gets up to 10 pages of"""
        page_asins, pages = self.get_new_releases_page(keyword=keyword, region=region, page=1)
        if pages is None or page_asins is None:
            return
        if pages == 1 and len(page_asins) > 0:
            return page_asins
        max_pages = 10 if pages > 10 else pages
        _logger.info("Max pages found for keyword '%s': %s", keyword, max_pages)
        all_asins = []
        all_asins.extend(page_asins)
        for page in range(2, max_pages + 1):
            _logger.info("Searching for new releases on page: %s", str(page))
            page_asins, pages = self.get_new_releases_page(keyword=keyword, region=region, page=page)
            if page_asins is None:
                continue
            all_asins.extend(page_asins)
        if len(all_asins) > 0:
            _logger.info("Foung %s ASINs", len(all_asins))
            return all_asins
        else:
            return None


def _non_existent_book(title: str, asin: str) -> BookDetails:
    return BookDetails(
        title=title,
        author=None,
        book_format=None,
        ASIN=asin,
        publication_date=None,
        price=None,
        currency=None,
        sales_rank=None,
        category=None,
        reviews=None,
        length=0,
        search_term="",
    )
