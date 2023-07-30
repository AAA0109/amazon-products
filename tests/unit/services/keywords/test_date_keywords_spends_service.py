import datetime

import pytest

from apps.ads_api.repositories.keywords.keywords_repository import KeywordsRepository
from apps.ads_api.services.keywords.date_keywords_spends_service import (
    DateKeywordsSpendsServce,
)


@pytest.mark.django_db
def test_date_keywords_spends_equal_one(report_data_with_keywords):
    date_keywords_spends_service = DateKeywordsSpendsServce(
        date=datetime.datetime.today(), keywords_list=KeywordsRepository.retrieve_all().values()
    )
    actual_spends = date_keywords_spends_service.calculate_spends()
    assert actual_spends == 1
