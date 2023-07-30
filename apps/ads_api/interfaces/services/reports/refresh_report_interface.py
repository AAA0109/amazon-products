from abc import ABC, abstractmethod

from apps.ads_api.constants import ServerLocation


class RefreshReportInterface(ABC):
    @abstractmethod
    def refresh(self, server: ServerLocation, report_id: str, profile_id: int):
        pass
