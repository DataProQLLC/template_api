from fastapi import APIRouter

from app.config import settings
from app.api.v1.routes import auth

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["Auth"])

# Load-testing endpoints. Gated so they can never ship to prod.
if not settings.is_prod:
    from app.api.v1.routes import debug

    router.include_router(debug.router, prefix="/debug", tags=["debug"])