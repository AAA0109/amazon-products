import abc


class AuthenticatableInterface(abc.ABC):
    @property
    @abc.abstractmethod
    def authenticator(self):
        pass
