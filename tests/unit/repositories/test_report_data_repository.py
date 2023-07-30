import datetime

import pytest

from apps.ads_api.constants import SpReportType
from apps.ads_api.models import ReportData, RecentReportData
from apps.ads_api.repositories.report_data_repository import ReportDataRepository


@pytest.fixture
def report_data_91_day(campaign):
    report_data = ReportDataRepository.create_from_kwargs(
        date=datetime.datetime(day=29, month=1, year=2023),
        report_type=SpReportType.CAMPAIGN,
        spend=0.8,
        campaign=campaign,
    )

    report_data.date = datetime.datetime.today() - datetime.timedelta(days=91)
    report_data.keyword_id = 9999
    report_data.save()
    return report_data

@pytest.mark.django_db
def test_transfere_90_days_recent_report_data_to_report_data(report_data_91_day):
    ReportDataRepository.transfere_90_days_recent_report_data_to_report_data()
    assert ReportData.objects.filter(keyword_id=9999).count() == 1
    assert RecentReportData.objects.filter(keyword_id=9999).count() == 0

