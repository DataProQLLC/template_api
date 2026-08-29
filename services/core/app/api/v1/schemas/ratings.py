from typing import Literal
from pydantic import BaseModel, Field

class RatingIn(BaseModel):
    claim_id: int
    belief: Literal["supported", "disputed", "unverifiable"]
    predicted_pct: float = Field(ge=0, le=100)
    confidence: int | None = Field(default=None, ge=1, le=5)
    time_spent_ms: int | None = None