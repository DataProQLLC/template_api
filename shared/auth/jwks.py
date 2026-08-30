import asyncio
import time

import httpx
from jwt.algorithms import ECAlgorithm, RSAAlgorithm


class JWKSCache:
    """Caches Supabase's public signing keys.

    The shared AsyncClient is attached during app startup (see lifespan). If
    nothing attaches one, a short-lived client is created per fetch, which
    keeps this usable in tests without a running app.
    """

    def __init__(self, jwks_url: str, min_refresh: int = 60):
        self._url, self._min_refresh = jwks_url, min_refresh
        self._keys: dict[str, object] = {}
        self._last = 0.0
        self._lock = asyncio.Lock()
        self._http: httpx.AsyncClient | None = None

    def attach(self, http: httpx.AsyncClient) -> None:
        self._http = http

    async def _get_json(self) -> dict:
        if self._http is not None:
            r = await self._http.get(self._url)
            r.raise_for_status()
            return r.json()
        async with httpx.AsyncClient(timeout=5.0) as c:
            r = await c.get(self._url)
            r.raise_for_status()
            return r.json()

    async def _fetch(self) -> None:
        payload = await self._get_json()
        keys: dict[str, object] = {}
        for k in payload.get("keys", []):
            if not k.get("kid"):
                continue
            if k.get("kty") == "EC":
                keys[k["kid"]] = ECAlgorithm.from_jwk(k)
            elif k.get("kty") == "RSA":
                keys[k["kid"]] = RSAAlgorithm.from_jwk(k)
        self._keys, self._last = keys, time.monotonic()

    async def get_key(self, kid: str):
        if kid in self._keys:
            return self._keys[kid]
        async with self._lock:
            if kid in self._keys:
                return self._keys[kid]
            if time.monotonic() - self._last < self._min_refresh:
                return None
            await self._fetch()
        return self._keys.get(kid)

    async def warm(self) -> None:
        try:
            await self._fetch()
        except Exception:
            # Startup must not fail because Supabase blipped; the first
            # authenticated request will retry the fetch.
            pass