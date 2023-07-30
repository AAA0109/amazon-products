import datetime

import pytest

from apps.ads_api.repositories.targets.targets_repository import TargetsRepository
from apps.ads_api.services.keywords.date_keywords_spends_service import (
    DateKeywordsSpendsServce,
)


@pytest.mark.freeze_time("2023-01-30")
@pytest.mark.django_db
def test_date_targets_spends_equal_one(report_data_with_targets):
    date_targets_spends_service = DateKeywordsSpendsServce(
        date=datetime.datetime.today(),
        keywords_list=TargetsRepository.retrieve_all().values()
    )
    actual_spends = date_targets_spends_service.calculate_spends()
    assert actual_spends == 1
