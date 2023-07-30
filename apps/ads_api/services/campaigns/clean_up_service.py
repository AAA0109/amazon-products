import logging
from datetime import datetime

from django.db.models import Q

from apps.ads_api.adapters.amazon_ads.sponsored_products.campaigns_adapter import CampaignAdapter
from apps.ads_api.constants import PRODUCT_AD_INVALID_STATUSES, AD_GROUP_INVALID_STATUSES, \
    CampaignServingStatus, SpState, CAMPAIGN_VALID_STATUSES
from apps.ads_api.entities.amazon_ads.sponsored_products.campaign import CampaignEntity
from apps.ads_api.exceptions.ads_api.base import BaseAmazonAdsException
from apps.ads_api.models import Campaign, AdGroup, ProductAd
from apps.ads_api.repositories.profile_repository import ProfileRepository

_logger = logging.getLogger(__name__)


class CleanUpCampaignsService:
    @classmethod
    def clean_up(cls):
        """Pauses managed campaigns with invalid ad groups or product ads"""
        profiles = ProfileRepository.get_managed_profiles()
        for profile in profiles:
            campaigns_to_pause = []
            campaigns_to_pause_in_db = []
            campaigns_to_check = Campaign.objects.filter(
                Q(product_ads__serving_status__in=PRODUCT_AD_INVALID_STATUSES)
                | Q(ad_groups__serving_status__in=AD_GROUP_INVALID_STATUSES),
                serving_status__in=CAMPAIGN_VALID_STATUSES,
                managed=True,
                profile=profile,
                sponsoring_type="sponsoredProducts",
            )
            if not campaigns_to_check.exists():
                continue
            for campaign in campaigns_to_check:
                # check if there are any valid ad groups
                valid_ad_groups = AdGroup.objects.filter(campaign=campaign).exclude(
                    serving_status__in=AD_GROUP_INVALID_STATUSES
                )
                # check if there are any valid product ads
                valid_product_ads = ProductAd.objects.filter(campaign=campaign).exclude(
                    serving_status__in=PRODUCT_AD_INVALID_STATUSES
                )
                if valid_ad_groups.count() == 0 or valid_product_ads.count() == 0:
                    campaigns_to_pause.append(
                        CampaignEntity(external_id=campaign.campaign_id_amazon, state=SpState.PAUSED).dict(
                            exclude_none=True, by_alias=True)
                    )
                    campaign.serving_status = CampaignServingStatus.CAMPAIGN_PAUSED.value
                    campaign.state = SpState.PAUSED.value
                    campaign.managed = False
                    campaigns_to_pause_in_db.append(campaign)

            if len(campaigns_to_pause) > 0:
                campaign_adapter = CampaignAdapter(profile)
                successfully_updated, errors = campaign_adapter.batch_update(campaigns_to_pause)

                Campaign.objects.bulk_update(
                    campaigns_to_pause_in_db,
                    ["serving_status", "state", "managed"],
                    batch_size=1000,
                )

                if errors:
                    _logger.error(
                        "Some campaigns were not updated. Updated [%s], errors [%s]",
                        successfully_updated,
                        errors,
                    )
                    raise BaseAmazonAdsException(
                        "Some campaigns were not updated. To see additional information, please "
                        f"refer to the logs. Time - {datetime.now()}"
                    )

                _logger.info(
                    "Paused %s campaigns on profile: %s [%s]",
                    len(campaigns_to_pause),
                    profile.nickname,
                    profile.country_code,
                )
