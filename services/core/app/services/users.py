# services/core/app/services/users.py
from datetime import datetime, timezone
import httpx
from shared.db.client import DBClient, Role
from shared.errors.exceptions import AppError, AuthError, ConflictError

def _session(data: dict) -> dict:
    user = data.get("user") or {}
    expires_at = data.get("expires_at")
    return {
        "user_id": user.get("id"),
        "email": user.get("email"),
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
        "expires_at": datetime.fromtimestamp(expires_at, tz=timezone.utc)
                      if expires_at else None,
    }

def signup(db: DBClient, email: str, password: str, username: str) -> dict:
    try:
        data = db.auth_post("signup", {
            "email": email,
            "password": password,
            "data": {"username": username},
        })
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 422:
            raise ConflictError("That email or username is already in use.")
        raise AppError("Could not create account.")

    if not data.get("access_token"):
        raise AppError(
            "Account created but no session returned. "
            "Email confirmation may be required."
        )

    return {**_session(data), "username": username}

def signin(db: DBClient, email: str, password: str) -> dict:
    try:
        data = db.auth_post(
            "token", {"email": email, "password": password},
            params={"grant_type": "password"},
        )
    except httpx.HTTPStatusError:
        raise AuthError("Incorrect email or password.")
    return _session(data)

def refresh(db: DBClient, refresh_token: str) -> dict:
    try:
        data = db.auth_post(
            "token", {"refresh_token": refresh_token},
            params={"grant_type": "refresh_token"},
        )
    except httpx.HTTPStatusError:
        raise AuthError("Session expired. Sign in again.")
    return _session(data)

def get_me(db: DBClient, *, role: Role, access_token: str) -> dict:
    """Runs as the user — RLS restricts the read to their own row."""
    rows = db.select(
        "profiles",
        params={"select": "*", "limit": "1"},
        role=role,
        access_token=access_token,
    )
    if not rows:
        raise AppError("Profile not found.")
    return rows[0]