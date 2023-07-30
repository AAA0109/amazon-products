from datetime import date

from pydantic import BaseModel, Field


class BookInfo(BaseModel):
    pages: int = Field(alias="pageCount")
    title: str
    authors: list[str]
    publish_date: date = Field(alias="publishedDate")


class Book(BaseModel):
    id: str
    etag: str
    self_link: str = Field(alias="selfLink")
    book_info: BookInfo = Field(alias="volumeInfo")


class SearchResult(BaseModel):
    total_items: int = Field(alias="totalItems")
    items: list[Book]
