from datetime import datetime, timedelta

from apps.ads_api.constants import DEFAULT_BUDGETING_DAYS
from apps.ads_api.interfaces.services.budget.budget_calculatable_intefrace import (
    BudgetCalculatableInteface,
)
from apps.ads_api.repositories.profile.profile_budget_repository import (
    ProfileBudgetRepository,
)


class MonthlyBudgetSpentService(BudgetCalculatableInteface):
    def __init__(self, profile_id: int):
        self._profile_id = profile_id
        self._profile_budget_repository = ProfileBudgetRepository(profile_id=self._profile_id)

    def calculate(self) -> float:
        date_from = datetime.today() - timedelta(days=DEFAULT_BUDGETING_DAYS)  # Calculate date 30 days ago
        date_to = datetime.today()
        spend = self._profile_budget_repository.total_spends_for_dates_range(date_from=date_from, date_to=date_to)
        return spend if spend else 0
