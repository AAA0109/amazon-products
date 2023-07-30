import abc
from datetime import datetime
from typing import Iterable


class ProfileBudgetRepositoryInterface(abc.ABC):
    @abc.abstractmethod
    def total_spends_for_dates_range(
        self, date_from: datetime, date_to: datetime, exclude_dates: Iterable[datetime]
    ) -> float:
        pass

    @abc.abstractmethod
    def total_spends_for_date(self, date: datetime) -> float:
        pass

    @abc.abstractmethod
    def get_monthly_planned_budget(self) -> int:
        pass
