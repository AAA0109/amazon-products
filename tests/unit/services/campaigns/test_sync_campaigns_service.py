import datetime
from decimal import Decimal

import mock
import pytest
from mock.mock import Mock

from apps.ads_api.constants import SpState, SpExpressionType, BiddingStrategies, CampaignServingStatus
from apps.ads_api.entities.amazon_ads.sponsored_products.campaign import CampaignEntity
from apps.ads_api.models import Campaign, CampaignPurpose
from apps.ads_api.services.campaigns.sync_campaigns_service import SyncCampaignsService


@pytest.fixture
def list_response():
    return {
        "campaigns": [
            {
                "budget": {"budget": 5.0, "budgetType": "DAILY"},
                "campaignId": "1",
                "dynamicBidding": {"placementBidding": [], "strategy": "LEGACY_FOR_SALES"},
                "endDate": "2019-02-21",
                "extendedData": {
                    "creationDateTime": "2019-02-15T05:35:06Z",
                    "lastUpdateDateTime": "2020-05-19T08:39:35Z",
                    "servingStatus": "CAMPAIGN_ARCHIVED",
                    "servingStatusDetails": [
                        {"name": "CAMPAIGN_ARCHIVED_DETAIL"},
                        {"name": "ENDED_DETAIL"}
                    ]
                },
                "name": "Test campaign name",
                "startDate": "2019-02-14",
                "state": "ARCHIVED",
                "targetingType": "AUTO"
            }
        ],
        "totalResults": 1
    }


@pytest.mark.django_db
class TestSyncCampaignsService:
    @mock.patch("apps.ads_api.adapters.amazon_ads.sponsored_products.campaigns_adapter.CampaignAdapter.list")
    def test_new_campaigns_created_successfuly(self, adapter_list_mock: Mock, profile, list_response):
        profile.managed = True
        profile.save()
        adapter_list_mock.return_value = [CampaignEntity.parse_obj(list_response["campaigns"][0])]

        sync_service = SyncCampaignsService([profile.id])
        sync_service.sync()

        campaign = Campaign.objects.first()
        assert float(campaign.daily_budget) == 5
        assert campaign.campaign_id_amazon == 1
        assert campaign.campaign_name == "Test campaign name"

        assert isinstance(campaign.created_at, datetime.datetime)
        assert isinstance(campaign.updated_at, datetime.datetime)

        assert campaign.sponsoring_type == "sponsoredProducts"
        assert campaign.last_updated_date_on_amazon == 1589877575000
        assert campaign.state == SpState.ARCHIVED.value
        assert campaign.targeting_type == SpExpressionType.AUTO.value
        assert campaign.bidding_strategy == BiddingStrategies.DOWN_ONLY.value
        assert campaign.serving_status == CampaignServingStatus.CAMPAIGN_ARCHIVED.value

    @mock.patch("apps.ads_api.adapters.amazon_ads.sponsored_products.campaigns_adapter.CampaignAdapter.list")
    def test_new_campaigns_updated_successfuly(self, adapter_list_mock: Mock, profile, list_response, campaign):
        profile.managed = True
        profile.save()
        campaign.campaign_id_amazon = 1
        campaign.save()
        campaign_entity = CampaignEntity.parse_obj(list_response["campaigns"][0])
        adapter_list_mock.return_value = [campaign_entity]
        Campaign.objects.filter(campaign_id_amazon=1).update(
            profile=profile,
            portfolio_id=campaign_entity.portfolio_id,
            targeting_type=campaign_entity.targeting_type,
            serving_status=CampaignServingStatus.CAMPAIGN_STATUS_ENABLED.value,
            last_updated_date_on_amazon=int(
                campaign_entity.extended_data.last_update_date_time.timestamp()
            ),
            campaign_name=campaign_entity.name,
            state=SpState.ENABLED.value,
            placement_tos_mult=0,
            placement_pp_mult=0,
            bidding_strategy=campaign_entity.dynamic_bidding.strategy
            if campaign_entity.dynamic_bidding.strategy
            else BiddingStrategies.DOWN_ONLY.value,
            premium_bid_adjustment=campaign_entity.bid_adjustment
            if campaign_entity.bid_adjustment
            else False,
            daily_budget=Decimal(campaign_entity.budget.budget),
            campaign_id_amazon=campaign_entity.external_id,
            campaign_purpose=CampaignPurpose.Auto_GP,
        )

        sync_service = SyncCampaignsService([profile.id])
        sync_service.sync()

        campaign = Campaign.objects.first()
        assert float(campaign.daily_budget) == 5
        assert campaign.campaign_id_amazon == 1
        assert campaign.campaign_name == "Test campaign name"

        assert isinstance(campaign.created_at, datetime.datetime)
        assert isinstance(campaign.updated_at, datetime.datetime)

        assert campaign.sponsoring_type == "sponsoredProducts"
        assert campaign.last_updated_date_on_amazon == 1589877575000
        assert campaign.state == SpState.ARCHIVED.value
        assert campaign.targeting_type == SpExpressionType.AUTO.value
        assert campaign.bidding_strategy == BiddingStrategies.DOWN_ONLY.value
        assert campaign.serving_status == CampaignServingStatus.CAMPAIGN_ARCHIVED.value

        assert Campaign.objects.count() == 1