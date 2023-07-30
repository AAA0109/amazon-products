from typing import Optional

from django.db import IntegrityError

from apps.ads_api.adapters.amazon_ads.sponsored_products.ad_group_adapter import (
    AdGroupAdapter,
)
from apps.ads_api.constants import TimeUnit
from apps.ads_api.entities.amazon_ads.sponsored_products.ad_group import AdGroupEntity
from apps.ads_api.entities.amazon_ads.sponsored_products.search_filters import (
    AdGroupSearchFilter,
)
from apps.ads_api.models import AdGroup, Campaign, Profile
from apps.utils.iso_to_epoch_converter import IsoToEpochConverter


class SyncAdGroupsService:
    def __init__(self, profile_ids: Optional[list[int]] = None):
        """
        :param profile_ids: primary keys of profiles. If no IDs
            were given, all managed profiles would be taken to process.
        """
        if profile_ids:
            profiles = Profile.objects.filter(id__in=profile_ids)
        else:
            # Only run for managed profiles
            profiles = Profile.objects.filter(managed=True)

        self._profiles = profiles

    @classmethod
    def get_ad_groups_from_adapter(cls, profile: Profile) -> list[AdGroupEntity]:
        """
        Retrieves campaigns from amazon API by using adapter.

        :param profile: Django ORM Profile model
        :return: list of CampaignEntity objects
        """
        adapter = AdGroupAdapter(profile)
        profile_campaigns = adapter.list(AdGroupSearchFilter())

        return profile_campaigns

    def sync(self):
        all_profile_campaigns = self.get_campaigns_for_managed_profiles()

        campaigns_by_campaign_id = {
            campaign["campaign_id_amazon"]: campaign["id"]
            for campaign in all_profile_campaigns
        }

        for current_profile in self._profiles:
            profile_ad_groups = self.get_ad_groups_from_adapter(current_profile)
            if not profile_ad_groups:
                continue

            for current_ad_group in profile_ad_groups:
                current_ad_group.internal_id = campaigns_by_campaign_id.get(
                    int(current_ad_group.campaign_id)
                )
                if not current_ad_group.internal_id:
                    continue
                self._update_or_create(ad_group=current_ad_group)

    @staticmethod
    def _update_or_create(ad_group: AdGroupEntity):
        converter = IsoToEpochConverter()
        try:
            AdGroup.objects.update_or_create(
                campaign_id=ad_group.internal_id,
                ad_group_id=int(ad_group.external_id),
                defaults={
                    "ad_group_name": ad_group.name,
                    "state": ad_group.state,
                    "serving_status": ad_group.extended_data.serving_status,
                    "last_updated_date_on_amazon":
                        converter.iso_to_epoch(
                            ad_group.extended_data.last_update_date_time,
                            convert_to=TimeUnit.MILLISECOND
                        ),
                    "default_bid": ad_group.bid,
                },
            )
        except IntegrityError:
            AdGroup.objects.filter(ad_group_id=ad_group.external_id).delete()
            AdGroup.objects.update_or_create(
                campaign_id=ad_group.internal_id,
                ad_group_id=int(ad_group.external_id),
                defaults={
                    "ad_group_name": ad_group.name,
                    "state": ad_group.state,
                    "serving_status": ad_group.extended_data.serving_status,
                    "last_updated_date_on_amazon":
                        converter.iso_to_epoch(
                            ad_group.extended_data.last_update_date_time,
                            convert_to=TimeUnit.MILLISECOND
                        ),
                    "default_bid": ad_group.bid,
                },
            )

    def get_campaigns_for_managed_profiles(self) -> list[dict]:
        return list(
            Campaign.objects.filter(
                profile__in=self._profiles, sponsoring_type="sponsoredProducts"
            ).values("campaign_id_amazon", "id")
        )
