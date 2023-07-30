from datetime import datetime
from typing import Iterable

from django.db.models import Sum, Q

from apps.ads_api.constants import SpReportType
from apps.ads_api.interfaces.repositories.profile.profile_budget_repository_intefrace import (
    ProfileBudgetRepositoryInterface,
)
from apps.ads_api.models import Profile, RecentReportData


class ProfileBudgetRepository(ProfileBudgetRepositoryInterface):
    def __init__(self, profile_id: int):
        self._profile_id = profile_id

    def total_spends_for_dates_range(
        self,
        date_from: datetime,
        date_to: datetime,
        exclude_dates: Iterable[datetime] = None,
    ) -> float:
        exclude_dates = exclude_dates if exclude_dates else []
        spend = (
            RecentReportData.objects.filter(
                date__gte=date_from,
                date__lte=date_to,
                campaign__profile__profile_id=self._profile_id,
                report_type=SpReportType.CAMPAIGN,
            )
            .exclude(date__in=exclude_dates)
            .aggregate(total_spend=Sum("spend"))["total_spend"]
        )
        return float(spend) if spend else 0

    def total_spends_for_date(self, date: datetime) -> float:
        spend = RecentReportData.objects.filter(
            date=date,
            campaign__profile__profile_id=self._profile_id,
            report_type=SpReportType.CAMPAIGN,
        ).aggregate(total_spend=Sum("spend"))["total_spend"]
        return float(spend) if spend else 0

    def get_monthly_planned_budget(self) -> int:
        return Profile.objects.get(profile_id=self._profile_id).monthly_budget
