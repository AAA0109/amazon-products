import logging
from typing import List, Optional

from apps.ads_api.adapters.amazon_ads.account_adapter import AccountAdapter
from apps.ads_api.constants import ServerLocation
from apps.ads_api.repositories.profile_repository import ProfileRepository

_logger = logging.getLogger(__name__)


def log_accessible_profiles_count(func):
    def wrapper(*args, **kwargs):
        _logger.info(
            "%s profiles accessible at start of profiles sync.",
            ProfileRepository.accessible_profiles_count(),
        )

        result = func(*args, **kwargs)

        _logger.info(
            "%s profiles accessible at end of profiles sync.",
            ProfileRepository.accessible_profiles_count(),
        )
        return result

    return wrapper


class SyncProfilesService:
    def __init__(self, server_location: Optional[List[ServerLocation]] = None):
        self.server_location = server_location if server_location else ServerLocation
        self._profile_repository = ProfileRepository()
        self._created_profiles: list[int] = []

    @log_accessible_profiles_count
    def sync(self) -> list[int]:
        """
        Syncs accessible profiles status with Amazon, creating new profiles if necessary
        Returns list of ids of created profiles (optionally)
        """
        for location_string in self.server_location:
            account_adapter = AccountAdapter(location_string)
            profiles = account_adapter.get_all_profiles()

            for profile in profiles:
                (
                    pk,
                    created,
                ) = self._profile_repository.update_or_create_from_profile(profile)
                if created:
                    self._created_profiles.append(pk)

            self._profile_repository.sync_profiles_status(profiles.ids, location_string)

        if self._created_profiles:
            _logger.info("New profiles ids: %s", self._created_profiles)

        return self._created_profiles
