from abc import ABC, abstractmethod


class RequestPerDatesInterface(ABC):
    @abstractmethod
    def request(self):
        pass
