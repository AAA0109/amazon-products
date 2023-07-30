import logging
from datetime import date
from typing import Optional

from pydantic import ValidationError

from apps.ads_api.adapters.amazon_ads.base_amazon_ads_adapter import (
    BaseAmazonAdsAdapter,
)
from apps.ads_api.constants import AdStatus, ServerLocation, SpReportType
from apps.ads_api.entities.amazon_ads.reports import ReportEntity
from apps.ads_api.exceptions.ads_api.reports import CreatingReportRequestException
from apps.ads_api.factories.report_payload_factory import ReportPayloadFactory

_logger = logging.getLogger(__name__)


class ReportsAdapter(BaseAmazonAdsAdapter):
    def __init__(
        self,
        report_type: SpReportType,
        server: ServerLocation,
        start_date: date,
        end_date: date,
        ad_status_filter: Optional[list[AdStatus]] = None,
    ):
        super().__init__(server)
        self._end_date = end_date
        self._start_date = start_date
        self._ad_status_filter = ad_status_filter or list(AdStatus.__members__.values())
        self._report_type = report_type

    def create_report_request_for_profile(self, profile_id: int) -> ReportEntity:
        payload_factory = ReportPayloadFactory(
            report_type=self._report_type,
            ad_status_filter=self._ad_status_filter,
            start_date=self._start_date,
            end_date=self._end_date,
        )

        url = f"/reporting/reports"
        headers = {
            "Amazon-Advertising-API-Scope": str(profile_id),
            "Content-Type": "application/json",
        }
        payload = payload_factory.create_payload()
        payload = payload.as_dict()

        try:
            response = self.send_request(url=url, method="POST", extra_headers=headers, body=payload)
        except Exception as e:
            raise CreatingReportRequestException() from e

        if response is None:
            _logger.error(
                "No response received. Profile: %s, Payload: %s",
                str(profile_id),
                payload,
            )
            raise CreatingReportRequestException("No response received from the server.")

        try:
            report = ReportEntity.parse_obj(response.json())
            report.report_type = self._report_type
            report.report_server = self.server
            report.profile_id = profile_id
        except ValidationError as e:
            raise CreatingReportRequestException() from e

        return report

    def get_generation_status(self, report_id: str):
        pass

    def download_report(self, ready_report_url: str, report_type: SpReportType):
        pass
