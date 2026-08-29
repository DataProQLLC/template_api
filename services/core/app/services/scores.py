# services/core/app/services/scores.py
from shared.db.client import DBClient, Role

def get_my_score(db: DBClient, *, access_token: str) -> dict:
    return db.rpc("get_my_score", {}, role=Role.USER, access_token=access_token)