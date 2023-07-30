from apps.ads_api.models import Book


class BookValidator:
    def __init__(self, book: Book):
        self._book = book

    def is_valid(self) -> bool:
        return (
                self._book_is_not_none()
                and self._book_is_eligible()
                and self._asin_is_not_empty()
                and self._title_is_not_empty()
                and self._book_profile_is_accessible()
        )

    def _book_is_not_none(self):
        return bool(self._book)

    def _book_is_eligible(self) -> bool:
        return self._book.eligible

    def _asin_is_not_empty(self) -> bool:
        return len(self._book.asin) > 0

    def _title_is_not_empty(self) -> bool:
        return len(self._book.title) > 0

    def _book_profile_is_accessible(self) -> bool:
        return self._book.profile.accessible
