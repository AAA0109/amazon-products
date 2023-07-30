import logging

from django.core.exceptions import MultipleObjectsReturned

from apps.ads_api.adapters.amazon_ads.reports_adapter import ReportsAdapter
from apps.ads_api.exceptions.ads_api.reports import CreatingReportRequestException
from apps.ads_api.models import Report
from apps.ads_api.repositories.report_repository import ReportRepository


_logger = logging.getLogger(__name__)


class RequestReportByIdService:
    @staticmethod
    def request(report_ids: list[str]):
        report_repository = ReportRepository()

        for report_type, date, profile_id, report_server in (
            Report.objects.filter(report_id__in=report_ids)
            .values_list(
                "report_type", "report_for_date", "profile_id", "report_server"
            )
            .iterator()
        ):
            report_adapter = ReportsAdapter(report_type=report_type, report_date=date)
            try:
                report = report_adapter.create_report_request_for_profile(
                    server_location=report_server, profile_id=profile_id
                )
            except CreatingReportRequestException:
                _logger.error(
                    "Got creating report error. Details: profile_id: %s, report_type: %s, date: %s",
                    profile_id,
                    report_type,
                    date,
                )
                continue

            try:
                report_repository.update_or_create_from_report(report)
            except MultipleObjectsReturned as e:
                _logger.error(
                    "Error for %s, %s, %s, %s",
                    report.report_type,
                    report.report_for_date,
                    report.profile_id,
                    e,
                )
