import abc


class BookPriceRepositoryInterface(abc.ABC):
    @abc.abstractmethod
    def set_book_price_for_date(self, date, price):
        pass

    @abc.abstractmethod
    def get_book_price_for_date(self, date):
        pass

    @abc.abstractmethod
    def get_actual_price(self):
        pass
