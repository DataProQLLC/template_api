# services/core/app/api/v1/schemas/users.py
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from app.config import settings

_prod = settings.env == "prod"

def _ex(*values):
    """Dev-only OpenAPI examples. Returns None in stage/prod."""
    return {"examples": list(values)} if not _prod else None

class SignupIn(BaseModel):
    email: EmailStr = Field(json_schema_extra=_ex("jwmatthews1126@gmail.com"))
    password: str = Field(
        min_length=8, max_length=72,
        json_schema_extra=_ex("testpassword123"),
    )
    username: str = Field(
        min_length=3, max_length=20, pattern=r"^[a-z0-9_]+$",
        json_schema_extra=_ex("joetest"),
    )

    model_config = {"title": "User.SignupIn"}

class SignupOut(BaseModel):
    user_id: str
    username: str
    access_token: str | None = None

    model_config = {"title": "User.SignupOut"}

class SigninIn(BaseModel):
    email: EmailStr = Field(json_schema_extra=_ex("jwmatthews1126@gmail.com"))
    password: str = Field(json_schema_extra=_ex("testpassword123"))

    model_config = {"title": "User.SigninIn"}

class SessionOut(BaseModel):
    user_id: str
    email: str | None = None
    access_token: str
    refresh_token: str
    expires_at: datetime | None = None

    model_config = {"title": "User.SessionOut"}

class RefreshIn(BaseModel):
    refresh_token: str

    model_config = {"title": "User.RefreshIn"}