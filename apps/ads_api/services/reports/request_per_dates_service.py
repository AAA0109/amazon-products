import logging
from datetime import date, datetime
from time import sleep
from typing import Optional

from django.core.exceptions import MultipleObjectsReturned

from apps.ads_api.adapters.amazon_ads.reports_adapter import ReportsAdapter
from apps.ads_api.constants import SP_REPORT_TYPES, AdStatus, SpReportType
from apps.ads_api.exceptions.ads_api.reports import CreatingReportRequestException
from apps.ads_api.interfaces.services.reports.request_per_dates_intefrace import (
    RequestPerDatesInterface,
)
from apps.ads_api.repositories.profile_repository import ProfileRepository
from apps.ads_api.repositories.report_repository import ReportRepository

_logger = logging.getLogger(__name__)


class RequestPerDatesService(RequestPerDatesInterface):
    def __init__(
        self,
        start_date: datetime,
        end_date: datetime,
        managed_profiles_ids: list[int],
        report_types: list[SpReportType] = SP_REPORT_TYPES,
        requests_interval: float = 0.5,
        ad_status_filter: Optional[list[AdStatus]] = None,
    ):
        self._start_date = start_date
        self._end_date = end_date
        self._profile_repository = ProfileRepository()
        self._report_repository = ReportRepository()
        self._managed_profiles_ids = (
            managed_profiles_ids if managed_profiles_ids else []
        )
        self._requests_interval = requests_interval
        self._report_types = report_types
        self._ad_status_filter = ad_status_filter

    def request(self):
        _logger.info(
            "Requesting reports for profiles with profile_id in %s",
            self._managed_profiles_ids,
        )
        for profile_id in self._managed_profiles_ids:
            server = self._profile_repository.get_server_by_profile_id(
                profile_id=profile_id
            )
            if not server:
                continue

            for report_type in self._report_types:
                report_adapter = ReportsAdapter(
                    report_type=report_type,
                    server=server,
                    start_date=self._start_date,
                    end_date=self._end_date,
                    ad_status_filter=self._ad_status_filter,
                )
                try:
                    report = report_adapter.create_report_request_for_profile(
                        profile_id=profile_id
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
                    self._report_repository.update_or_create_from_report(report)
                except MultipleObjectsReturned as e:
                    _logger.error(
                        "Error for %s, %s, %s, %s",
                        report.report_type,
                        report.start_date,
                        report.end_date,
                        report.profile_id,
                        e,
                    )

                sleep(self._requests_interval)

            _logger.info(
                "Reports were updated from %s to %s, profile id - %s",
                self._start_date.date(),
                self._end_date.date(),
                profile_id,
            )
