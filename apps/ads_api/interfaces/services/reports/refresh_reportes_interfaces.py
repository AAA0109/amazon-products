from abc import ABC, abstractmethod


class RefreshReportsInterface(ABC):
    @abstractmethod
    def refresh(self):
        pass
