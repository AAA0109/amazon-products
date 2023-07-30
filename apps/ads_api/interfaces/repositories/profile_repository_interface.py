from abc import ABC, abstractmethod

from apps.ads_api.constants import ServerLocation
from apps.ads_api.entities.amazon_ads.profiles import ProfileEntity


class ProfileRepositoryInterface(ABC):
    @abstractmethod
    def accessible_profiles_count(self) -> int:
        pass

    @abstractmethod
    def sync_profiles_status(
        self, profile_ids_from_source: list[int], location_string: ServerLocation
    ):
        pass

    @abstractmethod
    def update_or_create_from_profile(self, profile: ProfileEntity):
        pass

    @abstractmethod
    def get_managed_profiles_ids(self) -> list[int]:
        pass

    @abstractmethod
    def get_server_by_profile_id(self, profile_id: int) -> str:
        pass
