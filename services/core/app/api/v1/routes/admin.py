# services/core/app/api/v1/routes/admin.py
from fastapi import APIRouter, Header, HTTPException
from app.api.deps import Db
from app.config import settings
from app.services import scoring

router = APIRouter()

@router.post("/score")
def run_scoring(db: Db, x_admin_key: str = Header(...)):
    # if x_admin_key != settings.admin_key:
    #     raise HTTPException(403, "Forbidden")
    return scoring.run_scoring(db)