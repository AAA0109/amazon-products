import logging

from apps.ads_api.repositories.book.book_repository import BookRepository
from apps.ads_api.repositories.profile_repository import ProfileRepository


_logger = logging.getLogger(__name__)


class UpdateBooksEligibilityService:
    def __init__(self):
        self.book_repository = BookRepository()
        self.profile_repository = ProfileRepository()

    def update(self) -> None:
        _logger.info("update_books_eligibility is started")
        profiles = self.profile_repository.get_managed_profiles()
        (
            eligible,
            ineligible,
        ) = self.book_repository.update_books_eligibility_for_profiles(profiles)
        _logger.info(
            "update_books_eligibility is finished. %s eligible books,"
            " %s ineligible books",
            eligible,
            ineligible,
        )
