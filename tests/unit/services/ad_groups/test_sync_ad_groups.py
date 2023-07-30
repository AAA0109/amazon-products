import datetime

import mock
import pytest
from mock.mock import Mock

from apps.ads_api.constants import SpState
from apps.ads_api.entities.amazon_ads.sponsored_products.ad_group import AdGroupEntity
from apps.ads_api.services.ad_groups.sync_ad_groups_service import SyncAdGroupsService


@pytest.mark.django_db
@mock.patch("apps.ads_api.adapters.amazon_ads.sponsored_products.ad_group_adapter.AdGroupAdapter.list")
@mock.patch("apps.ads_api.services.ad_groups.sync_ad_groups_service.SyncAdGroupsService._update_or_create")
class TestSyncAdGroupsService:
    def test_update_or_create_not_called_if_no_campaign_exists(self, update_create_mock: Mock, ad_group_list_mock: Mock, profile, campaign):
        sync_service = SyncAdGroupsService([profile.id])
        ad_group_list_mock.return_value = [AdGroupEntity(**{
            "campaign_id": "123456789",
            "external_id": "987654321",
            "name": "Example Ad Group",
            "state": SpState.ENABLED,
            "extended_data": {
                "serving_status": "servable",
                "last_update_date_time": datetime.datetime.now()
            },
            "bid": 1.5
        })]

        sync_service.sync()

        update_create_mock.assert_not_called()

    def test_update_or_create_called_if_campaign_exists(self, update_create_mock: Mock, ad_group_list_mock: Mock, profile,
                                                        campaign):
        campaign.campaign_id_amazon = 123456789
        campaign.profile = profile
        campaign.save()
        sync_service = SyncAdGroupsService([profile.id])
        ad_group_entity = AdGroupEntity(**{
            "campaign_id": "123456789",
            "external_id": "987654321",
            "name": "Example Ad Group",
            "state": SpState.ENABLED,
            "extended_data": {
                "serving_status": "servable",
                "last_update_date_time": datetime.datetime.now()
            },
            "bid": 1.5
        })
        ad_group_list_mock.return_value = [ad_group_entity]

        sync_service.sync()

        update_create_mock.assert_called_once_with(ad_group=ad_group_entity)
