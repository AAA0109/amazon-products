from apps.ads_api.exceptions.ads_api.base import BaseAmazonAdsException


class CampaignDoesNotCreated(BaseAmazonAdsException):
    pass


class CampaignDoesNotUpdated(BaseAmazonAdsException):
    pass


class CampaignAlreadyExists(BaseAmazonAdsException):
    pass


class InvalidCampaignPurpose(BaseAmazonAdsException):
    pass
