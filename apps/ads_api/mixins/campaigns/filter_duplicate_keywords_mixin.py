import abc


class FilterDuplicateKeywordsMixin:
    def __init__(self):
        self._text_keywords = set()

    def _remove_existing_keywords(self):
        if not isinstance(self._text_keywords, set):
            raise TypeError(f"Text keywords should be of type set, but provided type is {type(self._text_keywords)}")

        existing_keywords = set(self.get_existing_keywords_text())
        self._text_keywords -= existing_keywords

    @abc.abstractmethod
    def get_existing_keywords_text(self):
        pass

