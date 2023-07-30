from datetime import datetime
from decimal import Decimal
from typing import Iterable

from django.db.models import Sum, F, When, Case

from apps.ads_api.interfaces.repositories.spends_calculatable_repository_interface import (
    SpendsCalculatableRepositoryInterface,
)
from apps.ads_api.models import RecentReportData


class KeywordsSpendsRepository(SpendsCalculatableRepositoryInterface):
    def __init__(self, keywords_ids: Iterable[int]):
        self._keywords_ids = keywords_ids

    def get_toatal_spends(self) -> Decimal:
        spends = RecentReportData.objects.filter(
            keyword_id__in=self._keywords_ids
        ).aggregate(Sum("spend"))["spend__sum"]
        return spends if spends else 0

    def get_spends_for_date(self, date: datetime) -> Decimal:
        spends = RecentReportData.objects.filter(
            keyword_id__in=self._keywords_ids, date=date
        ).aggregate(Sum("spend"))["spend__sum"]
        return spends if spends else 0
