import abc


class BudgetCalculatableInteface(abc.ABC):
    @abc.abstractmethod
    def calculate(self):
        pass
