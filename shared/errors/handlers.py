"""One error shape for every failure.

Without this, a client sees three different bodies:
    AppError            -> {"error": {...}}
    HTTPException (401) -> {"detail": "Missing bearer token"}
    Validation    (422) -> {"detail": [{"loc": [...], "msg": ...}]}

All of them now emit:
    {"error": {"code", "message", "details"?, "request_id"}}

NOTE: a CORS failure can never reach this code. The browser discards the
response before JavaScript sees it, and a rejected preflight never runs a
route handler at all. "Failed to fetch" is not something a server-side
error shape can fix.
"""
import logging
import uuid
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .exceptions import AppError

log = logging.getLogger("api.errors")

REQUEST_ID_HEADER = "X-Request-ID"

# HTTP status -> stable error code, for errors raised by the framework
# rather than by application code.
_STATUS_CODES = {
    400: "bad_request",
    401: "invalid_credentials",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    422: "validation_failed",
    429: "rate_limited",
    500: "internal_error",
    502: "upstream_unavailable",
    503: "unavailable",
    504: "upstream_timeout",
}


def request_id(request: Request) -> str:
    return getattr(request.state, "request_id", None) or str(uuid.uuid4())


def error_body(
    code: str, message: str, *, rid: str, details: Any = None
) -> dict[str, Any]:
    err: dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        err["details"] = details
    err["request_id"] = rid
    return {"error": err}


def _json(status_code: int, body: dict, rid: str, headers: dict | None = None):
    hdrs = {REQUEST_ID_HEADER: rid, **(headers or {})}
    return JSONResponse(status_code=status_code, content=body, headers=hdrs)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError):
        rid = request_id(request)
        return _json(
            exc.status_code,
            error_body(exc.code, exc.message, rid=rid, details=exc.details),
            rid,
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(request: Request, exc: StarletteHTTPException):
        rid = request_id(request)
        code = _STATUS_CODES.get(exc.status_code, "http_error")
        message = exc.detail if isinstance(exc.detail, str) else "Request failed."
        return _json(
            exc.status_code,
            error_body(code, message, rid=rid),
            rid,
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(request: Request, exc: RequestValidationError):
        rid = request_id(request)
        details = [
            {
                # Drop the leading "body"/"query" segment -- clients care about
                # the field name, not FastAPI's internal location tuple.
                "field": ".".join(str(p) for p in e["loc"][1:]) or str(e["loc"][0]),
                "message": e["msg"],
                "type": e["type"],
            }
            for e in exc.errors()
        ]
        return _json(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_body(
                "validation_failed",
                "One or more fields are invalid.",
                rid=rid,
                details=jsonable_encoder(details),
            ),
            rid,
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        """Catch-all. Never leak internals to the client -- log them instead,
        and hand back the request_id so a support ticket maps to a log line."""
        rid = request_id(request)
        log.exception("unhandled error request_id=%s path=%s", rid, request.url.path)
        return _json(
            500,
            error_body(
                "internal_error",
                "Something went wrong on our end. Please try again.",
                rid=rid,
            ),
            rid,
        )