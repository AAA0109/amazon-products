import pytest

from apps.ads_api.constants import ReportStatus, EMPTY_REPORT_BYTES
from apps.ads_api.models import Report
from apps.ads_api.repositories.report.status_repository import \
    ReportStatusRepository


@pytest.mark.django_db
def test_count_by_status():
    Report.objects.create(
        report_id=f"report_id_1",
        report_status=ReportStatus.COMPLETED,
        report_size=EMPTY_REPORT_BYTES,
    )
    Report.objects.create(
        report_id=f"4_report_id_2",
        report_status=ReportStatus.PENDING,
        report_size=EMPTY_REPORT_BYTES,
    )

    for i, val in enumerate(ReportStatus.__members__.values()):
        Report.objects.create(
            report_id=f"{i}_report_id",
            report_status=val,
        )

    count_completed = ReportStatusRepository().count_by_status(
        ReportStatus.COMPLETED
    )
    assert count_completed == 1

    count_empty = ReportStatusRepository().count_by_status(ReportStatus.EMPTY)
    assert count_empty == 1

    count_pending = ReportStatusRepository().count_by_status(
        ReportStatus.PENDING
    )
    assert count_pending == 3

    count_processing = ReportStatusRepository().count_by_status(
        ReportStatus.PROCESSING
    )
    assert count_processing == 1
