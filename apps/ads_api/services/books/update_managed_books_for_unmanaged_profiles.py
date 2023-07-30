from typing import List

from apps.ads_api.repositories.book.book_repository import BookRepository


class UpdateManagedBooksForUnmanagedProfilesService:
    @classmethod
    def update(cls, profile_pks: List[int]):
        BookRepository.set_managed_false_for_profiles(profile_pks)
