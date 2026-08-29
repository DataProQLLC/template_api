# services/core/app/services/claims.py
from shared.db.client import DBClient, Role

def list_claims(
    db: DBClient,
    *,
    role: Role,
    access_token: str | None = None,
    view: str | None = None,
    category: str | None = None,
    state: str | None = None,
    rated: str | None = None,
    saved_only: bool = False,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    return db.rpc(
        "get_claims",
        {
            "p_view": view,
            "p_category": category,
            "p_state": state,
            "p_rated": rated,
            "p_saved_only": saved_only,
            "p_limit": limit,
            "p_offset": offset,
        },
        role=role,
        access_token=access_token if role is Role.USER else None,
    )

def get_filters(db: DBClient, *, access_token: str) -> dict:
    return db.rpc("get_claim_filters", {}, role=Role.USER,
                  access_token=access_token)

def toggle_save(db: DBClient, *, role: Role, access_token: str, claim_id: int) -> bool:
    return db.rpc("toggle_claim_save", {"p_claim_id": claim_id},
                  role=role, access_token=access_token)