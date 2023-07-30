import logging
from collections import defaultdict

from apps.ads_api.adapters.amazon_ads.sponsored_products.negative_targets_adapter import (
    NegativeTargetsAdapter,
)
from apps.ads_api.constants import SpState
from apps.ads_api.entities.amazon_ads.sponsored_products.negative_target import (
    Expression,
    NegativeTargetEntity,
)
from apps.ads_api.models import Book, Target
from apps.ads_api.repositories.book.releated_ad_groups_repository import (
    RelatedAdGroupsRepository,
)

_logger = logging.getLogger(__name__)


class FillWithNegativeTargetsService:
    def __init__(self, book: Book) -> None:
        self.book = book
        self.book_ad_groups = self._retrieve_ad_groups()

    def fill_with_negatives(
        self,
        text_negatives: list[str],
        predicate_type: str,
    ):
        _logger.info(
            "Params: predicate_type=%s, book=%s, given negatives count: %s",
            predicate_type,
            self.book,
            len(text_negatives),
        )
        adapter = NegativeTargetsAdapter(self.book.profile)
        existing_negatives = self._retrieve_existing_negatives()

        ad_group_id2existing_negatives_text_list_map = defaultdict(list)
        _logger.info(
            "Retrieved negative targets(count: %s) for profile %s: %s",
            len(existing_negatives),
            self.book.profile,
            existing_negatives,
        )

        for negative in existing_negatives:
            ad_group_id2existing_negatives_text_list_map[negative.ad_group_id].append(
                negative.resolved_expression_text
            )
        _logger.info("Ad group to targets text map: %s", ad_group_id2existing_negatives_text_list_map)

        negatives_to_create: list[dict] = []
        for text in text_negatives:
            for ad_group in self.book_ad_groups:
                if text not in ad_group_id2existing_negatives_text_list_map[ad_group]:
                    keyword_entity = NegativeTargetEntity(
                        campaign_id=ad_group.campaign.campaign_id_amazon,
                        ad_group_id=ad_group.ad_group_id,
                        expression=[
                            Expression(
                                type=predicate_type,
                                value=text,
                            )
                        ],
                        state=SpState.ENABLED,
                    )
                    negatives_to_create.append(keyword_entity.dict(exclude_none=True, by_alias=True))
        _logger.info(
            "Negative targets to create(count: %s): %s", len(negatives_to_create), negatives_to_create
        )

        return adapter.batch_create(negatives_to_create)

    def _retrieve_existing_negatives(self):
        return Target.objects.filter(
            keyword_type="Negative",
            state=SpState.ENABLED.value,
            ad_group_id__in=self.book_ad_groups.values_list("ad_group_id", flat=True),
        )

    def _retrieve_ad_groups(self):
        repository = RelatedAdGroupsRepository()
        ad_groups = repository.retrieve_valid_ad_groups(self.book)
        ad_groups = ad_groups.exclude(
            campaign__campaign_purpose__in=["Exact", "Broad", "Product-Comp", "Product-Own", "GP"],
        )
        _logger.info("Ad groups retrieved(%s): %s", len(ad_groups), ad_groups)
        return ad_groups
