from datetime import datetime
from typing import Iterator, Iterable

from apps.ads_api.constants import (
    EMPTY_REPORT_BYTES,
    AmazonReportStatuses,
    ReportStatus,
)
from apps.ads_api.entities.amazon_ads.reports import ReportEntity, ReportListEntity
from apps.ads_api.models import Report


class ReportStatusRepository:
    @classmethod
    def count_by_status(cls, status: ReportStatus):
        if status == ReportStatus.COMPLETED:
            count = (
                Report.objects.filter(
                    report_status__in=[
                        status.value for status in AmazonReportStatuses.COMPLETED
                    ]
                )
                .exclude(report_size=EMPTY_REPORT_BYTES)
                .count()
            )
        elif status == ReportStatus.EMPTY:
            count = Report.objects.filter(
                report_status__in=[
                    status.value for status in AmazonReportStatuses.COMPLETED
                ],
                report_size=EMPTY_REPORT_BYTES,
            ).count()
        elif status == ReportStatus.PENDING:
            count = Report.objects.filter(
                report_status__in=[
                    status.value for status in AmazonReportStatuses.PENDING
                ]
            ).count()
        else:
            count = Report.objects.filter(report_status=status).count()
        return count

    @classmethod
    def retrieve_reports_to_download_iterator(cls) -> Iterator[ReportEntity]:
        reports_iterator = (
            Report.objects.filter(
                report_status__in=[
                    status.value for status in AmazonReportStatuses.PENDING
                ]
            )
            .order_by("updated_at")
            .values(
                "report_id",
                "profile_id",
                "report_server",
                "report_type",
                "report_for_date",
            )
            .iterator()
        )

        for report in reports_iterator:
            report = ReportEntity.parse_obj(
                {
                    "report_id": report["report_id"],
                    "profile_id": report["profile_id"],
                    "report_server": report["report_server"],
                    "report_type": report["report_type"],
                    "report_for_date": report["report_for_date"],
                }
            )
            yield report

    @classmethod
    def retrieve_by_statuses(cls, statuses: Iterable[ReportStatus]):
        reports = Report.objects.filter(
            report_status__in=[status.value for status in statuses]
        ).values()
        if reports:
            reports = ReportListEntity.parse_obj(list(reports))
        else:
            reports = []
        return reports

    @classmethod
    def update_empty_reports_as_initial_processed(cls):
        """
        Updates successful reports witch size equals to empty reports bytes size (24)
        """
        Report.objects.filter(
            report_status__in=[
                status.value for status in AmazonReportStatuses.COMPLETED
            ],
            report_size=EMPTY_REPORT_BYTES,
        ).update(report_status=ReportStatus.INTERNAL_PROCESSED.value)

    @classmethod
    def is_reports_with_success_status_exists(
        cls, profile_id: int, report_type: str, date: datetime
    ) -> bool:
        """
        Checks if report with given args is exists, will exclude reports with failed status
        """
        return (
            Report.objects.filter(
                profile_id=profile_id,
                report_type=report_type,
                report_for_date=date,
            )
            .exclude(report_status__contains=ReportStatus.FAILURE.value)
            .exists()
        )
