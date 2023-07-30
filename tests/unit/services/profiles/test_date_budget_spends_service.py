import pytest
from datetime import datetime

from apps.ads_api.services.profiles.date_budget_spent_service import (
    DateBudgetSpentService,
)


@pytest.mark.freeze_time("2023-01-30")
@pytest.mark.django_db
def test_result_of_calculate_equals_one(profile, report_data_with_today_report_data):
    date_budget_spend_service = DateBudgetSpentService(
        profile_id=profile.profile_id, date=datetime.today()
    )
    spend = date_budget_spend_service.calculate()
    assert spend == 1
