# services/core_api/app/api/v1/routes/users.py
from fastapi import APIRouter, status
from shared.db.client import Role
from app.api.deps import CurrentUserDep, Db
from app.api.v1.schemas.users import SignupIn, SignupOut, SessionOut, SigninIn, RefreshIn
from app.services import users as service

router = APIRouter()

@router.post("/signup", response_model=SessionOut, status_code=201)
def signup(payload: SignupIn, db: Db):
    return service.signup(db, payload.email, payload.password, payload.username)

@router.post("/signin", response_model=SessionOut)
def signin(payload: SigninIn, db: Db):
    return service.signin(db, payload.email, payload.password)

@router.post("/refresh", response_model=SessionOut)
def refresh(payload: RefreshIn, db: Db):
    return service.refresh(db, payload.refresh_token)

@router.get("/me")
def me(user: CurrentUserDep, db: Db):
    return service.get_me(db, role=Role.USER, access_token=user.access_token)

@router.get("/all")
def me(user: CurrentUserDep, db: Db):
    return service.get_me(db, role=Role.ADMIN, access_token=user.access_token)