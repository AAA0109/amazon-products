import abc


class SchedulerInterface(abc.ABC):
    @abc.abstractmethod
    def setup_with_delay_by_location(self):
        pass
