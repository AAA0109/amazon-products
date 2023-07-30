from datetime import datetime
from typing import Optional, Union

from apps.ads_api.interfaces.services.spends.spends_calculatable_interface import (
    SpendsCalculatableInterface,
)
from apps.ads_api.models import Keyword, Target
from apps.utils.repositories.spends_repository_mapper import SpendsRepositoryMapper


class DateKeywordsSpendsServce(SpendsCalculatableInterface):
    def __init__(self, date: datetime, keywords_list: list[Union[Keyword, Target]]):
        self._date = date
        self._keywords_list = keywords_list
        self._repository_mapper = SpendsRepositoryMapper(keywords_list)

    def calculate_spends(self) -> Optional[float]:
        spends = 0
        if self._keywords_list:
            repository = self._repository_mapper.get_repository()
            spends = repository.get_spends_for_date(self._date)
        return float(spends)
