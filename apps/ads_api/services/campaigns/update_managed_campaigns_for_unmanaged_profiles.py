from typing import List

from apps.ads_api.repositories.campaign_repository import CampaignRepository


class UpdateManagedCampaignsForUnmanagedProfilesService:
    @classmethod
    def update(cls, profile_pks: List[int]):
        CampaignRepository.set_managed_false_for_profiles(profile_pks)
