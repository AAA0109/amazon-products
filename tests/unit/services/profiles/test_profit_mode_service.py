import mock
import pytest
from mock.mock import Mock

from apps.ads_api.constants import SpReportType, TARGETS_VALID_STATUSES, SpState, DEFAULT_MIN_BID
from apps.ads_api.models import RecentReportData, Keyword, Target
from apps.ads_api.services.profiles.profit_mode_service import ProfitModeService


@pytest.mark.django_db
class TestProfitModeService:
    @mock.patch(
        "apps.ads_api.services.profiles.profit_mode_service.ProfitModeService._minimize_bids_for_unproved_targets"
    )
    @mock.patch("apps.ads_api.adapters.amazon_ads.sponsored_products.keywords_adapter.KeywordsAdapter.batch_update")
    def test_minimum_bids_applied_correctly_to_unproven_keywords(
            self,
            adapter_update_mock: Mock,
            minimize_turgets_mock: Mock,
            profile,
            campaign
    ):
        campaign.profile = profile
        campaign.save()

        report_data = RecentReportData()
        report_data.campaign = campaign
        report_data.keyword_id = 1
        report_data.sales = 0
        report_data.report_type = SpReportType.KEYWORD
        report_data.save()

        keyword = Keyword()
        keyword.campaign = campaign
        keyword.bid = 10
        keyword.serving_status = TARGETS_VALID_STATUSES[0]
        keyword.state = SpState.ENABLED.value
        keyword.keyword_id = 1
        keyword.save()

        ProfitModeService.turn_on(profile)
        keyword.refresh_from_db()

        adapter_update_mock.assert_called_once_with([{"keywordId": "1", "bid": DEFAULT_MIN_BID}])
        assert float(keyword.bid) == DEFAULT_MIN_BID

    @mock.patch(
        "apps.ads_api.services.profiles.profit_mode_service.ProfitModeService._minimize_bids_for_unproved_keywords"
    )
    @mock.patch("apps.ads_api.adapters.amazon_ads.sponsored_products.targets_adapter.TargetsAdapter.batch_update")
    def test_minimum_bids_applied_correctly_to_unproven_targets(
            self,
            adapter_update_mock: Mock,
            minimize_keywords_mock: Mock,
            profile,
            campaign
    ):
        campaign.profile = profile
        campaign.save()

        report_data = RecentReportData()
        report_data.campaign = campaign
        report_data.target_id = 1
        report_data.sales = 0
        report_data.report_type = SpReportType.KEYWORD
        report_data.save()

        target = Target()
        target.campaign = campaign
        target.bid = 10
        target.serving_status = TARGETS_VALID_STATUSES[0]
        target.state = SpState.ENABLED.value
        target.target_id = 1
        target.save()

        ProfitModeService.turn_on(profile)
        target.refresh_from_db()

        adapter_update_mock.assert_called_once_with([{"targetId": "1", "bid": DEFAULT_MIN_BID}])
        assert float(target.bid) == DEFAULT_MIN_BID
