import logging

from apps.ads_api.constants import ServerLocation, AmazonReportStatuses, ReportStatus
from apps.ads_api.entities.amazon_ads.reports import ReportEntity
from apps.ads_api.exceptions.ads_api.reports import (
    RefreshingReportException,
    StillGeneratingReportException,
)
from apps.ads_api.interfaces.services.reports.refresh_report_interface import (
    RefreshReportInterface,
)
from apps.ads_api.repositories.report_repository import ReportRepository
from apps.ads_api.services.amazon.reports.fetch_from_amazon_service import (
    FetchReportDetailsService,
)

_logger = logging.getLogger(__name__)


class RefreshReportService(RefreshReportInterface):
    def __init__(self):
        self.report_repository = ReportRepository()

    def refresh(
        self, server: ServerLocation, report_id: str, profile_id: int
    ) -> ReportEntity:
        fetch_report_details_service = FetchReportDetailsService(server)
        report = fetch_report_details_service.fetch(
            report_id=report_id, profile_id=profile_id
        )

        if self._is_report_failed(report):
            if report.failure_reason:
                _logger.warning(
                    "%s - failure (%s)", report.report_id, report.failure_reason
                )
                self.report_repository.update_by(
                    report.report_id,
                    report_status=ReportStatus.FAILURE.value,
                    failure_reason=report.failure_reason,
                )
                raise RefreshingReportException()
            else:
                self.report_repository.update_from_report(report)
                return report
        elif self._is_report_still_generating(report):
            raise StillGeneratingReportException()
        else:
            raise RefreshingReportException()

    @staticmethod
    def _is_report_failed(report: ReportEntity):
        return report and report.report_status not in AmazonReportStatuses.PENDING

    @staticmethod
    def _is_report_still_generating(report: ReportEntity):
        return report and report.report_status in AmazonReportStatuses.PENDING
