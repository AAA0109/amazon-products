import datetime

from pytest import fixture

from apps.ads_api.constants import SpReportType
from apps.ads_api.repositories.report_data_repository import ReportDataRepository


@fixture
def report_data_with_old_one(report_data, campaign, profile):
    report_data.append(
        ReportDataRepository.create_from_kwargs(
            date=datetime.datetime.today() - datetime.timedelta(days=60),
            report_type=SpReportType.CAMPAIGN,
            spend=0.2,
            campaign=campaign,
        ),
    )


@fixture()
def report_data_with_today_report_data(report_data, campaign):
    report_data.append(
        ReportDataRepository.create_from_kwargs(
            date=datetime.datetime(day=30, month=1, year=2023),
            report_type=SpReportType.CAMPAIGN,
            spend=0.2,
            campaign=campaign,
        ),
    )
    report_data.append(
        ReportDataRepository.create_from_kwargs(
            date=datetime.datetime(day=30, month=1, year=2023),
            report_type=SpReportType.CAMPAIGN,
            spend=0.8,
            campaign=campaign,
        ),
    )
