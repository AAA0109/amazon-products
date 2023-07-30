from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class Book(BaseModel):
    asin: Optional[str]
    price: Optional[float]
    pages: Optional[int] = Field(alias="numberOfPages")
    publication_date: Optional[date] = Field(alias="publicationDate")
    status: str = Field(alias="acquisitionStatus")
