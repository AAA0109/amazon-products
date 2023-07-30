import json

from apps.ads_api.constants import (
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


class PlacementPayload(BasePayloadMixin, GeneratePayloadInterface):
    ASSOCIATED_COLUMNS = ["placementClassification"]

    def as_dict(self) -> dict:
        return self._get_payload_dict()

    def _get_payload_dict(self):
        return {
            "startDate": self.report_date_formatted(self._start_date),
            "endDate": self.report_date_formatted(self._end_date),
            "configuration": {
                "adProduct": AdProductTypes.SP_PRODUCTS,
                "groupBy": ["campaign", "campaignPlacement"],
                "columns": self.BASE_COLUMNS + self.ASSOCIATED_COLUMNS,
                "reportTypeId": TypeIdOfReport.SP_CAMPAIGNS,
                "timeUnit": TimeUnitOfReport.DAILY,
                "format": FormatOfReport.GZIP_JSON,
            },
        }
