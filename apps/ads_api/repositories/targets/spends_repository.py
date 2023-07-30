from datetime import datetime
from decimal import Decimal
from typing import Iterable

from django.db.models import Sum

from apps.ads_api.interfaces.repositories.spends_calculatable_repository_interface import (
    SpendsCalculatableRepositoryInterface,
)
from apps.ads_api.models import RecentReportData


class TargetsSpendsRepository(SpendsCalculatableRepositoryInterface):
    def __init__(self, targets_ids: Iterable[int]):
        self._targets_ids = targets_ids

    def get_toatal_spends(self) -> Decimal:
        spends = RecentReportData.objects.filter(
            target_id__in=self._targets_ids
        ).aggregate(Sum("spend"))["spend__sum"]
        return spends if spends else 0

    def get_spends_for_date(self, date: datetime):
        spends = RecentReportData.objects.filter(
            target_id__in=self._targets_ids, date=date
        ).aggregate(Sum("spend"))["spend__sum"]
        return spends if spends else 0
