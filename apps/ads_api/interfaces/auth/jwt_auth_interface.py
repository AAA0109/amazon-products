from abc import ABC, abstractmethod


class JWTAuthInterface(ABC):
    @abstractmethod
    def get_access_token(self):
        pass

    @abstractmethod
    def refresh_access_token(self):
        pass
