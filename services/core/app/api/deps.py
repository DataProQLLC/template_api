# services/core_api/app/api/deps.py
from typing import Annotated, Optional
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials
from supabase import Client
from shared.auth.jwks import JWKSCache
from shared.auth.deps import bearer, make_auth_deps, CurrentUser
from shared.db.client import DBClient, get_db
from app.config import settings

jwks = JWKSCache(f"{settings.supabase_url}/auth/v1/.well-known/jwks.json")
_current_user = make_auth_deps(jwks, settings.supabase_url)

async def current_user(
    cred: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer)],
) -> CurrentUser:
    return await _current_user(cred)

CurrentUserDep = Annotated[CurrentUser, Depends(current_user)]

def db() -> DBClient:
    return get_db(
        settings.supabase_url,
        settings.supabase_publishable_key,
        settings.supabase_secret_key,
    )

Db = Annotated[DBClient, Depends(db)]