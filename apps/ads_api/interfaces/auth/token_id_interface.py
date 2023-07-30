import abc


class TokenIdInterface(abc.ABC):
    @property
    @abc.abstractmethod
    def token_id(self):
        pass
