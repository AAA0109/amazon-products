import mock
import pytest
from mock.mock import Mock, PropertyMock
from requests import Response

from apps.ads_api.adapters.amazon_ads.sponsored_products.base_sp_adapter import (
    BaseSponsoredProductsAdapter,
)


@pytest.fixture
def sample_error_response():
    return {
        "RESPONSE_DATA_KEY": {
            "error": [
                {
                    "errors": [
                        {
                            "errorType": "duplicateValueError",
                            "errorValue": {
                                "duplicateValueError": {
                                    "cause": {
                                        "location": "$.campaigns[0].name",
                                        "trigger": "LYSOJFKA5-SP-Product-Own-4-B08L6W13NZ-Kindle",
                                    },
                                    "message": "Campaign with name=LYSOJFKA5-SP-Product-Own-4-B08L6W13NZ-Kindle already exists!",
                                    "reason": "DUPLICATE_VALUE",
                                }
                            },
                        }
                    ],
                    "index": 0,
                }
            ],
            "success": [],
        }
    }


class TestBaseSpAdapter:
    def test_parse_response_retrieves_all_errors(self, sample_error_response):
        BaseSponsoredProductsAdapter.RESPONSE_DATA_KEY = "RESPONSE_DATA_KEY"
        BaseSponsoredProductsAdapter.RESPONSE_DATA_ID = "RESPONSE_DATA_ID"

        response_mock = Mock(spec=Response)
        response_mock.json = lambda: sample_error_response

        success, errors = BaseSponsoredProductsAdapter._parse_response(response_mock)

        assert len(errors) == 1
        assert errors[0]["errorType"] == "duplicateValueError"
