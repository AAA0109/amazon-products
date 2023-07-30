import logging
from decimal import Decimal

import mock
import pytest
from mock.mock import Mock

from apps.ads_api.adapters.amazon_ads.sponsored_products.campaigns_adapter import (
    CampaignAdapter,
)
from apps.ads_api.constants import (
    CampaignRetryStrategy,
    CampaignServingStatus,
    ProductAdServingStatus,
)
from apps.ads_api.factories.compaign_factory import CampaignFactory
from apps.ads_api.models import (
    AdGroup,
    Book,
    Campaign,
    CampaignPurpose,
    ProductAd,
    Target,
)
from apps.ads_api.tasks import RetryServiceForCampaignsWithInvalidStatus

_logger = logging.getLogger(__name__)

campaigns_to_recrate_strategy = [
    {
        "serving_status": CampaignServingStatus.OTHER.value,
        "product_ads__serving_status": ProductAdServingStatus.ADVERTISER_STATUS_ENABLED.value,
        "campaign_id_amazon": 1,
        "id": 1,
    },
    {
        "product_ads__serving_status": ProductAdServingStatus.AD_MISSING_DECORATION.value,
        "serving_status": CampaignServingStatus.ACCOUNT_OUT_OF_BUDGET.value,
        "id": 1,
        "campaign_id_amazon": 1,
    },
    {
        "product_ads__serving_status": ProductAdServingStatus.AD_POLICING_SUSPENDED.value,
        "serving_status": CampaignServingStatus.ACCOUNT_OUT_OF_BUDGET.value,
        "id": 1,
        "campaign_id_amazon": 1,
    },
]

campaigns_to_fill_up_with_keywords_strategy = [
    {
        "serving_status": CampaignServingStatus.CAMPAIGN_INCOMPLETE.value,
        "product_ads__serving_status": ProductAdServingStatus.ADVERTISER_STATUS_ENABLED.value,
        "id": 1,
        "campaign_id_amazon": 1,
    }
]


@pytest.fixture
def invalid_campaigns(profile):
    return [
        Campaign.objects.create(
            profile=profile,
            managed=True,
            campaign_id_amazon=1,
            campaign_purpose=CampaignPurpose.Discovery,
            campaign_name="ABFM-SP-Auto-Discovery-Complements-1-1801019959-Paperback",
            serving_status=CampaignServingStatus.OTHER.value,
        ),
        Campaign.objects.create(
            profile=profile,
            managed=True,
            campaign_id_amazon=2,
            campaign_purpose=CampaignPurpose.Discovery,
            campaign_name="ABFM-SP-Auto-Discovery-Complements-2-1801019959-Paperback",
            serving_status=CampaignServingStatus.CAMPAIGN_INCOMPLETE.value,
        ),
    ]


@pytest.fixture
def invalid_ad_groups(profile):
    campaign_1 = Campaign.objects.create(
        profile=profile,
        managed=True,
        campaign_id_amazon=3,
        campaign_purpose=CampaignPurpose.Discovery,
        campaign_name="ABFM-SP-Auto-Discovery-Complements-3-1801019959-Paperback",
    )
    ad_group_1 = AdGroup.objects.create(
        ad_group_id=1, ad_group_name="test_ad_group_name", campaign=campaign_1
    )
    ProductAd.objects.create(
        product_ad_id=1,
        campaign=campaign_1,
        ad_group=ad_group_1,
        serving_status=ProductAdServingStatus.AD_MISSING_DECORATION.value,
    )

    campaign_2 = Campaign.objects.create(
        profile=profile,
        managed=True,
        campaign_id_amazon=4,
        campaign_purpose=CampaignPurpose.Discovery,
        campaign_name="ABFM-SP-Auto-Discovery-Complements-4-1801019959-Paperback",
    )
    ad_group_2 = AdGroup.objects.create(
        ad_group_id=2, ad_group_name="test_ad_group_name", campaign=campaign_2
    )
    ProductAd.objects.create(
        product_ad_id=2,
        campaign=campaign_2,
        ad_group=ad_group_2,
        serving_status=ProductAdServingStatus.AD_POLICING_SUSPENDED.value,
    )


@pytest.fixture
def add_books_to_campaigns():
    for indx, campaign in enumerate(Campaign.objects.all(), start=1):
        campaign.books.add(
            Book.objects.create(
                title=f"test_title_{indx}",
                asin=f"testasin_{indx}",
            )
        )


class TestRetryServiceForCampaignsWithInvalidStatus:
    @pytest.mark.django_db
    def test_all_campaigns_with_faliled_statuses_are_retrieved(self, invalid_campaigns, invalid_ad_groups):
        retry_service = RetryServiceForCampaignsWithInvalidStatus([invalid_campaigns[0].profile])
        invalid_campaigns = retry_service._retrieve_invalid_campaigns(invalid_campaigns[0].profile)

        assert set(invalid_campaigns.values_list("campaign_id_amazon", flat=True)) == {
            1,
            2,
            3,
            4,
        }

    @pytest.mark.parametrize("campaign_to_recreate", campaigns_to_fill_up_with_keywords_strategy)
    @mock.patch("apps.ads_api.tasks.RetryServiceForCampaignsWithInvalidStatus._fill_campaign_with_keywords")
    def test_retry_strategy_fill_up_with_keywords_called(
        self, fill_campaign_with_keywords_mock: Mock, monkeypatch, campaign_to_recreate
    ):
        monkeypatch.setattr(
            RetryServiceForCampaignsWithInvalidStatus,
            "_retrieve_invalid_campaigns",
            lambda _, profile: [campaign_to_recreate],
        )
        monkeypatch.setattr(
            RetryServiceForCampaignsWithInvalidStatus,
            "_increase_campaigns_retry_counter",
            Mock(),
        )
        monkeypatch.setattr(
            RetryServiceForCampaignsWithInvalidStatus,
            "_post_recreate_actions",
            Mock(),
        )
        retry_service = RetryServiceForCampaignsWithInvalidStatus([Mock()])
        retry_service.retry()

        fill_campaign_with_keywords_mock.assert_called_once()

    @pytest.mark.parametrize("campaign_to_recreate", campaigns_to_recrate_strategy)
    @mock.patch("apps.ads_api.tasks.RetryServiceForCampaignsWithInvalidStatus._recreate_campaign")
    def test_retry_strategy_recreate_called(
        self,
        recreate_campaign: Mock,
        campaign_to_recreate,
        monkeypatch,
    ):
        monkeypatch.setattr(
            RetryServiceForCampaignsWithInvalidStatus,
            "_retrieve_invalid_campaigns",
            lambda _, profile: [campaign_to_recreate],
        )
        monkeypatch.setattr(
            RetryServiceForCampaignsWithInvalidStatus,
            "_increase_campaigns_retry_counter",
            Mock(),
        )
        monkeypatch.setattr(
            RetryServiceForCampaignsWithInvalidStatus,
            "_post_recreate_actions",
            Mock(),
        )
        monkeypatch.setattr(CampaignAdapter, "batch_update", Mock())
        retry_service = RetryServiceForCampaignsWithInvalidStatus([Mock()])
        retry_service.retry()

        recreate_campaign.assert_called_once()

    @pytest.mark.django_db
    @mock.patch(
        "apps.ads_api.tasks.RetryServiceForCampaignsWithInvalidStatus._create_campaign", return_value=None
    )
    def test_create_campaign_takes_proper_arguments(
        self,
        create_campaign_mock: Mock,
        invalid_ad_groups,
        add_books_to_campaigns,
        profile,
    ):
        retry_service = RetryServiceForCampaignsWithInvalidStatus([profile])
        invalid_campaign = retry_service._retrieve_invalid_campaigns(profile)[0]

        Target.objects.create(
            campaign_id=invalid_campaign["id"], ad_group_id=invalid_campaign["ad_groups__ad_group_id"]
        )
        expected_campaign_dict = {
            "campaign_id_amazon": invalid_campaign["campaign_id_amazon"],
            "campaign_name": invalid_campaign["campaign_name"],
            "serving_status": invalid_campaign["serving_status"],
            "campaign_purpose": invalid_campaign["campaign_purpose"],
            "bidding_strategy": invalid_campaign["bidding_strategy"],
            "placement_tos_mult": invalid_campaign["placement_tos_mult"],
            "placement_pp_mult": invalid_campaign["placement_pp_mult"],
            "id": invalid_campaign["id"],
            "ad_groups__default_bid": invalid_campaign["ad_groups__default_bid"],
            "ad_groups__ad_group_id": invalid_campaign["ad_groups__ad_group_id"],
            "product_ads__product_ad_id": invalid_campaign["product_ads__product_ad_id"],
            "product_ads__serving_status": invalid_campaign["product_ads__serving_status"],
            "product_ads__asin": invalid_campaign["product_ads__asin"],
            "profile__country_code": invalid_campaign["profile__country_code"],
            "books": invalid_campaign["books"],
        }

        retry_service._recreate_campaign(invalid_campaign)

        assert type(create_campaign_mock.call_args.args[0]) is Book  # assert first argument is book
        assert (
            create_campaign_mock.call_args.args[1] == expected_campaign_dict
        )  # assert proper campaign passed to create method
        assert create_campaign_mock.call_args.args[2] == []  # assert no keyords passed
        assert create_campaign_mock.call_args.args[3] == [
            {"resolved_expression_text": "", "resolved_expression_type": "", "targeting_type": "MANUAL"}
        ]  # assert 1 target passed
