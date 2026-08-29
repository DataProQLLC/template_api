# services/core_api/app/api/v1/__init__.py
from fastapi import APIRouter
from app.api.v1.routes import users
from app.api.v1.routes import claims
from app.api.v1.routes import ratings
from app.api.v1.routes import admin
from app.api.v1.routes import scores
from app.api.v1.routes import puzzle

router = APIRouter()
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(claims.router, prefix="/claims", tags=["claims"])
router.include_router(ratings.router, prefix="/ratings", tags=["ratings"])
router.include_router(admin.router, prefix="/admin", tags=["admin"])
router.include_router(scores.router, prefix="/scores", tags=["scores"])
router.include_router(puzzle.router, prefix="/puzzle", tags=["puzzle"])