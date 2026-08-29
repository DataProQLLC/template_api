# services/core/app/api/v1/routes/puzzle.py
from fastapi import APIRouter
from shared.db.client import Role
from app.api.deps import Db, CurrentUserDep
from app.api.v1.schemas.puzzle import PuzzleAnswerOut, PuzzleDailyOut, PuzzlePlayOut
from app.services import puzzle as service

router = APIRouter()

@router.get("", response_model=PuzzleDailyOut)
def get_daily_puzzle(user: CurrentUserDep, db: Db):
    data = service.get_daily_puzzle(
        db, role=Role.USER, access_token=user.access_token, user_id=user.id,
    )
    answer = data.get("answer")
    play = data.get("play")
    return PuzzleDailyOut(
        as_of=data["as_of"],
        puzzle_date=data["puzzle_date"],
        answer=PuzzleAnswerOut(**answer) if answer else None,
        play=PuzzlePlayOut(**play) if play else None,
    )