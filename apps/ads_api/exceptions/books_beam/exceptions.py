class BaseBooksBeamException(Exception):
    pass


class BookStillProcessing(BaseBooksBeamException):
    pass


class BookAlreadyTracking(BaseBooksBeamException):
    pass


class ResponseValidationException(BaseBooksBeamException):
    pass


class BooksbeamServerError(BaseBooksBeamException):
    pass
