from datetime import datetime
from pydantic import BaseModel

class ClaimOut(BaseModel):
    id: int
    name: str
    description: str | None = None
    category: str | None = None
    subcategory: str | None = None
    microcategory: str | None = None
    opened_at: datetime
    closed_at: datetime | None = None
    created_at: datetime
    rating_count: int = 0
    consensus_state: str
    actual_supported: float | None = None
    actual_disputed: float | None = None
    predicted_supported: float | None = None
    predicted_disputed: float | None = None
    info_supported: float | None = None
    info_disputed: float | None = None
    has_rated: bool
    is_informed: bool
    my_rated_at: datetime | None = None
    is_saved: bool

    model_config = {"title": "Claim.Out"}

class ClaimListOut(BaseModel):
    view: str = "explore"
    claims: list[ClaimOut] = []
    saved: list[ClaimOut] = []
    recently_rated: list[ClaimOut] = []
    total: int = 0
    ran_as: str | None = None

    model_config = {"title": "Claim.List"}