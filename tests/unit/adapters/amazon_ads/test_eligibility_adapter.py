import mock
import pytest
from mock.mock import MagicMock

from apps.ads_api.adapters.amazon_ads.eligibility_adapter import EligibilityAdapter
from apps.ads_api.exceptions.ads_api.product_eligibility import EligibilityRetrievalException


@pytest.fixture
def sample_eligibility_response():
    return {
        'productResponseList': [
            {
                'eligibilityStatusList': [],
                'overallStatus': 'ELIGIBLE',
                'productDetails': {'asin': 'testasin', 'sku': None}
            }
        ],
        'requestId': '2efa5223-f645-45d1-9918-4be9d79b29f3'
    }


@mock.patch("apps.ads_api.adapters.amazon_ads.base_amazon_ads_adapter.BaseAmazonAdsAdapter.send_request")
def test_eligibility_adapter_raises_error_for_null_response(request_mock):
    book = MagicMock(asin="test_asin")
    eligibility_adapter = EligibilityAdapter(book)
    with pytest.raises(EligibilityRetrievalException):
        eligibility_adapter.get_eligibility()


@mock.patch("apps.ads_api.adapters.amazon_ads.base_amazon_ads_adapter.BaseAmazonAdsAdapter.send_request", return_value=MagicMock(status_code=400))
def test_eligibility_adapter_raises_error_for_response_error_status_code(request_mock):
    book = MagicMock(asin="test_asin")
    eligibility_adapter = EligibilityAdapter(book)
    with pytest.raises(EligibilityRetrievalException):
        eligibility_adapter.get_eligibility()


@mock.patch("apps.ads_api.adapters.amazon_ads.base_amazon_ads_adapter.BaseAmazonAdsAdapter.send_request")
def test_eligibility_adapter_returns_updated_eligibility(request_mock, sample_eligibility_response):
    response = MagicMock()
    response.json = MagicMock(return_value=sample_eligibility_response)
    response.status_code = 200

    request_mock.return_value = response

    book = MagicMock(asin="test_asin")
    eligibility_adapter = EligibilityAdapter(book)

    eligibility = eligibility_adapter.get_eligibility()
    assert eligibility is True
