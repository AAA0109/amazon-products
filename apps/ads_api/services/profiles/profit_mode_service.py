from apps.ads_api.adapters.amazon_ads.sponsored_products.keywords_adapter import (
    KeywordsAdapter,
)
from apps.ads_api.adapters.amazon_ads.sponsored_products.targets_adapter import TargetsAdapter
from apps.ads_api.constants import (
    SpReportType,
    DEFAULT_MIN_BID,
    SpState, TARGETS_VALID_STATUSES,
)
from apps.ads_api.entities.amazon_ads.sponsored_products.keywords import KeywordEntity
from apps.ads_api.entities.amazon_ads.sponsored_products.targets import TargetEntity
from apps.ads_api.models import Profile, Keyword, Target, RecentReportData


class ProfitModeService:
    @classmethod
    def turn_on(cls, profile: Profile):
        cls._minimize_bids_for_unproved_keywords(profile)
        cls._minimize_bids_for_unproved_targets(profile)

    @staticmethod
    def _minimize_bids_for_unproved_keywords(profile):
        keywords_adapter = KeywordsAdapter(profile)

        unproven_keywords_ids = (
            RecentReportData.objects.filter(
                campaign__profile=profile,
                report_type=SpReportType.KEYWORD,
                sales=0,
            )
            .order_by("keyword_id")
            .values_list("keyword_id", flat=True)
            .distinct("keyword_id")
        )
        keywords = Keyword.objects.filter(
            campaign__profile=profile,
            bid__gt=DEFAULT_MIN_BID,
            serving_status__in=TARGETS_VALID_STATUSES,
            state=SpState.ENABLED.value,
            keyword_id__in=unproven_keywords_ids,
        )

        keywords_adapter.batch_update(
            [
                KeywordEntity(
                    external_id=keyword.keyword_id,
                    bid=DEFAULT_MIN_BID,
                ).dict(by_alias=True, exclude_none=True)
                for keyword in keywords
            ]
        )

        keywords.update(**{"bid": DEFAULT_MIN_BID})

    @staticmethod
    def _minimize_bids_for_unproved_targets(profile):
        targets_adapter = TargetsAdapter(profile)
        unproven_targets_ids = (
            RecentReportData.objects.filter(
                campaign__profile=profile,
                report_type=SpReportType.KEYWORD,
                sales=0,
            )
            .order_by("target_id")
            .values_list("target_id", flat=True)
            .distinct("target_id")
        )
        targets = Target.objects.filter(
            campaign__profile=profile,
            bid__gt=DEFAULT_MIN_BID,
            serving_status__in=TARGETS_VALID_STATUSES,
            state=SpState.ENABLED.value,
            target_id__in=unproven_targets_ids,
        )

        targets_adapter.batch_update(
            [
                TargetEntity(
                    external_id=target.target_id,
                    bid=DEFAULT_MIN_BID,
                ).dict(by_alias=True, exclude_none=True)
                for target in targets
            ]
        )

        targets.update(**{"bid": DEFAULT_MIN_BID})
