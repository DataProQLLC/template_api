import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from shared.errors.handlers import REQUEST_ID_HEADER


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Assigns every request an id and times it.

    Honours an inbound X-Request-ID so a trace survives across services and
    matches what the client logged. Always echoes it back, so a user can
    report an id that maps straight to a log line.
    """

    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        request.state.request_id = rid
        started = time.perf_counter()
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = rid
        response.headers["X-Response-Time-ms"] = (
            f"{(time.perf_counter() - started) * 1000:.1f}"
        )
        return response