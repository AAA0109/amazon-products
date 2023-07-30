from apps.ads_api.interfaces.services.budget.budget_calculatable_intefrace import (
    BudgetCalculatableInteface,
)
from apps.ads_api.models import Profile
from apps.ads_api.services.profiles.remaining_daily_budget_service import (
    RemainingDailyBudgetService,
)


class ProvenBudgetService(BudgetCalculatableInteface):
    def __init__(self, profile: Profile):
        self._profile = profile
        self._outstanding_daily_budget_service = RemainingDailyBudgetService(
            profile.profile_id
        )

    def calculate(self) -> float:
        outstanding_daily_budget = self._outstanding_daily_budget_service.calculate()
        proven_budget = (
            1 - self._profile.research_percentage / 100
        ) * outstanding_daily_budget
        return round(proven_budget, 3)
