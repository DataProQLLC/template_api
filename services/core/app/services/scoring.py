# services/core/app/services/scoring.py
from shared.db.client import DBClient, Role

def run_scoring(db: DBClient) -> dict:
    return db.rpc("run_all_scoring", {}, role=Role.ADMIN)