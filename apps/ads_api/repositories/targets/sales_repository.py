from datetime import datetime

from django.db.models import F

from apps.ads_api.interfaces.repositories.sales_calculatable_interface import (
    SalesCalculatableInterface,
)
from apps.ads_api.models import Target


class TagrgetSelesRepository(SalesCalculatableInterface):
    def __init__(self, targets_ids: list[int]):
        self._targets_ids = targets_ids

    def get_sales_for_date(self, date):
        sales = 0
        for target in (
            Target.objects.filter(
                target_id__in=self._targets_ids, campaign__reportdata__date=date
            )
            .prefetch_related("campaign__books", "campaign__books__datebookprice_set")
            .annotate(conversions=F("campaign__reportdata__attributed_conversions_30d"))
            .iterator()
        ):
            book_price = (
                target.campaign.books.first()
                .datebookprice_set.filter(date__lte=datetime.today())
                .order_by("-date")
                .first()
                .price
            )
            sales += book_price * target.conversions
        return sales
