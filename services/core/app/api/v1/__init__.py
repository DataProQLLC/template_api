# services/core_api/app/api/v1/__init__.py
from fastapi import APIRouter
from app.api.v1.routes import users

router = APIRouter()
router.include_router(users.router, prefix="/users", tags=["users"])
