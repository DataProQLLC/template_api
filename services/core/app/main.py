# services/core_api/app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from shared.errors.handlers import register_error_handlers
from app.config import settings
from app.api.deps import jwks
from app.api.v1 import router as v1

@asynccontextmanager
async def lifespan(app: FastAPI):
    await jwks.warm()
    yield

app = FastAPI(
    title="Template Core API",
    lifespan=lifespan,
    docs_url=None if settings.is_prod else "/docs",
)
register_error_handlers(app)
app.include_router(v1, prefix="/v1")

@app.get("/health")
def health():
    return {"ok": True, "env": settings.env}