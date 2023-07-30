import datetime

import pytest

from apps.ads_api.constants import SpReportType
from apps.ads_api.models import RecentReportData
from apps.ads_api.services.profiles.remaining_daily_budget_service import (
    RemainingDailyBudgetService,
)


@pytest.mark.django_db
@pytest.mark.freeze_time("2023-01-30")
class TestRemainingDailyBudgetService:
    def test_remaining_daily_budget_queals_expected(self, profile, campaign):
        profile.monthly_budget = 100
        profile.research_percentage = 20
        profile.save()

        campaign.profile = profile
        campaign.save()

        RecentReportData.objects.create(
            date=datetime.datetime(day=29, month=1, year=2023),
            report_type=SpReportType.CAMPAIGN,
            spend=5,
            campaign=campaign,
        )

        remaining_daily_budget_service = RemainingDailyBudgetService(
            profile_id=profile.profile_id
        )
        actual_remaining_daily_budget = remaining_daily_budget_service.calculate()
        expected_remaining_daily_budget = 6.5

        assert actual_remaining_daily_budget == expected_remaining_daily_budget

    def test_remaining_daily_budget_equals_0_if_overspend(self, profile, campaign):
        profile.monthly_budget = 10
        profile.research_percentage = 20
        profile.save()

        campaign.profile = profile
        campaign.save()

        RecentReportData.objects.create(
            date=datetime.datetime(day=29, month=1, year=2023),
            report_type=SpReportType.CAMPAIGN,
            spend=30,
            campaign=campaign,
        )

        remaining_daily_budget_service = RemainingDailyBudgetService(
            profile_id=profile.profile_id
        )
        actual_remaining_daily_budget = remaining_daily_budget_service.calculate()
        assert actual_remaining_daily_budget == 0
