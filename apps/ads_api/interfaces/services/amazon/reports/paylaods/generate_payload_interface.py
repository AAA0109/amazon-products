import abc


class GeneratePayloadInterface(abc.ABC):
    @abc.abstractmethod
    def as_dict(self) -> dict:
        pass
