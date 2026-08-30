from typing import Annotated, Optional

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials

from shared.auth.jwks import JWKSCache
from shared.auth.deps import bearer, make_auth_deps, CurrentUser
from shared.db.client import DBClient
from app.config import settings

# Holds only a URL and a dict at import time; the HTTP client is attached
# during lifespan startup.
jwks = JWKSCache(f"{settings.supabase_url}/auth/v1/.well-known/jwks.json")
_current_user = make_auth_deps(jwks, settings.supabase_url)


async def current_user(
    cred: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer)],
) -> CurrentUser:
    return await _current_user(cred)


CurrentUserDep = Annotated[CurrentUser, Depends(current_user)]


def db(request: Request) -> DBClient:
    """Built in lifespan, so it is never bound to the wrong event loop."""
    return request.app.state.db


Db = Annotated[DBClient, Depends(db)]