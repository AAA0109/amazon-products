from datetime import date

from apps.ads_api.exceptions.ads_api.reports import NoPayloadForGivenReportType
from apps.ads_api.payloads.reports.campaign_payload import (
    CampaignPayload,
)
from apps.ads_api.payloads.reports.keyword_payload import (
    KeywordPayload,
)
from apps.ads_api.payloads.reports.keyword_search_term_payload import (
    KeywordSearchTermPayload,
)
from apps.ads_api.payloads.reports.placement_payload import (
    PlacementPayload,
)
from apps.ads_api.payloads.reports.product_ad_payload import (
    ProductAdPayload,
)
from apps.ads_api.payloads.reports.target_payload import (
    TargetPayload,
)
from apps.ads_api.payloads.reports.target_search_term_payload import (
    TargetQueryPayload,
)

from apps.ads_api.constants import SpReportType, AdStatus


class ReportPayloadFactory:
    def __init__(
        self,
        report_type: SpReportType,
        start_date: date,
        end_date: date,
        ad_status_filter: list[AdStatus] = None,
    ):
        self._ad_status_filter = ad_status_filter
        self._report_type = report_type
        self._start_date = start_date
        self._end_date = end_date

    def create_payload(self):
        if self._report_type == SpReportType.TARGET:
            payload = TargetPayload(
                ad_status_filter=self._ad_status_filter,
                start_date=self._start_date,
                end_date=self._end_date,
            )
        elif self._report_type == SpReportType.TARGET_QUERY:
            payload = TargetQueryPayload(
                start_date=self._start_date,
                end_date=self._end_date,
            )
        elif self._report_type == SpReportType.KEYWORD:
            payload = KeywordPayload(
                ad_status_filter=self._ad_status_filter,
                start_date=self._start_date,
                end_date=self._end_date,
            )
        elif self._report_type == SpReportType.KEYWORD_QUERY:
            payload = KeywordSearchTermPayload(
                start_date=self._start_date,
                end_date=self._end_date,
            )
        elif self._report_type == SpReportType.PLACEMENT:
            payload = PlacementPayload(
                start_date=self._start_date,
                end_date=self._end_date,
            )
        elif self._report_type == SpReportType.PRODUCT_AD:
            payload = ProductAdPayload(
                start_date=self._start_date,
                end_date=self._end_date,
            )
        elif self._report_type == SpReportType.CAMPAIGN:
            payload = CampaignPayload(
                ad_status_filter=self._ad_status_filter,
                start_date=self._start_date,
                end_date=self._end_date,
            )
        else:
            raise NoPayloadForGivenReportType(
                f"There no case for given report type: {self._report_type}"
            )
        return payload
