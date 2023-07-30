import gzip
import json
import logging

import requests
from pydantic import parse_obj_as, ValidationError

from apps.ads_api.constants import SpReportType
from apps.ads_api.entities.amazon_ads.reports import (
    CampaignsReportDataEntity,
    KeywordQueryReportDataEntity,
    KeywordsReportDataEntity,
    PlacementsReportDataEntity,
    ProductAdsReportData,
    TargetQueryReportDataEntity,
    TargetsReportData,
    BaseReportDataEntity,
    ReportEntity,
)
from apps.ads_api.exceptions.ads_api.reports import NoReportDataReturned
from apps.ads_api.interfaces.services.amazon.reports.download_report_interface import (
    DowloadReportInterface,
)
from apps.utils.gzip import GzipExtracter

_logger = logging.getLogger(__name__)


class DownloadReportService(DowloadReportInterface):
    def download(
        self,
        report: ReportEntity,
    ) -> list[BaseReportDataEntity]:
        response = requests.get(report.report_location)
        if not response:
            raise NoReportDataReturned()

        gzip_extracter = GzipExtracter(response)

        try:
            response_data = gzip_extracter.extract()
        except gzip.BadGzipFile:
            response_data = json.loads(response.text)

        ReportDataEntity = self._resolve_entity_class(report_type=report.report_type)

        try:
            report_data_list = parse_obj_as(list[ReportDataEntity], response_data)
        except ValidationError as e:
            _logger.error(e.json())
            raise NoReportDataReturned()

        return report_data_list

    @staticmethod
    def _resolve_entity_class(report_type: SpReportType):
        classes = {
            SpReportType.TARGET: TargetsReportData,
            SpReportType.KEYWORD: KeywordsReportDataEntity,
            SpReportType.CAMPAIGN: CampaignsReportDataEntity,
            SpReportType.PLACEMENT: PlacementsReportDataEntity,
            SpReportType.PRODUCT_AD: ProductAdsReportData,
            SpReportType.KEYWORD_QUERY: KeywordQueryReportDataEntity,
            SpReportType.TARGET_QUERY: TargetQueryReportDataEntity,
        }
        try:
            report_data_class = classes[report_type]
        except KeyError:
            _logger.error(
                "No class available for given report type - %s, available types: %s",
                report_type,
                classes.keys(),
            )
        else:
            return report_data_class

    @staticmethod
    def _get_headers(profile_id):
        return {"Amazon-Advertising-API-Scope": str(profile_id)}
