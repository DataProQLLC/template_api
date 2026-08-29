# services/core_api/app/api/v1/routes/users.py
from fastapi import APIRouter, status
from shared.db.client import Role
from app.api.deps import CurrentUserDep, Db
from app.api.v1.schemas.ratings import RatingIn
from app.services import ratings as service

router = APIRouter()

@router.post("/add", status_code=201)
def rate(payload: RatingIn, user: CurrentUserDep, db: Db):
    return service.rate_add(db, payload.claim_id, payload.belief, payload.predicted_pct, payload.confidence, payload.time_spent_ms, role=Role.USER, access_token=user.access_token)