from apps.ads_api.entities.amazon_ads.reports import BaseReportDataEntity
from apps.ads_api.models import RecentReportData


class ReportDataEntityConverter:
    @classmethod
    def convert_to_django_model(
        cls, report_data_entity: BaseReportDataEntity, override_fields: dict = None
    ) -> RecentReportData:
        report_data = RecentReportData(**report_data_entity.dict())
        if override_fields:
            for field, v in override_fields.items():
                setattr(report_data, field, v)
        return report_data
