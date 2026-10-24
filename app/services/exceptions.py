"""Errors raised by the service layer."""


class NotFoundError(LookupError):
    """Raised when a requested resource does not exist."""
