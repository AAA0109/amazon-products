import logging

from apps.ads_api.repositories.keywords.spends_repository import KeywordsSpendsRepository
from apps.ads_api.repositories.targets.spends_repository import TargetsSpendsRepository


_logger = logging.getLogger(__name__)


class SpendsRepositoryMapper:
    def __init__(self, keywords_list: list[dict]):
        self._keywords_list = keywords_list

    def get_repository(self):
        if "keyword_id" in self._keywords_list[0].keys():
            keywords_ids = self._keywords_list.values_list("keyword_id", flat=True)
            repo = KeywordsSpendsRepository(keywords_ids)
        elif "target_id" in self._keywords_list[0].keys():
            targets_ids = self._keywords_list.values_list("target_id", flat=True)
            repo = TargetsSpendsRepository(targets_ids)
        else:
            _logger.error("Not implemented error for %s", type(self._keywords_list[0]))
            raise NotImplementedError()
        return repo
