import abc


class SalesCalculatableInterface(abc.ABC):
    @abc.abstractmethod
    def get_sales_for_date(self, date):
        pass
