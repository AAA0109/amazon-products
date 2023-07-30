import datetime

import pytest

from apps.ads_api.constants import SpReportType
from apps.ads_api.repositories.report_data_repository import ReportDataRepository


@pytest.fixture
def report_data_with_targets(report_data, campaign, targets):
    report_data.append(
        ReportDataRepository.create_from_kwargs(
            date=datetime.datetime.today(),
            report_type=SpReportType.TARGET,
            spend=0.8,
            campaign=campaign,
            target_id=targets[0].target_id,
        )
    )

    report_data.append(
        ReportDataRepository.create_from_kwargs(
            date=datetime.datetime.today(),
            report_type=SpReportType.TARGET,
            spend=0.2,
            campaign=campaign,
            target_id=targets[1].target_id,
        )
    )
