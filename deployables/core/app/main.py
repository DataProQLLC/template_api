from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from shared.db.client import DBClient
from shared.docs.swagger import swagger_ui_with_versions
from shared.errors.handlers import register_error_handlers
from app.config import settings
from app.api.deps import jwks
from app.api.v1 import router as v1_router
from app.api.v2 import router as v2_router

_hide = settings.is_prod

# Single source of truth for versions. Order matters: last entry is "latest".
# Adding v3 = one line here + an app/api/v3 package. Retiring v1 = delete a line.
VERSIONS: list[tuple[str, object, str]] = [
    ("v1", v1_router, "Maintenance only. New clients should use the latest version."),
    ("v2", v2_router, "Current version."),
]
# VERSIONS: list[tuple[str, object, str]] = [
#     ("v1", v1_router, "Current version."),
# ]
VERSION_NAMES = [name for name, _, _ in VERSIONS]
LATEST = VERSION_NAMES[-1]


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(10.0, connect=3.0),
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
    ) as http:
        db = DBClient(
            settings.supabase_url,
            settings.supabase_publishable_key,
            settings.supabase_secret_key,
            http=http,
        )
        # Inside a mounted sub-app request.app is the SUB-app, so shared
        # resources must be set on every version app, not just the parent.
        for target in (app, *_version_apps):
            target.state.http = http
            target.state.db = db
        jwks.attach(http)
        await jwks.warm()
        yield


# Parent is a routing shell. Mounted apps don't appear in its OpenAPI schema,
# so it has no docs of its own -- /docs below is served manually.
app = FastAPI(
    title=f"{settings.app_name} core API",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
register_error_handlers(app)

_version_apps: list[FastAPI] = []
for _name, _router, _note in VERSIONS:
    _sub = FastAPI(
        title=f"{settings.app_name} core API",
        description=_note,
        version=_name,
        # Each version's spec must still be reachable -- the version dropdown
        # fetches these. The per-version UI pages are disabled so there is one
        # canonical docs page.
        openapi_url=None if _hide else "/openapi.json",
        docs_url=None,
        redoc_url=None,
        # Absolute per-environment URLs instead of the auto-injected relative
        # root_path, so the Servers dropdown can switch environments.
        servers=settings.doc_servers(f"/{_name}"),
        root_path_in_servers=False,
    )
    _sub.include_router(_router)
    register_error_handlers(_sub)
    app.mount(f"/{_name}", _sub)
    _version_apps.append(_sub)


@app.get("/health")
async def health():
    """Unversioned on purpose -- this contract must never break."""
    return {
        "ok": True,
        "env": settings.env,
        "versions": VERSION_NAMES,
        "latest": LATEST,
    }


@app.get("/", include_in_schema=False)
async def index():
    body = {"versions": VERSION_NAMES, "latest": LATEST}
    if not _hide:
        body["docs"] = "/docs"
    return body


if not _hide:

    @app.get("/docs", include_in_schema=False)
    async def docs():
        """One Swagger UI, two dropdowns:

        - "Select a definition" (top bar) switches API VERSION
        - "Servers"                       switches ENVIRONMENT

        Deep link a version with /docs?urls.primaryName=v1
        """
        return swagger_ui_with_versions(
            title=f"{settings.app_name} core API",
            urls=[{"url": f"/{v}/openapi.json", "name": v} for v in VERSION_NAMES],
            primary_name=LATEST,
        )

    @app.get("/redoc", include_in_schema=False)
    async def redoc_redirect():
        return RedirectResponse("/docs")