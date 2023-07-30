import mock
from mock.mock import MagicMock

from apps.ads_api.services.books.eligibility_service import BookElgibilityService


@mock.patch("apps.ads_api.adapters.amazon_ads.eligibility_adapter.EligibilityAdapter.get_eligibility",
            return_value=True)
def test_eligibility_service_skips_book_update_if_eligibilities_equal(eligibility_adapter_mock):
    book = MagicMock()
    book.save = MagicMock()
    book.eligible = True

    eligibility_service = BookElgibilityService(book)
    eligibility_service.refresh()

    assert book.save.called is False


@mock.patch("apps.ads_api.adapters.amazon_ads.eligibility_adapter.EligibilityAdapter.get_eligibility",
            return_value=True)
def test_eligibility_service_call_book_update_if_eligibilities_are_not_equal(eligibility_adapter_mock):
    book = MagicMock()
    book.save = MagicMock()
    book.eligible = False

    eligibility_service = BookElgibilityService(book)
    eligibility_service.refresh()

    assert book.save.called is True
