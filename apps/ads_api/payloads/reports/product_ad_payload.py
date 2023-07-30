import json

from apps.ads_api.constants import (
    TypeIdOfReport,
    AdProductTypes,
    FormatOfReport,
    TimeUnitOfReport,
)
from apps.ads_api.interfaces.services.amazon.reports.paylaods.generate_payload_interface import (
    GeneratePayloadInterface,
)
from apps.ads_api.payloads.reports.base_payload import (
    BasePayloadMixin,
)


class ProductAdPayload(BasePayloadMixin, GeneratePayloadInterface):
    ASSOCIATED_COLUMNS = ["adId", "adGroupName", "adGroupId", "advertisedAsin"]

    def as_dict(self) -> dict:
        return self._get_payload_dict()

    def _get_payload_dict(self):
        return {
            "startDate": self.report_date_formatted(self._start_date),
            "endDate": self.report_date_formatted(self._end_date),
            "configuration": {
                "reportTypeId": TypeIdOfReport.SP_ADVERTISED_PRODUCT,
                "columns": self.BASE_COLUMNS + self.ASSOCIATED_COLUMNS,
                "adProduct": AdProductTypes.SP_PRODUCTS,
                "format": FormatOfReport.GZIP_JSON,
                "groupBy": ["advertiser"],
                "timeUnit": TimeUnitOfReport.DAILY,
            },
        }
