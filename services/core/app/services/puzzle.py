# services/core/app/services/puzzle.py
from shared.db.client import DBClient, Role


def get_daily_puzzle(
    db: DBClient,
    *,
    role: Role,
    user_id: str,
    access_token: str | None = None,
) -> dict:
    return db.rpc(
        "get_daily_puzzle",
        {"p_user_id": user_id},
        role=role,
        access_token=access_token if role is Role.USER else None,
    )