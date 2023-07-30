import datetime

import pytest

from apps.ads_api.constants import SpReportType
from apps.ads_api.repositories.report_data_repository import ReportDataRepository


@pytest.fixture
def report_data_with_keywords(report_data, campaign, keywords):
    report_data.append(
        ReportDataRepository.create_from_kwargs(
            date=datetime.datetime.today(),
            report_type=SpReportType.KEYWORD,
            spend=0.8,
            campaign=campaign,
            keyword_id=keywords[0].keyword_id,
        )
    )

    report_data.append(
        ReportDataRepository.create_from_kwargs(
            date=datetime.datetime.today(),
            report_type=SpReportType.KEYWORD,
            spend=0.2,
            campaign=campaign,
            keyword_id=keywords[1].keyword_id,
        )
    )
