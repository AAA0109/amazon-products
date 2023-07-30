import abc


class ProfilesAdapterInterface(abc.ABC):
    @abc.abstractmethod
    def get_all_profiles(self):
        pass

    @abc.abstractmethod
    def get_all_profiles_iterator(self):
        pass
