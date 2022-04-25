class AccessDenied(Exception):
    """ Raised when access was denied from Discord API """
    def __init__(self, message: str):
        super().__init__(message)


class HTTPException(Exception):
    """ Base exception for HTTP errors """
    def __init__(self, code: int, data: dict, path: str):
        self.path = path
        self.code = code
        self.message = data.get("message", "")
        self.retry_after = data.get("retry_after", 0)

        super().__init__(
            f"HTTP {self.code}: {self.message} | {self.path} "
            f"(retry after {self.retry_after} seconds)"
        )


class NotSignedIn(Exception):
    """ Raised when the user is not signed in """
    pass
