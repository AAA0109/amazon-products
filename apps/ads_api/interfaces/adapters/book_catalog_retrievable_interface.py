import abc


class BookCatalogRetrievableInterface(abc.ABC):
    @abc.abstractmethod
    def retrieve_book_catalog(self):
        pass
