from abc import ABC, abstractmethod

from apps.ads_api.constants import ServerLocation, SpReportType
from apps.ads_api.entities.amazon_ads.reports import ReportEntity


class DowloadReportInterface(ABC):
    @abstractmethod
    def download(self, report: ReportEntity):
        pass
