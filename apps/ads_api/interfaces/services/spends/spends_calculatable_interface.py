import abc


class SpendsCalculatableInterface(abc.ABC):
    @abc.abstractmethod
    def calculate_spends(self) -> float:
        pass
