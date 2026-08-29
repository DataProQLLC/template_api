# shared/ultra_shared/errors/exceptions.py
class AppError(Exception):
    status_code = 400
    code = "app_error"

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)

class ConflictError(AppError):
    status_code = 409
    code = "conflict"

class UpstreamError(AppError):
    status_code = 502
    code = "upstream_unavailable"

class AuthError(AppError):
    status_code = 401
    code = "invalid_credentials"