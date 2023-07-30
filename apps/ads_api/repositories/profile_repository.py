import logging
from typing import Union, Optional

from django.db.models import QuerySet

from apps.ads_api.constants import ServerLocation, REGIONS
from apps.ads_api.interfaces.repositories.profile_repository_interface import (
    ProfileRepositoryInterface,
)
from apps.ads_api.models import Profile
from apps.ads_api.entities.amazon_ads.profiles import ProfileEntity


_logger = logging.getLogger(__name__)


class ProfileRepository(ProfileRepositoryInterface):
    def get_server_by_profile_id(self, profile_id: int) -> Optional[ServerLocation]:
        try:
            profile_server = Profile.objects.get(profile_id=profile_id).profile_server
        except Profile.DoesNotExist:
            _logger.error("Profile with profile_id[%s] does not exist", profile_id)
        else:
            for server in REGIONS.keys():
                if profile_server == server:
                    return server

    @classmethod
    def accessible_profiles_count(cls):
        return Profile.objects.filter(accessible=True).count()

    @classmethod
    def sync_profiles_status(
        cls,
        profile_ids_from_source: list[int],
        location_string: Union[ServerLocation, str],
    ):
        """
        Update profiles that have not returned from adapter accessible_status to False
        """
        Profile.objects.filter(profile_server=location_string).exclude(
            profile_id__in=profile_ids_from_source,
        ).update(accessible=False, managed=False)

    def update_or_create_from_profile(self, profile: ProfileEntity) -> tuple[int, bool]:
        """
        Return a tuple (pk, created), where created is a boolean specifying whether an object was created.
        """
        obj, created = Profile.objects.update_or_create(
            profile_id=profile.profile_id,
            defaults={
                "profile_id": profile.profile_id,
                "country_code": profile.country_code,
                "marketplace_string_id": profile.account_info.marketplace_id,
                "entity_id": profile.account_info.id,
                "valid_payment_method": profile.account_info.valid_payment_method,
                "type": profile.account_info.type,
                "profile_server": self._resolve_server_location(profile.country_code),  # type: ignore
            },
        )
        return obj.pk, created

    @staticmethod
    def _resolve_server_location(country_code) -> str:
        for key in REGIONS:
            if country_code in REGIONS[key]:
                return key.value

    @classmethod
    def get_managed_profiles_ids(cls) -> list[int]:
        return list(
            Profile.objects.filter(managed=True).values_list("profile_id", flat=True)
        )

    @classmethod
    def get_managed_profiles(cls) -> QuerySet[Profile]:
        return Profile.objects.filter(managed=True)

    @classmethod
    def get_unmanaged_profiles_pks(cls) -> list[int]:
        return list(Profile.objects.filter(managed=False).values_list("id", flat=True))

    @classmethod
    def get_ordered_by(cls, *args) -> QuerySet[Profile]:
        return Profile.objects.order_by(*args)

    @classmethod
    def retrieve_profiles_by_ids(cls, ids: list[int]) -> QuerySet[Profile]:
        profiles = Profile.objects.filter(id__in=ids)
        cls._assert_all_profiles_are_retrieved(profiles, ids)
        return profiles

    @classmethod
    def _assert_all_profiles_are_retrieved(
        cls, profiles: QuerySet[Profile], expected_ids: list[int]
    ):
        retrieved_ids = list(profiles.values_list("id", flat=True))
        try:
            assert len(retrieved_ids) == len(expected_ids)
        except AssertionError as err:
            _logger.error(
                "Profiles have not retrieved correctly, expected_ids(%s), retrieved_ids(%s)",
                expected_ids,
                retrieved_ids,
            )
            raise err

    @classmethod
    def filter_by_kwargs(cls, **kwargs):
        return Profile.objects.filter(**kwargs)

    @classmethod
    def filter_by_server(cls, profiles: QuerySet[Profile], server: ServerLocation):
        return profiles.filter(server=server)

    @classmethod
    def create_by_kwargs(cls, **kwargs):
        return Profile.objects.create(**kwargs)
