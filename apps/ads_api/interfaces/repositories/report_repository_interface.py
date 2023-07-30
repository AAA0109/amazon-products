from abc import ABC, abstractmethod
from datetime import datetime

from apps.ads_api.entities.amazon_ads.reports import ReportEntity, ReportListEntity


class ReportRepositoryInterface(ABC):
    @abstractmethod
    def is_report_exists(self, date, profile_id, report_type):
        pass

    @abstractmethod
    def update_by(self, report_id: str, **kwargs):
        pass

    @abstractmethod
    def update_from_report(self, report: ReportEntity):
        pass

    @abstractmethod
    def create_from_report(self, report: ReportEntity):
        pass

    @abstractmethod
    def update_or_create_from_report(self, report: ReportEntity):
        pass
