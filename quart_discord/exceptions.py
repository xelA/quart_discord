class AccessDenied(Exception):
    """ Raised when access was denied from Discord API """
    def __init__(self, message: str):
        super().__init__(message)


class HTTPException(Exception):
    """ Base exception for HTTP errors """
    def __init__(self, message: str):
        super().__init__(message)


class NotSignedIn(Exception):
    """ Raised when the user is not signed in """
    pass
