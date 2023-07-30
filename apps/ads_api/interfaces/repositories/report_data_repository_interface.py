from abc import ABC, abstractmethod


class ReportDataInterface(ABC):
    @abstractmethod
    def create_or_update(self, report_data):
        pass
