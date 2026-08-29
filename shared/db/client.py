# shared/ultra_shared/db/client.py
from enum import Enum
from functools import lru_cache
from typing import Any
import httpx

class Role(str, Enum):
    USER = "user"
    ADMIN = "admin"

@lru_cache
def _pool() -> httpx.Client:
    """One connection pool for the process. No per-request state."""
    return httpx.Client(
        timeout=httpx.Timeout(10.0, connect=3.0),
        limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
    )

class DBClient:
    """Thin PostgREST wrapper. Auth is per-call, so instances are safe to share."""

    def __init__(self, url: str, publishable_key: str, secret_key: str):
        base = url.rstrip("/")
        self._base = f"{base}/rest/v1"
        self._auth_base = f"{base}/auth/v1"
        self._publishable = publishable_key
        self._secret = secret_key

    def _headers(self, role: Role, access_token: str | None) -> dict[str, str]:
        if role is Role.ADMIN:
            key, token = self._secret, self._secret
        else:
            if not access_token:
                raise ValueError("USER role requires an access_token")
            key, token = self._publishable, access_token
        return {
            "apikey": key,
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
    
    def _auth_headers(self, access_token: str | None = None) -> dict[str, str]:
        return {
            "apikey": self._publishable,
            "Authorization": f"Bearer {access_token or self._publishable}",
            "Content-Type": "application/json",
        }

    def auth_post(self, path: str, body: dict,
                  params: dict | None = None,
                  access_token: str | None = None) -> dict:
        r = _pool().post(
            f"{self._auth_base}/{path.lstrip('/')}",
            json=body,
            params=params,
            headers=self._auth_headers(access_token),
        )
        r.raise_for_status()
        return r.json()

    def rpc(
        self,
        fn: str,
        params: dict[str, Any] | None = None,
        *,
        role: Role = Role.ADMIN,
        access_token: str | None = None,
    ) -> Any:
        r = _pool().post(
            f"{self._base}/rpc/{fn}",
            json=params or {},
            headers=self._headers(role, access_token),
        )
        r.raise_for_status()
        return r.json()

    def select(
        self,
        table: str,
        *,
        params: dict[str, str] | None = None,
        role: Role = Role.ADMIN,
        access_token: str | None = None,
    ) -> list[dict]:
        r = _pool().get(
            f"{self._base}/{table}",
            params=params or {},
            headers=self._headers(role, access_token),
        )
        r.raise_for_status()
        return r.json()

    def insert(
        self,
        table: str,
        rows: dict | list[dict],
        *,
        role: Role = Role.ADMIN,
        access_token: str | None = None,
        upsert_on: str | None = None,
    ) -> list[dict]:
        headers = self._headers(role, access_token)
        headers["Prefer"] = "return=representation"
        if upsert_on:
            headers["Prefer"] += ",resolution=merge-duplicates"
        r = _pool().post(
            f"{self._base}/{table}",
            json=rows,
            params={"on_conflict": upsert_on} if upsert_on else None,
            headers=headers,
        )
        r.raise_for_status()
        return r.json()

@lru_cache
def get_db(url: str, publishable_key: str, secret_key: str) -> DBClient:
    return DBClient(url, publishable_key, secret_key)