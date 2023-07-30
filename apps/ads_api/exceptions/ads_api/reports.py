from apps.ads_api.exceptions.ads_api.base import BaseAmazonAdsException


class NoPayloadForGivenReportType(BaseAmazonAdsException):
    pass


class NoReportDataReturned(BaseAmazonAdsException):
    pass


class CreatingReportRequestException(BaseAmazonAdsException):
    pass


class BaseRefreshingReportException(BaseAmazonAdsException):
    pass


class RefreshingReportException(BaseRefreshingReportException):
    pass


class StillGeneratingReportException(BaseRefreshingReportException):
    pass


class EmptyReportDataReturned(BaseRefreshingReportException):
    pass
