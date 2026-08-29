# services/core/app/services/users.py
import httpx
from shared.db.client import DBClient, Role
from shared.errors.exceptions import AppError, AuthError, ConflictError

    #return service.rate_add(db, payload.claim_id, payload.belief, payload.predicted_pct, payload.confidence, payload.time_spent_ms, role=Role.USER, access_token=user.access_token)
def rate_add(db: DBClient, claim_id: int, belief: str, predicted_pct: float, confidence: int, time_spent_ms: int, role: Role, access_token: str) -> dict:
    try:
        rows = {"claim_id": claim_id, "belief": belief, "predicted_pct": predicted_pct, "confidence": confidence, "time_spent_ms": time_spent_ms}
        data = db.insert(
            "ratings",
            rows=rows,
            role=role,
            access_token=access_token,
            )
    except httpx.HTTPStatusError as e:
        raise AppError("Could not create rating.")

    return {
        "rows": rows
    }