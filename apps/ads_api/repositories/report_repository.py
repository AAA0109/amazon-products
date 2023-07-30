import logging

from apps.ads_api.entities.amazon_ads.reports import ReportEntity
from apps.ads_api.interfaces.repositories.report_repository_interface import (
    ReportRepositoryInterface,
)
from apps.ads_api.models import Report


_logger = logging.getLogger(__name__)


class ReportRepository(ReportRepositoryInterface):
    @classmethod
    def is_report_exists(cls, date, profile_id, report_type) -> bool:
        return Report.objects.filter(
            profile_id=profile_id,
            report_type=report_type,
            report_for_date=date,
        ).exists()

    def update_by(self, report_id: str, **kwargs):
        Report.objects.filter(report_id=report_id).update(**kwargs)

    @classmethod
    def update_from_report(cls, report: ReportEntity):
        try:
            stored_report = Report.objects.get(report_id=report.report_id)
            stored_report.report_location = report.report_location
            stored_report.report_status = report.report_status
            stored_report.report_size = report.report_size
            stored_report.failure_reason = (
                report.failure_reason if report.failure_reason else ""
            )
            stored_report.save()
        except Report.DoesNotExist as e:
            _logger.error("%s, report_id=%s", e, report.report_id)

    @classmethod
    def create_from_report(cls, report: ReportEntity):
        Report.objects.create(
            **{
                "report_id": report.report_id,
                "profile_id": report.profile_id,
                "report_type": report.report_type,
                "report_status": report.report_status,
                "start_date": report.start_date,
                "end_date": report.end_date,
                "report_server": report.report_server,
            }
        )

    @classmethod
    def update_or_create_from_report(cls, report: ReportEntity):
        report_size = report.report_size if report.report_size else 0
        report_location = report.report_location if report.report_location else ""

        Report.objects.update_or_create(
            profile_id=report.profile_id,
            report_type=report.report_type,
            start_date=report.start_date,
            end_date=report.end_date,
            defaults={
                "report_id": report.report_id,
                "report_server": report.report_server,
                "report_status": report.report_status,
                "report_size": report_size,
                "report_location": report_location,
            },
        )

    @classmethod
    def create_from_dict(cls, **kwargs) -> Report:
        return Report.objects.create(**kwargs)

    @classmethod
    def remove(cls, report_id: str):
        Report.objects.filter(report_id=report_id).delete()
