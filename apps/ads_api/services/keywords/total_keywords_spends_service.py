from typing import Union, Optional

from django.db.models import QuerySet

from apps.ads_api.interfaces.services.spends.spends_calculatable_interface import (
    SpendsCalculatableInterface,
)
from apps.ads_api.models import Keyword, Target
from apps.utils.repositories.spends_repository_mapper import SpendsRepositoryMapper


class TotalKeywordsSpendsService(SpendsCalculatableInterface):
    def __init__(self, queryset: QuerySet[Union[Keyword, Target]]):
        self._queryset = queryset
        self._repository_mapper = SpendsRepositoryMapper(queryset)

    def calculate_spends(self) -> Optional[float]:
        repository = self._repository_mapper.get_repository()
        spends = repository.get_toatal_spends()
        return float(spends)
