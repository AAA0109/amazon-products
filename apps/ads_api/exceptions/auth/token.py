class AuthFailed(Exception):
    pass


class TokenNotFoundException(AuthFailed):
    pass


class TokenExpiredException(AuthFailed):
    """
    Custom exception raised when a token has expired.
    """

    def __init__(self, message="Token has expired"):
        self.message = message
        super().__init__(self.message)
