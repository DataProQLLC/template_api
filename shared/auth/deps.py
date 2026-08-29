# shared/ultra_shared/auth/deps.py
from dataclasses import dataclass
from typing import Optional
import jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

bearer = HTTPBearer(auto_error=False)
ALGORITHMS = ["ES256", "RS256"]

@dataclass(frozen=True)
class CurrentUser:
    id: str
    email: Optional[str]
    claims: dict
    access_token: str

def unauthorized(detail: str) -> HTTPException:
    return HTTPException(status.HTTP_401_UNAUTHORIZED, detail,
                         headers={"WWW-Authenticate": "Bearer"})

def make_auth_deps(jwks, supabase_url: str):
    """Factory so each service binds its own JWKS cache and issuer."""

    async def decode(token: str) -> dict:
        try:
            kid = jwt.get_unverified_header(token).get("kid")
        except jwt.PyJWTError:
            raise unauthorized("Malformed token")
        if not kid:
            raise unauthorized("Token missing key id")
        key = await jwks.get_key(kid)
        if key is None:
            raise unauthorized("Unknown signing key")
        try:
            return jwt.decode(
                token, key=key, algorithms=ALGORITHMS,
                audience="authenticated",
                issuer=f"{supabase_url}/auth/v1",
                options={"require": ["exp", "sub", "aud"]},
            )
        except jwt.ExpiredSignatureError:
            raise unauthorized("Token expired")
        except jwt.PyJWTError:
            raise unauthorized("Invalid token")

    async def current_user(cred: Optional[HTTPAuthorizationCredentials]) -> CurrentUser:
        if cred is None:
            raise unauthorized("Missing bearer token")
        c = await decode(cred.credentials)
        return CurrentUser(id=c["sub"], email=c.get("email"), claims=c, access_token=cred.credentials)

    return current_user