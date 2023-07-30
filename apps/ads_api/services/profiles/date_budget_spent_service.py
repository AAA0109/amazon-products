from datetime import datetime

from apps.ads_api.interfaces.services.budget.budget_calculatable_intefrace import (
    BudgetCalculatableInteface,
)
from apps.ads_api.repositories.profile.profile_budget_repository import (
    ProfileBudgetRepository,
)


class DateBudgetSpentService(BudgetCalculatableInteface):
    def __init__(self, profile_id: int, date: datetime):
        self._date = date
        self._profile_id = profile_id

    def calculate(self) -> float:
        profile_budget_repository = ProfileBudgetRepository(profile_id=self._profile_id)
        spend = profile_budget_repository.total_spends_for_date(date=self._date)
        return spend
