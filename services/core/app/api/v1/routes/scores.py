# services/core/app/api/v1/routes/scores.py
from fastapi import APIRouter
from app.api.deps import CurrentUserDep, Db
from app.api.v1.schemas.scores import UserScoreOut
from app.services import scores as service

router = APIRouter()

# services/core/app/api/v1/routes/scores.py
@router.get("/me", response_model=UserScoreOut)
def my_score(user: CurrentUserDep, db: Db):
    return service.get_my_score(db, access_token=user.access_token)