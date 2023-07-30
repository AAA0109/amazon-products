from apps.ads_api.constants import BOOK_FORMATS_MAP
from apps.ads_api.entities.amazon_ads.books import BookInfo, BookCatalog


def test_single_book_can_be_parsed(single_book_response):
    book: BookInfo = BookInfo.parse_obj(single_book_response)

    assert book.reviews == 1726
    assert book.asin == "B0BK74FYBM"
    assert book.price == 9.99
    assert (
        book.title
        == "A Mark Of Imperfection: A Black Beacons Murder Mystery (DCI Evan Warlow Crime Thriller Book 6)"
    )
    assert book.book_format == "Kindle"
    assert book.eligible is True


def test_book_catalog_response_with_prices(book_catalog_response):
    book_catalog = BookCatalog(books=book_catalog_response)
    assert len(book_catalog) == 2
    assert book_catalog[0].asin == "B0BK74FYBM"

    for book in book_catalog:
        assert book.asin == "B0BK74FYBM"


def test_book_catalog_should_skip_books_with_no_prices(book_catalog_response):
    del book_catalog_response[0]["prices"]

    book_catalog = BookCatalog(books=book_catalog_response)
    assert len(book_catalog) == 0


def test_book_catalog_should_skip_books_with_blank_titles(book_catalog_response):
    book_catalog_response[0]["name"] = ""

    book_catalog = BookCatalog(books=book_catalog_response)
    assert len(book_catalog) == 0


def test_foreign_book_formats_map_correctly(single_book_response):
    for foreign_format, english_format in BOOK_FORMATS_MAP.items():
        single_book_response["bookBindingInformation"] = foreign_format
        book: BookInfo = BookInfo.parse_obj(single_book_response)
        assert book.book_format == english_format