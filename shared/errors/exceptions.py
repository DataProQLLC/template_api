"""Application errors.

Every one carries a stable machine-readable `code`. Clients should branch on
`code`, never on `message` -- messages are for humans and may be reworded or
localised at any time without a version bump.
"""
from typing import Any


class AppError(Exception):
    status_code = 400
    code = "bad_request"

    def __init__(self, message: str, *, details: Any = None):
        self.message = message
        self.details = details
        super().__init__(message)


class ValidationFailed(AppError):
    status_code = 422
    code = "validation_failed"


class AuthError(AppError):
    status_code = 401
    code = "invalid_credentials"


class ForbiddenError(AppError):
    status_code = 403
    code = "forbidden"


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class ConflictError(AppError):
    status_code = 409
    code = "conflict"


class RateLimitedError(AppError):
    status_code = 429
    code = "rate_limited"


class UpstreamError(AppError):
    status_code = 502
    code = "upstream_unavailable"