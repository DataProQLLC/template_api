from fastapi import APIRouter

from app.api.deps import CurrentUserDep, Db
from app.api.v1.schemas.users import SignupIn, SessionOut, SigninIn, RefreshIn
from app.services import auth as service

router = APIRouter()


@router.post("/signup", response_model=SessionOut, status_code=201)
async def signup(payload: SignupIn, db: Db):
    return await service.signup(db, payload.email, payload.password, payload.username)


@router.post("/signin", response_model=SessionOut)
async def signin(payload: SigninIn, db: Db):
    return await service.signin(db, payload.email, payload.password)


@router.post("/refresh", response_model=SessionOut)
async def refresh(payload: RefreshIn, db: Db):
    return await service.refresh(db, payload.refresh_token)


@router.get("/me")
async def me(user: CurrentUserDep, db: Db):
    return await service.get_me(db, access_token=user.access_token)