from typing import List, Optional

from pydantic import BaseModel


class BookItemSummary(BaseModel):
    marketplace_id: str
    brand_name: str
    item_name: str
    manufacturer: str
    browse_node_id: Optional[str]


class BookItem(BaseModel):
    asin: str
    summaries: List[BookItemSummary]


class BookSearchResult(BaseModel):
    results: List[BookItem]


class BookDetails(BaseModel):
    title: str
    author: Optional[str]
    ASIN: str
    publication_date: Optional[str]
    book_format: Optional[str] = "Paperback"  # Could be Hardcover or other
    price: Optional[str]
    currency: Optional[str] = "USD"
    sales_rank: Optional[str] = ""
    reviews: Optional[int]
    length: Optional[int]
    category: Optional[str]
    search_term: Optional[str]
    qualifies: bool = False
