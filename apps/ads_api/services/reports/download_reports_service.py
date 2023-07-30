import logging
from itertools import groupby
from time import sleep
from typing import Iterable

from apps.ads_api.constants import EMPTY_REPORT_BYTES, ReportStatus, SpReportType
from apps.ads_api.converters.report_data_entity_converter import (
    ReportDataEntityConverter,
)
from apps.ads_api.entities.amazon_ads.reports import BaseReportDataEntity, ReportEntity
from apps.ads_api.exceptions.ads_api.reports import (
    BaseRefreshingReportException,
    EmptyReportDataReturned,
    NoReportDataReturned,
)
from apps.ads_api.interfaces.services.reports.download_reports_interface import (
    DownloadReportsInterface,
)
from apps.ads_api.models import Campaign, RecentReportData
from apps.ads_api.repositories.campaign_repository import CampaignRepository
from apps.ads_api.repositories.report.status_repository import ReportStatusRepository
from apps.ads_api.repositories.report_data_repository import ReportDataRepository
from apps.ads_api.repositories.report_repository import ReportRepository
from apps.ads_api.services.amazon.reports.download_from_amazon_service import (
    DownloadReportService,
)
from apps.ads_api.services.reports.refresh_report_service import RefreshReportService

_logger = logging.getLogger(__name__)


class DownloadReportsService(DownloadReportsInterface):
    def __init__(self):
        self._reports_repository = ReportRepository()
        self._campaigns_repository = CampaignRepository()
        self._report_data_repository = ReportDataRepository()
        self._download_reports_data_service = DownloadReportService()

    def download(self):
        timeout = 5
        retries = 0
        _logger.info("Downloading started")
        reports_to_download_count = ReportStatusRepository.count_by_status(ReportStatus.PENDING)

        while reports_to_download_count > 0 or retries < timeout:
            reports_to_download = ReportStatusRepository.retrieve_reports_to_download_iterator()

            _logger.info("Reports to process: %s", reports_to_download_count)
            for report in reports_to_download:
                try:
                    refreshed_report = self._refresh_report(report)
                except EmptyReportDataReturned:
                    self._reports_repository.update_by(report.report_id, report_status=ReportStatus.EMPTY.value)
                    continue
                except BaseRefreshingReportException:
                    continue

                try:
                    reports_data = self._download_reports_data_service.download(refreshed_report)
                except NoReportDataReturned:
                    self._reports_repository.update_by(
                        report.report_id,
                        report_status=ReportStatus.INTERNAL_FAILURE.value,
                    )
                    continue

                self._save_reports_data(reports_data, refreshed_report)

            reports_to_download_count = ReportStatusRepository.count_by_status(ReportStatus.PENDING)
            if reports_to_download_count > 0:
                sleep(60 * 30)  # 30 minutes

            retries += 1

        _logger.info("sp_process_reports is done")

    @staticmethod
    def _refresh_report(report: ReportEntity) -> ReportEntity:
        refresh_service = RefreshReportService()
        refreshed_report = refresh_service.refresh(report.report_server, report.report_id, report.profile_id)
        if refreshed_report.report_size == EMPTY_REPORT_BYTES:
            raise EmptyReportDataReturned()

        refreshed_report.report_type = report.report_type

        return refreshed_report

    def _save_reports_data(self, reports_data: list[BaseReportDataEntity], report: ReportEntity):
        reports_data_to_save = []
        campaigns_data = {
            campaign["campaign_id_amazon"]: campaign["id"]
            for campaign in Campaign.objects.filter(
                campaign_id_amazon__in={report.campaign_id for report in reports_data}
            ).values("id", "campaign_id_amazon")
        }

        reports_data = sorted(reports_data, key=lambda x: x.campaign_id)
        grouped_data = {
            campaign_external_id: list(report_data)
            for campaign_external_id, report_data in groupby(reports_data, key=lambda x: x.campaign_id)
            if campaign_external_id in campaigns_data
        }

        reports_data_to_save.extend(
            [
                ReportDataEntityConverter.convert_to_django_model(
                    report_data,
                    override_fields={
                        "report_type": report.report_type,
                        "campaign_id_amazon": campaign_external_id,
                        "campaign_id": campaigns_data[campaign_external_id],
                    },
                )
                for campaign_external_id, reports_data in grouped_data.items()
                for report_data in reports_data
                if self._report_has_new_data(report_data)
            ]
        )
        campaign_ids = campaigns_data.values()
        self._delete_existing_report_data(report, campaign_ids)

        RecentReportData.objects.bulk_create(reports_data_to_save)

        self._reports_repository.remove(report.report_id)

    @staticmethod
    def _report_has_new_data(report: BaseReportDataEntity) -> bool:
        """
        Returns True if there's any data greater then zero
        """
        return any(
            field > 0
            for field in (
                report.orders,
                report.sales,
                report.kenp_royalties,
                report.sales,
                report.impressions,
                report.clicks,
            )
        )

    def _delete_existing_report_data(self, report: ReportEntity, campaign_ids: Iterable[int]):
        type_filter, type_exclude_filter = self._map_report_data_type_filter(report)
        if type_filter and type_exclude_filter is None:
            reports_to_delete = RecentReportData.objects.filter(
                date__range=(report.start_date, report.end_date),
                campaign_id__in=campaign_ids,
                **type_filter,
            )
        elif type_exclude_filter and type_filter is None:
            reports_to_delete = RecentReportData.objects.filter(
                date__range=(report.start_date, report.end_date),
                campaign_id__in=campaign_ids,
            ).exclude(**type_exclude_filter)
        else:
            reports_to_delete = RecentReportData.objects.filter(
                date__range=(report.start_date, report.end_date),
                campaign_id__in=campaign_ids,
                **type_filter,
            ).exclude(**type_exclude_filter)
        reports_to_delete.delete()

    @staticmethod
    def _map_report_data_type_filter(report: ReportEntity):
        filters = {
            SpReportType.CAMPAIGN: {
                "filter": {
                    "keyword_id__isnull": True,
                    "placement": "",
                    "ad_id__isnull": True,
                    "target_id__isnull": True,
                    "campaign_id__isnull": False,
                }
            },
            SpReportType.KEYWORD_QUERY: {
                "filter": {
                    "keyword_id__isnull": False,
                },
                "exclude": {
                    "query": "",
                },
            },
            SpReportType.KEYWORD: {
                "filter": {
                    "keyword_id__isnull": False,
                    "query": "",
                }
            },
            SpReportType.PLACEMENT: {
                "exclude": {
                    "placement": "",
                }
            },
            SpReportType.PRODUCT_AD: {"filter": {"ad_id__isnull": False}},
            SpReportType.TARGET_QUERY: {
                "filter": {
                    "target_id__isnull": False,
                },
                "exclude": {
                    "query": "",
                },
            },
            SpReportType.TARGET: {
                "filter": {
                    "target_id__isnull": False,
                    "query": "",
                }
            },
        }
        return filters[report.report_type].get("filter"), filters[report.report_type].get("exclude")
