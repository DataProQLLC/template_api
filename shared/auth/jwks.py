# shared/ultra_shared/auth/jwks.py
import asyncio, time
import httpx, jwt
from jwt.algorithms import ECAlgorithm, RSAAlgorithm

class JWKSCache:
    def __init__(self, jwks_url: str, min_refresh: int = 60):
        self._url, self._min_refresh = jwks_url, min_refresh
        self._keys: dict[str, object] = {}
        self._last = 0.0
        self._lock = asyncio.Lock()

    async def _fetch(self) -> None:
        async with httpx.AsyncClient(timeout=5.0) as c:
            r = await c.get(self._url)
            r.raise_for_status()
        keys = {}
        for k in r.json().get("keys", []):
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
            pass