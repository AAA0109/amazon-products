import logging
from collections import defaultdict

from django.db.models import Q

from apps.ads_api.adapters.amazon_ads.sponsored_products.negative_keywords_adapter import (
    NegativeKeywordsAdapter,
)
from apps.ads_api.constants import (
    AD_GROUP_INVALID_STATUSES,
    CAMPAIGN_VALID_STATUSES,
    NegativeMatchType,
    SpState,
)
from apps.ads_api.entities.amazon_ads.sponsored_products.negative_keyword import (
    NegativeKeywordEntity,
)
from apps.ads_api.exceptions.ads_api.base import ObjectNotCreatedError
from apps.ads_api.models import AdGroup, Book, Keyword
from apps.ads_api.repositories.book.releated_ad_groups_repository import (
    RelatedAdGroupsRepository,
)

_logger = logging.getLogger(__name__)


class FillWithNegativeKeywordsService:
    def __init__(self, book: Book) -> None:
        self.book = book
        self.book_ad_groups = self._retrieve_ad_groups()

    def fill_with_negatives(
        self,
        text_negatives: list[str],
        match_type: str,
    ):
        _logger.info(
            "Params: match_type=%s, book=%s, given negatives count: %s",
            match_type,
            self.book,
            len(text_negatives),
        )
        adapter = NegativeKeywordsAdapter(self.book.profile)
        existing_negatives = self._retrieve_existing_negatives()
        _logger.info(
            "Retrieved negative keywords(count: %s) for profile %s: %s",
            len(existing_negatives),
            self.book.profile,
            existing_negatives,
        )

        ad_group_id2existing_negatives_text_list_map: dict[str, list[str]] = defaultdict(list)

        for negative in existing_negatives:
            ad_group_id2existing_negatives_text_list_map[negative.ad_group_id].append(negative.keyword_text)
        _logger.info("Ad group to keywords text map: %s", ad_group_id2existing_negatives_text_list_map)

        negatives_to_create: list[dict] = []
        for text in text_negatives:
            for ad_group in self.book_ad_groups:
                if text not in ad_group_id2existing_negatives_text_list_map[ad_group]:
                    keyword_entity = NegativeKeywordEntity(
                        campaign_id=ad_group.campaign.campaign_id_amazon,
                        ad_group_id=ad_group.ad_group_id,
                        match_type=self._resolve_match_type(match_type),
                        keyword_text=text,
                        state=SpState.ENABLED,
                    )
                    negatives_to_create.append(keyword_entity.dict(exclude_none=True, by_alias=True))
        _logger.info(
            "Negative keywords to create(count: %s): %s", len(negatives_to_create), negatives_to_create
        )

        return adapter.batch_create(negatives_to_create)

    def _resolve_match_type(self, match_type: str):
        if match_type == "exact":
            match_type = NegativeMatchType.EXACT
        elif match_type == "phrase":
            match_type = NegativeMatchType.PHRASE
        else:
            _logger.error("Invalid match type: %s passed to negatives function", match_type)
            raise TypeError(
                (
                    f"Invalid match type: {match_type}. "
                    f"Allowed match types {[NegativeMatchType.EXACT, NegativeMatchType.PHRASE, ]}"
                )
            )
        return match_type

    def _retrieve_existing_negatives(self):
        return Keyword.objects.filter(
            keyword_type="Negative",
            state=SpState.ENABLED.value,
            ad_group_id__in=self.book_ad_groups.values_list("ad_group_id", flat=True),
        )

    def _retrieve_ad_groups(self):
        repository = RelatedAdGroupsRepository()
        ad_groups = repository.retrieve_valid_ad_groups(self.book)
        ad_groups = ad_groups.exclude(
            campaign__campaign_purpose__in=["Exact", "Product", "GP", "Cat-Research"],
        )
        _logger.info("Ad groups retrieved(%s): %s", len(ad_groups), ad_groups)
        return ad_groups
