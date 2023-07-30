from datetime import datetime

from django.db.models import F

from apps.ads_api.interfaces.repositories.sales_calculatable_interface import (
    SalesCalculatableInterface,
)
from apps.ads_api.models import Keyword


class KeywordSelesRepository(SalesCalculatableInterface):
    def __init__(self, keywords_ids: list[int]):
        self._keywords_ids = keywords_ids

    def get_sales_for_date(self, date):
        sales = 0
        for keyword in (
            Keyword.objects.filter(
                keyword_id__in=self._keywords_ids, campaign__reportdata__date=date
            )
            .prefetch_related("campaign__books", "campaign__books__datebookprice_set")
            .annotate(conversions=F("campaign__reportdata__attributed_conversions_30d"))
            .iterator()
        ):
            book_price = (
                keyword.campaign.books.first()
                .datebookprice_set.filter(date__lte=datetime.today())
                .order_by("-date")
                .first()
                .price
            )
            sales += book_price * keyword.conversions
        return sales
