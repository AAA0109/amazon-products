import pytest

from apps.ads_api.models import Book
from apps.ads_api.repositories.book.book_repository import BookRepository
from apps.utils.models import delete_dublicates_by_fields


@pytest.fixture
def create_books_with_dublicates():
    BookRepository.create(
            **{
                "title": "test title dublicated",
                "asin": "testasin dublicated",
            }
        )
    BookRepository.create(
            **{
                "title": "test title dublicated",
                "asin": "testasin dublicated",
            }
        )
    BookRepository.create(
            **{
                "title": "test title",
                "asin": "testasin",
            }
        )


@pytest.mark.django_db
def test_delete_dublicates_func_deletes_all_dublicates(create_books_with_dublicates):
    model = Book
    delete_dublicates_by_fields(model, "title", "asin")
    assert model.objects.count() == 2
