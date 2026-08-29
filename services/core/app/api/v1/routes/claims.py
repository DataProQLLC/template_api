# services/core/app/api/v1/routes/claims.py
from fastapi import APIRouter, Query
from shared.db.client import Role
from app.api.deps import Db, CurrentUserDep
from app.api.v1.schemas.claims import ClaimOut, ClaimListOut
from app.services import claims as service

router = APIRouter()

# services/core/app/api/v1/routes/claims.py
@router.get("", response_model=ClaimListOut)
def list_claims(
    user: CurrentUserDep,
    db: Db,
    view: str = Query("explore"),
    category: str | None = Query(None),
    state: str | None = Query(None),
    rated: str | None = Query(None),
    saved_only: bool = Query(False),
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
):
    data = service.list_claims(
        db, role=Role.USER, access_token=user.access_token, view=view,
        category=category, state=state, rated=rated,
        saved_only=saved_only, limit=limit, offset=offset,
    )
    return ClaimListOut(
        view=data.get("view", "explore"),
        claims=[ClaimOut(**c) for c in data.get("claims", [])],
        saved=[ClaimOut(**c) for c in data.get("saved", [])],
        recently_rated=[ClaimOut(**c) for c in data.get("recently_rated", [])],
        total=data.get("total", 0),
    )

@router.get("/filters")
def filters(user: CurrentUserDep, db: Db):
    return service.get_filters(db, access_token=user.access_token)


@router.post("/{claim_id}/save")
def toggle_save(claim_id: int, user: CurrentUserDep, db: Db):
    saved = service.toggle_save(
        db, role=Role.USER, access_token=user.access_token, claim_id=claim_id)
    print(f"result={saved}")
    return {"saved": saved}