import json
from datetime import date

from apps.ads_api.constants import (
    AdStatus,
    AdProductTypes,
    TypeIdOfReport,
    TimeUnitOfReport,
    FormatOfReport,
)
from apps.ads_api.interfaces.services.amazon.reports.paylaods.generate_payload_interface import (
    GeneratePayloadInterface,
)
from apps.ads_api.payloads.reports.base_payload import (
    BasePayloadMixin,
)


class TargetPayload(BasePayloadMixin, GeneratePayloadInterface):
    ASSOCIATED_COLUMNS = [
        "adGroupName",
        "adGroupId",
        "keywordId",
        "keyword",
        "targeting",
        "keywordType",
    ]

    def __init__(
        self, start_date: date, end_date: date, ad_status_filter: list[AdStatus]
    ):
        super().__init__(start_date, end_date)
        self._ad_status_filter = ad_status_filter

    def as_dict(self) -> dict:
        return self._get_payload_dict()

    def _get_payload_dict(self):
        return {
            "startDate": self.report_date_formatted(self._start_date),
            "endDate": self.report_date_formatted(self._end_date),
            "configuration": {
                "adProduct": AdProductTypes.SP_PRODUCTS,
                "groupBy": ["targeting"],
                "columns": self.BASE_COLUMNS + self.ASSOCIATED_COLUMNS,
                "filters": [
                    {
                        "field": "keywordType",
                        "values": [
                            "TARGETING_EXPRESSION",
                            "TARGETING_EXPRESSION_PREDEFINED",
                        ],
                    },
                    {"field": "adKeywordStatus", "values": self._ad_status_filter},
                ],
                "reportTypeId": TypeIdOfReport.SP_TARGETING,
                "timeUnit": TimeUnitOfReport.DAILY,
                "format": FormatOfReport.GZIP_JSON,
            },
        }
