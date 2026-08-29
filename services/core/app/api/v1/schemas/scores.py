# services/core/app/api/v1/schemas/scores.py
from datetime import datetime
from pydantic import BaseModel

class UserScoreOut(BaseModel):
    profile_id: int
    ratings_scored: int = 0
    avg_bts: float | None = None
    avg_info: float | None = None
    avg_pred: float | None = None
    trust_score: float | None = None
    computed_at: datetime | None = None

    model_config = {"title": "Score.UserScoreOut"}