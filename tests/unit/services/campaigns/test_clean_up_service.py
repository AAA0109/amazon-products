import mock
import pytest
from mock.mock import Mock

from apps.ads_api.constants import CAMPAIGN_VALID_STATUSES, PRODUCT_AD_INVALID_STATUSES, AD_GROUP_INVALID_STATUSES, \
    CampaignServingStatus, SpState, AD_GROUP_VALID_STATUSES, PRODUCT_AD_VALID_STATUSES
from apps.ads_api.services.campaigns.clean_up_service import CleanUpCampaignsService


@pytest.mark.django_db
class TestCleanUpService:
    @mock.patch(
        "apps.ads_api.adapters.amazon_ads.sponsored_products.campaigns_adapter.CampaignAdapter.batch_update",
        return_value=([], [])
    )
    def test_pause_when_no_valid_ad_groups_or_product_ads_exist(self, adapter_update_mock: Mock, profile,
                                                                          campaign, product_ad, ad_group):
        profile.managed = True
        profile.save()

        campaign.managed = True
        campaign.profile = profile
        campaign.sponsoring_type = "sponsoredProducts"
        campaign.serving_status = CAMPAIGN_VALID_STATUSES[0]
        campaign.save()

        ad_group.campaign = campaign
        ad_group.serving_status = AD_GROUP_INVALID_STATUSES[0]
        ad_group.save()

        product_ad.serving_status = PRODUCT_AD_INVALID_STATUSES[0]
        product_ad.campaign = campaign
        product_ad.ad_group = ad_group
        product_ad.save()

        CleanUpCampaignsService.clean_up()

        adapter_update_mock.assert_called_with([{'state': 'PAUSED', 'campaignId': '123'}])

        campaign.refresh_from_db()
        assert campaign.serving_status == CampaignServingStatus.CAMPAIGN_PAUSED.value
        assert campaign.state == SpState.PAUSED.value
        assert campaign.managed is False

    @mock.patch(
        "apps.ads_api.adapters.amazon_ads.sponsored_products.campaigns_adapter.CampaignAdapter.batch_update",
        return_value=([], [])
    )
    def test_pause_with_invalid_product_ads_and_valid_ad_groups(self, adapter_update_mock: Mock, profile,
                                                                          campaign, product_ad, ad_group):
        profile.managed = True
        profile.save()

        campaign.managed = True
        campaign.profile = profile
        campaign.sponsoring_type = "sponsoredProducts"
        campaign.serving_status = CAMPAIGN_VALID_STATUSES[0]
        campaign.save()

        ad_group.campaign = campaign
        ad_group.serving_status = AD_GROUP_VALID_STATUSES[0]
        ad_group.save()

        product_ad.serving_status = PRODUCT_AD_INVALID_STATUSES[0]
        product_ad.campaign = campaign
        product_ad.ad_group = ad_group
        product_ad.save()

        CleanUpCampaignsService.clean_up()

        adapter_update_mock.assert_called_with([{'state': 'PAUSED', 'campaignId': '123'}])

        campaign.refresh_from_db()
        assert campaign.serving_status == CampaignServingStatus.CAMPAIGN_PAUSED.value
        assert campaign.state == SpState.PAUSED.value
        assert campaign.managed is False

    @mock.patch(
        "apps.ads_api.adapters.amazon_ads.sponsored_products.campaigns_adapter.CampaignAdapter.batch_update",
        return_value=([], [])
    )
    def test_do_not_pause_with_valid_product_ads_and_valid_ad_groups(self, adapter_update_mock: Mock, profile,
                                                                          campaign, product_ad, ad_group):
        profile.managed = True
        profile.save()

        campaign.managed = True
        campaign.profile = profile
        campaign.sponsoring_type = "sponsoredProducts"
        campaign.serving_status = CAMPAIGN_VALID_STATUSES[0]
        campaign.save()

        ad_group.campaign = campaign
        ad_group.serving_status = AD_GROUP_VALID_STATUSES[0]
        ad_group.save()

        product_ad.serving_status = PRODUCT_AD_VALID_STATUSES[0]
        product_ad.campaign = campaign
        product_ad.ad_group = ad_group
        product_ad.save()

        CleanUpCampaignsService.clean_up()

        adapter_update_mock.assert_not_called()
