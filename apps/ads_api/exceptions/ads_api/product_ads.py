from apps.ads_api.exceptions.ads_api.base import BaseAmazonAdsException


class ProductAdDoesNotCreated(BaseAmazonAdsException):
    pass


class ProductAdIneligible(BaseAmazonAdsException):
    def __init__(self, asin: str):
        self.asin = asin

    def __str__(self):
        return f"Product[{self.asin}] is ineligible for advertising"
