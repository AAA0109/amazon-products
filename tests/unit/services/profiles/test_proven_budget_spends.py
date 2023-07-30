import datetime

import pytest

from apps.ads_api.constants import SpReportType
from apps.ads_api.models import RecentReportData
from apps.ads_api.services.profiles.proven_budget_service import ProvenBudgetService


@pytest.mark.freeze_time("2023-01-30")
@pytest.mark.django_db
def test_proven_budget_spends_equal_one(profile, campaign):
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

    proven_budget_service = ProvenBudgetService(profile=profile)
    proven_budget = proven_budget_service.calculate()
    assert proven_budget == 5.2
