from abc import ABC, abstractmethod


class DownloadReportsInterface(ABC):
    @abstractmethod
    def download(self):
        pass
