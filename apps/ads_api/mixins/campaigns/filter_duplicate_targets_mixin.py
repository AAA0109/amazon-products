import abc


class FilterDuplicateTargetsMixin:
    def __init__(self):
        self._text_targets = set()

    def _remove_existing_targeted_asins(self):
        if not isinstance(self._text_targets, set):
            raise TypeError(f"Text targets should be of type set, but provided type is {type(self._text_keywords)}")

        existing_targeted_asins = set(self.get_existing_targeted_asins())
        self._text_targets -= existing_targeted_asins

    @abc.abstractmethod
    def get_existing_targeted_asins(self):
        pass

