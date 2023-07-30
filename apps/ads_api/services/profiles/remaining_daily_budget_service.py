import logging

from apps.ads_api.constants import DEFAULT_BUDGETING_DAYS, MIN_MONTHLY_BUDGET
from apps.ads_api.interfaces.services.budget.budget_calculatable_intefrace import (
    BudgetCalculatableInteface,
)
from apps.ads_api.repositories.profile.profile_budget_repository import (
    ProfileBudgetRepository,
)
from apps.ads_api.services.profiles.monthly_budget_spent_service import (
    MonthlyBudgetSpentService,
)

_logger = logging.getLogger(__name__)


class RemainingDailyBudgetService(BudgetCalculatableInteface):
    def __init__(self, profile_id: int):
        if not isinstance(profile_id, int):
            raise TypeError("profile_id must be an integer.")
        self._profile_id = profile_id
        self._profile_budget_repository = ProfileBudgetRepository(profile_id=self._profile_id)
        self._monthly_budget_spent_service = MonthlyBudgetSpentService(profile_id=self._profile_id)

    def calculate(self) -> float:
        actually_spend_budget = self._monthly_budget_spent_service.calculate()
        planned_budget = self._profile_budget_repository.get_monthly_planned_budget()

        if planned_budget is None or planned_budget == 0:
            _logger.error(
                f"No planned budget found for profile_id {self._profile_id}, setting planned_budget to actually_spend_budget or {MIN_MONTHLY_BUDGET} if it's less."
            )
            planned_budget = int(
                actually_spend_budget if actually_spend_budget >= MIN_MONTHLY_BUDGET else MIN_MONTHLY_BUDGET
            )

        days_in_period = DEFAULT_BUDGETING_DAYS  # Normally 30 days

        # Get delta from the last 30 days
        # delta_last_period will be positive if underspent, negative if overspent
        delta_last_period = planned_budget - actually_spend_budget

        # Any delta added to or taken away from the planned budget
        remaining_daily_budget = (planned_budget + delta_last_period) / days_in_period

        if remaining_daily_budget < 0:
            remaining_daily_budget = 0

        return round(remaining_daily_budget, 3)
