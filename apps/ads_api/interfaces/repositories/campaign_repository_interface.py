from abc import ABC, abstractmethod
from datetime import datetime


class CampaignRepositoryInterface(ABC):
    @abstractmethod
    def exists_by(self, **kwargs):
        pass
