import logging

from pydantic import ValidationError

from apps.ads_api.adapters.amazon_ads.base_amazon_ads_adapter import (
    BaseAmazonAdsAdapter,
)
from apps.ads_api.entities.amazon_ads.reports import ReportEntity

_logger = logging.getLogger(__name__)


class FetchReportDetailsService(BaseAmazonAdsAdapter):
    def fetch(self, report_id: str, profile_id: int) -> ReportEntity:
        headers = {"Amazon-Advertising-API-Scope": str(profile_id)}
        response = self.send_request(
            f"/reporting/reports/{report_id}", extra_headers=headers
        )
        if response:
            try:
                report = ReportEntity.parse_obj(response.json())
            except ValidationError as e:
                _logger.error(e.json())
            else:
                return report
        else:
            _logger.error(
                "Failed to fetch reports details on server: %s, report_id: %s",
                report_id,
                self.server,
            )
