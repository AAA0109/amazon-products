from apps.ads_api.exceptions.ads_api.base import BaseAmazonAdsException


class EligibilityRetrievalException(BaseAmazonAdsException):
    """
    Custom exception raised when there's an error retrieving eligibility.
    """

    def __init__(self, message="Eligibility retrieval error"):
        self.message = message
        super().__init__(self.message)
