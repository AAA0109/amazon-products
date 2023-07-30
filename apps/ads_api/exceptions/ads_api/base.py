class BaseAmazonAdsException(Exception):
    pass


class ObjectNotCreatedError(BaseAmazonAdsException):
    def __init__(self, errors):
        self.errors = errors

    def __str__(self):
        return f"Object not created. Details {self.errors}"


class ObjectNotUpdatedError(BaseAmazonAdsException):
    pass
