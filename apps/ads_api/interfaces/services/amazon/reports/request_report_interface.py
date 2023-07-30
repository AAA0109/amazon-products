from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from apps.ads_api.constants import ServerLocation, SpReportType, AdStatus
from apps.ads_api.entities.amazon_ads.reports import ReportEntity


class ReuestReportService(ABC):
    @abstractmethod
    def request(
        self,
        server: ServerLocation,
        profile_id: int,
        report_date: datetime,
        report_type: SpReportType,
        state_filter: Optional[AdStatus] = AdStatus.ENABLED,
    ) -> ReportEntity:
        pass
