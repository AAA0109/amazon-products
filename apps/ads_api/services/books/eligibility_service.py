from apps.ads_api.adapters.amazon_ads.eligibility_adapter import EligibilityAdapter
from apps.ads_api.exceptions.ads_api.product_eligibility import (
    EligibilityRetrievalException,
)
from apps.ads_api.models import Book


class BookElgibilityService:
    def __init__(self, book: Book):
        self._book = book

    def refresh(self):
        eligibility_adapter = EligibilityAdapter(self._book)
        try:
            eligibility = eligibility_adapter.get_eligibility()
        except EligibilityRetrievalException:
            pass
        else:
            if eligibility != self._book.eligible:
                self._book.eligible = eligibility
                self._book.save()
