import abc
from datetime import datetime


class SpendsCalculatableRepositoryInterface(abc.ABC):
    @abc.abstractmethod
    def get_toatal_spends(self):
        pass

    @abc.abstractmethod
    def get_spends_for_date(self, date: datetime):
        pass
