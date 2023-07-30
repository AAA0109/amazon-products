from django.db.models import Q

from apps.ads_api.constants import (
    AD_GROUP_INVALID_STATUSES,
    CAMPAIGN_VALID_STATUSES,
    SpState,
)
from apps.ads_api.models import AdGroup, Book


class RelatedAdGroupsRepository:
    def retrieve_valid_ad_groups(self, book: Book):
        return (
            AdGroup.objects.filter(
                campaign__serving_status__in=CAMPAIGN_VALID_STATUSES,
                campaign__sponsoring_type="sponsoredProducts",
                state=SpState.ENABLED.value,
                campaign__books__asin=book.asin,
            )
            .exclude(
                Q(serving_status__in=AD_GROUP_INVALID_STATUSES)
                | Q(campaign__campaign_name__contains="-Exact-")
                | Q(campaign__campaign_name__contains="-Product-")
                | Q(campaign__campaign_name__contains="-GP-")
            )
            .select_related("campaign")
            .order_by("ad_group_id")
            .distinct("ad_group_id")
        )
