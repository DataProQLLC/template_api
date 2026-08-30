"""Response conventions.

Rule: SINGLE resources are returned bare; COLLECTIONS are wrapped.

    GET /users/me      -> {"id": ..., "username": ...}
    GET /users         -> {"data": [...], "meta": {...}}

Enveloping single resources too ({"data": {...}}) is a defensible
alternative (JSON:API does it), but it adds a level of nesting to every
client model for metadata that only collections actually have. What matters
most is being consistent within a version -- do not mix both styles.
"""
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageMeta(BaseModel):
    limit: int = Field(description="Max items requested.")
    offset: int = Field(description="Items skipped.")
    count: int = Field(description="Items in this page.")
    total: int | None = Field(
        default=None,
        description="Total matching rows, when the datastore reports it cheaply.",
    )
    has_more: bool = Field(description="Whether another page exists.")
    next_offset: int | None = Field(
        default=None, description="Offset for the next page, or null at the end."
    )


class Page(BaseModel, Generic[T]):
    data: list[T]
    meta: PageMeta

    @classmethod
    def of(
        cls, items: list[T], *, limit: int, offset: int, total: int | None = None
    ) -> "Page[T]":
        has_more = (
            (offset + len(items)) < total if total is not None else len(items) == limit
        )
        return cls(
            data=items,
            meta=PageMeta(
                limit=limit,
                offset=offset,
                count=len(items),
                total=total,
                has_more=has_more,
                next_offset=offset + len(items) if has_more else None,
            ),
        )


class PageParams(BaseModel):
    """Shared query params for list endpoints. Use with Depends()."""

    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


# --- Documented error shape (for OpenAPI responses=) ---------------------


class ErrorDetail(BaseModel):
    field: str | None = None
    message: str
    type: str | None = None


class ErrorBody(BaseModel):
    code: str = Field(description="Stable machine-readable code. Branch on this.")
    message: str = Field(description="Human-readable. May change without notice.")
    details: list[ErrorDetail] | None = None
    request_id: str = Field(description="Echoes X-Request-ID. Quote it in bug reports.")


class ErrorResponse(BaseModel):
    error: ErrorBody


#: Attach to routers so every endpoint documents the same error shape.
ERROR_RESPONSES: dict = {
    400: {"model": ErrorResponse, "description": "Bad request"},
    401: {"model": ErrorResponse, "description": "Missing or invalid credentials"},
    403: {"model": ErrorResponse, "description": "Not permitted"},
    404: {"model": ErrorResponse, "description": "Not found"},
    409: {"model": ErrorResponse, "description": "Conflict"},
    422: {"model": ErrorResponse, "description": "Validation failed"},
    429: {"model": ErrorResponse, "description": "Rate limited"},
    500: {"model": ErrorResponse, "description": "Internal error"},
    502: {"model": ErrorResponse, "description": "Upstream unavailable"},
}