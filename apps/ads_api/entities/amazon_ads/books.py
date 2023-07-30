from typing import Optional, Iterator

from pydantic import BaseModel, Field, root_validator, validator

from apps.ads_api.constants import BOOK_FORMATS_MAP


class BookInfo(BaseModel):
    asin: str
    title: str = Field(alias="name")
    reviews: int = Field(alias="customerReview")
    price: float = Field(alias="prices")
    book_format: str = Field(alias="bookBindingInformation")
    eligible: bool = Field(alias="eligibilityStatus", default=False)

    @root_validator(pre=True)
    def extract_reviews(cls, v):
        try:
            v["customerReview"] = v["customerReview"]["reviewCount"]["value"]
        except KeyError:
            v["customerReview"] = 0
        return v

    @root_validator(pre=True)
    def extract_eligible_status(cls, v):
        try:
            v["eligibilityStatus"] = bool(v["eligibilityStatus"] == "ELIGIBLE")
        except KeyError:
            v["eligibilityStatus"] = False
        return v

    @root_validator(pre=True)
    def extract_price(cls, v):
        amazon_price = 0
        for price in v.get("prices", []):
            if price["max"] > amazon_price:
                amazon_price = price["max"]
        v["prices"] = amazon_price
        return v

    @validator("book_format")
    def map_book_format(cls, v):
        if v in BOOK_FORMATS_MAP.keys():
            v = BOOK_FORMATS_MAP[v]
        elif "Kindle" in v:
            v = "Kindle"
        return v


class BookCatalog(BaseModel):
    books: list[BookInfo]

    @validator("books")
    def skip_books_with_0_price(cls, books: list[BookInfo]):
        validated_books = []
        for book in books:
            if book.price != 0:
                validated_books.append(book)
        return validated_books

    @validator("books")
    def skip_books_with_blank_tittle(cls, books: list[BookInfo]):
        validated_books = []
        for book in books:
            if book.title != "":
                validated_books.append(book)
        return validated_books

    def __len__(self):
        return len(self.books)

    def __getitem__(self, item) -> BookInfo:
        return self.books[item]

    def __iter__(self) -> Iterator[BookInfo]:
        return iter(self.books)
