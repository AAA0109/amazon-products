from pydantic import ValidationError

from apps.ads_api.entities.amazon_ads.books import BookCatalog
from apps.ads_api.interfaces.adapters.book_catalog_retrievable_interface import (
    BookCatalogRetrievableInterface,
)


class BookCatalogAdapter(BookCatalogRetrievableInterface):
    def __init__(self, entity_id: str, country_code: str):
        self.country_code = country_code
        self.entity_id = entity_id

    def retrieve_book_catalog(self) -> BookCatalog:
        from apps.ads_api.data_exchange import get_catalog
        book_catalog_response = get_catalog(
            entity_id=self.entity_id, country_code=self.country_code
        )
        try:
            catalog = BookCatalog(books=book_catalog_response)
        except ValidationError:
            catalog = []
        return catalog
