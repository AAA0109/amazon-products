from abc import ABC, abstractmethod

from apps.ads_api.constants import ServerLocation
from apps.ads_api.entities.amazon_ads.reports import ReportEntity


class FetchReportDetailsInterface(ABC):
    @abstractmethod
    def fetch(
        self, server: ServerLocation, report_id: str, profile_id: int
    ) -> ReportEntity:
        pass
