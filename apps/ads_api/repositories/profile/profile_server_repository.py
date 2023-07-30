from apps.ads_api.constants import ServerLocation
from apps.ads_api.models import Profile


class ProfileServerRepository:
    def __init__(self, server_location: ServerLocation):
        self._server_location = server_location

    def get_primary_keys_list(self) -> list[int]:
        return list(
            Profile.objects.filter(
                managed=True, profile_server=self._server_location
            ).values_list("pk", flat=True)
        )

    def get_profile_ids_list(self) -> list[int]:
        return list(
            Profile.objects.filter(
                managed=True, profile_server=self._server_location
            ).values_list("profile_id", flat=True)
        )
