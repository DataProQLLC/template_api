from enum import Enum
from typing import Any

import httpx


class Role(str, Enum):
    """Which credential the request runs under.

    USER  -> publishable key + the caller's JWT. RLS applies. Default for
             anything acting on behalf of a signed-in user.
    ADMIN -> secret key. RLS is BYPASSED. Only for trusted server-side work
             (webhooks, cron, admin tools). Never reachable from a plain
             authenticated route without an explicit authorization check.
    """

    USER = "user"
    ADMIN = "admin"


class DBClient:
    """Thin async PostgREST wrapper.

    The httpx.AsyncClient is injected rather than created here: an AsyncClient
    binds to the event loop it is created on, so it must be built inside the
    app lifespan and closed on shutdown. Injecting it also makes this class
    trivial to fake in tests.
    """

    def __init__(
        self,
        url: str,
        publishable_key: str,
        secret_key: str,
        http: httpx.AsyncClient,
    ):
        base = url.rstrip("/")
        self._base = f"{base}/rest/v1"
        self._auth_base = f"{base}/auth/v1"
        self._publishable = publishable_key
        self._secret = secret_key
        self._http = http

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

    async def auth_post(
        self,
        path: str,
        body: dict,
        params: dict | None = None,
        access_token: str | None = None,
    ) -> dict:
        r = await self._http.post(
            f"{self._auth_base}/{path.lstrip('/')}",
            json=body,
            params=params,
            headers=self._auth_headers(access_token),
        )
        r.raise_for_status()
        return r.json()

    async def rpc(
        self,
        fn: str,
        params: dict[str, Any] | None = None,
        *,
        role: Role = Role.USER,
        access_token: str | None = None,
    ) -> Any:
        r = await self._http.post(
            f"{self._base}/rpc/{fn}",
            json=params or {},
            headers=self._headers(role, access_token),
        )
        r.raise_for_status()
        return r.json()

    async def select(
        self,
        table: str,
        *,
        params: dict[str, str] | None = None,
        role: Role = Role.USER,
        access_token: str | None = None,
    ) -> list[dict]:
        r = await self._http.get(
            f"{self._base}/{table}",
            params=params or {},
            headers=self._headers(role, access_token),
        )
        r.raise_for_status()
        return r.json()

    async def insert(
        self,
        table: str,
        rows: dict | list[dict],
        *,
        role: Role = Role.USER,
        access_token: str | None = None,
        upsert_on: str | None = None,
    ) -> list[dict]:
        headers = self._headers(role, access_token)
        headers["Prefer"] = "return=representation"
        if upsert_on:
            headers["Prefer"] += ",resolution=merge-duplicates"
        r = await self._http.post(
            f"{self._base}/{table}",
            json=rows,
            params={"on_conflict": upsert_on} if upsert_on else None,
            headers=headers,
        )
        r.raise_for_status()
        return r.json()