import logging
from datetime import datetime, timedelta

from apps.ads_api.constants import DEFAULT_BOOK_PRICE
from apps.ads_api.entities.amazon_ads.reports import BaseReportDataEntity
from apps.ads_api.interfaces.repositories.report_data_repository_interface import (
    ReportDataInterface,
)
from apps.ads_api.models import Campaign, RecentReportData, ReportData

_logger = logging.getLogger(__name__)


class ReportDataRepository(ReportDataInterface):
    def create_or_update(self, report_data: BaseReportDataEntity):
        campaign = Campaign.objects.filter(
            campaign_id_amazon=report_data.campaign_id
        ).first()
        filter_fields = {
            "ad_id": report_data.ad_id,
            "keyword_id": report_data.keyword_id,
            "target_id": report_data.target_id,
            "asin": report_data.asin,
            "query": report_data.query,
            "placement": report_data.placement,
            "campaign": campaign,
            "date": report_data.date,
            "report_type": report_data.report_type,
        }
        try:
            report_to_save = RecentReportData.objects.get(**filter_fields)
        except RecentReportData.MultipleObjectsReturned:
            _logger.warning("Multiple object returned")
            report_to_save = self._get_first_and_delete_dublicates(filter_fields)
        except RecentReportData.DoesNotExist:
            report_to_save = RecentReportData(**filter_fields)

        report_to_save.ad_group_name = report_data.ad_group_name
        report_to_save.ad_group_id = report_data.ad_group_id
        report_to_save.keyword_text = report_data.keyword_text
        report_to_save.match_type = report_data.match_type
        report_to_save.target_expression = report_data.target_expression
        report_to_save.target_text = report_data.target_text
        report_to_save.target_type = report_data.target_type
        report_to_save.impressions = report_data.impressions
        report_to_save.clicks = report_data.clicks
        report_to_save.spend = report_data.spend
        report_to_save.sales = self._recalculate_sales(report_data)
        report_to_save.orders = report_data.orders
        report_to_save.kenp_royalties = report_data.kenp_royalties
        report_to_save.attributed_conversions_30d = (
            report_data.attributed_conversions_30d
        )
        report_to_save.save()

    @staticmethod
    def _get_first_and_delete_dublicates(filter_fields: dict) -> RecentReportData:
        dublicated_reports = RecentReportData.objects.filter(**filter_fields).order_by(
            "id"
        )

        ids = list(dublicated_reports.values_list("pk", flat=True))
        _logger.warning("Dublcicates ids are %s", ids)

        report_to_save = dublicated_reports.first()

        for report_to_delete in dublicated_reports[1:]:
            id_ = report_to_delete.id
            report_to_delete.delete()
            _logger.warning("Dublcicate with id %s is deleted", id_)

        return report_to_save

    @staticmethod
    def _recalculate_sales(report_data: BaseReportDataEntity):
        identifier = "keyword_id" if report_data.keyword_id else "target_id"
        keyword_id = f"{identifier[:-3]}__{identifier}"
        try:
            book_price = (
                Campaign.objects.filter(
                    **{keyword_id: getattr(report_data, identifier)}
                )
                .first()
                .books.first()
                .datebookprice_set.filter(date__lte=datetime.today())
                .order_by("-date")
                .first()
                .price
            )
        except AttributeError:
            book_price = DEFAULT_BOOK_PRICE
        sales = float(book_price) * report_data.attributed_conversions_30d

        if report_data.sales > sales:
            sales = report_data.sales
        return sales

    @classmethod
    def create_from_kwargs(cls, **kwargs):
        return RecentReportData.objects.create(**kwargs)

    @classmethod
    def batch_save_as_recent(
        cls, reports_data: list[ReportData] = None, batch_size=100_000
    ):
        to_save = []
        counter = 0
        if not reports_data:
            date = datetime.today() - timedelta(days=90)
            reports_data = ReportData.objects.filter(
                updated_at__gt=date, campaign__profile__managed=True
            ).iterator(batch_size)

            print(
                ReportData.objects.filter(
                    updated_at__gt=date, campaign__profile__managed=True
                ).count()
            )

        for report_data in reports_data:
            recent_report_data = RecentReportData()
            cls._equalize_two_report_data_objects(recent_report_data, report_data)
            to_save.append(recent_report_data)

            counter += 1

            if counter % batch_size == 0:
                RecentReportData.objects.bulk_create(to_save, batch_size=batch_size)
                to_save.clear()
                print(f"{counter} saved")

        RecentReportData.objects.bulk_create(to_save, batch_size=batch_size)

    @classmethod
    def transfere_90_days_recent_report_data_to_report_data(cls, batch_size=10_000):
        counter = 0
        date = datetime.today() - timedelta(days=90)
        old_report_data = RecentReportData.objects.filter(date__lte=date)
        to_save = []
        for old_report_data in old_report_data.iterator():
            report_data = ReportData()
            cls._equalize_two_report_data_objects(report_data, old_report_data)
            to_save.append(old_report_data)

            counter += 1

            if counter % batch_size == 0:
                ReportData.objects.bulk_create(
                    to_save, batch_size=batch_size, ignore_conflicts=True
                )
                to_save.clear()
                print(f"{counter} saved")

        ReportData.objects.bulk_create(
            to_save, batch_size=batch_size, ignore_conflicts=True
        )
        old_report_data.delete()

    @classmethod
    def _equalize_two_report_data_objects(cls, to_report_data, from_report_data):
        to_report_data.created_at = from_report_data.created_at
        to_report_data.updated_at = datetime.now()
        to_report_data.campaign = from_report_data.campaign
        to_report_data.date = from_report_data.date
        to_report_data.report_type = from_report_data.report_type
        to_report_data.impressions = from_report_data.impressions
        to_report_data.clicks = from_report_data.clicks
        to_report_data.spend = from_report_data.spend
        to_report_data.sales = from_report_data.sales
        to_report_data.orders = from_report_data.orders
        to_report_data.kenp_royalties = from_report_data.kenp_royalties
        to_report_data.placement = from_report_data.placement
        to_report_data.ad_id = from_report_data.ad_id
        to_report_data.ad_group_id = from_report_data.ad_group_id
        to_report_data.ad_group_name = from_report_data.ad_group_name
        to_report_data.keyword_id = from_report_data.keyword_id
        to_report_data.target_id = from_report_data.target_id
        to_report_data.keyword_text = from_report_data.keyword_text
        to_report_data.query = from_report_data.query
        to_report_data.match_type = from_report_data.match_type
        to_report_data.asin = from_report_data.asin
        to_report_data.target_expression = from_report_data.target_expression
        to_report_data.target_text = from_report_data.target_text
        to_report_data.target_type = from_report_data.target_type
        to_report_data.units_sold_14d = from_report_data.units_sold_14d
        to_report_data.attributed_conversions_30d = (
            from_report_data.attributed_conversions_30d
        )
