from requests import JSONDecodeError

from apps.ads_api.adapters.amazon_ads.base_amazon_ads_adapter import (
    BaseAmazonAdsAdapter,
)
from apps.ads_api.exceptions.ads_api.product_eligibility import (
    EligibilityRetrievalException,
)
from apps.ads_api.models import Book


class EligibilityAdapter(BaseAmazonAdsAdapter):
    def __init__(self, book: Book):
        super().__init__(book.profile.profile_server)
        self._book = book

    def get_eligibility(self) -> bool:
        url = "/eligibility/product/list"
        body = {
            "addType": "sp",
            "productDetailsList": [
                {
                    "asin": self._book.asin,
                }
            ],
        }
        headers = {
            "Amazon-Advertising-API-Scope": str(self._book.profile.profile_id),
            "Content-Type": "application/json",
        }
        response = self.send_request(
            url, extra_headers=headers, method="POST", body=body,
        )

        try:
            if response and response.status_code == 200:
                eligible_status = response.json()["productResponseList"][0][
                    "overallStatus"
                ]
            elif response and response.status_code != 200:
                raise EligibilityRetrievalException(
                    f"Error retrieving eligibility, response details: {response.json()}"
                )
            else:  # response is None or False
                raise EligibilityRetrievalException(
                    "Error retrieving eligibility. Got no response"
                )
        except JSONDecodeError as e:
            raise EligibilityRetrievalException(
                f"Error while decoding response as json, details: {e}"
            )

        return eligible_status == "ELIGIBLE"
