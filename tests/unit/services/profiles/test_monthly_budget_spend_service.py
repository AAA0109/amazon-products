import pytest
from apps.ads_api.services.profiles.monthly_budget_spent_service import (
    MonthlyBudgetSpentService,
)


@pytest.mark.freeze_time("2023-01-30")
@pytest.mark.django_db
def test_result_of_calculate_equals_one(profile, report_data):
    monthly_budget_spend_service = MonthlyBudgetSpentService(profile.profile_id)
    spend = monthly_budget_spend_service.calculate()
    assert spend == 1


@pytest.mark.freeze_time("2023-01-30")
@pytest.mark.django_db
def test_old_report_data_sholud_not_be_included(profile, report_data_with_old_one):
    monthly_budget_spend_service = MonthlyBudgetSpentService(profile.profile_id)
    spend = monthly_budget_spend_service.calculate()
    assert spend == 1
