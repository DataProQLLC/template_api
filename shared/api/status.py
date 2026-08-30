"""Two different endpoints for two different audiences.

/health          unversioned, for Cloud Run / load balancer probes.
                 Must stay fast and dependency-free -- if it checked the
                 database, a slow DB would make the platform kill healthy
                 instances and take the whole service down.

/{version}/status  per-version, for humans and for the mobile client's
                 launch check. Shows deprecation state, runtime capacity,
                 and server time.
"""
import os
import platform
import time
from datetime import datetime, timezone

import anyio
from fastapi import APIRouter, Request

# Regenerated on every process start -- a stand-in for "which Cloud Run
# instance answered". Watch it multiply to see autoscaling.
INSTANCE = os.getenv("K_REVISION_INSTANCE") or os.urandom(4).hex()
STARTED_AT = time.time()


def make_status_router(
    *,
    version: str,
    latest: str,
    versions: list[str],
    env: str,
    deprecated: bool = False,
    sunset: str | None = None,
) -> APIRouter:
    router = APIRouter()

    @router.get("/status", tags=["meta"], summary="Version status and runtime")
    async def status(request: Request):
        limiter = anyio.to_thread.current_default_thread_limiter()
        pool = getattr(request.app.state, "http", None)

        return {
            "version": version,
            "latest_version": latest,
            "supported_versions": versions,
            # Clients read these to decide whether to prompt an upgrade.
            "deprecated": deprecated,
            "sunset": sunset,
            "env": env,
            "deployment": {
                "instance": INSTANCE,
                "revision": os.getenv("K_REVISION", "local"),
                "service": os.getenv("K_SERVICE", "local"),
                "uptime_seconds": round(time.time() - STARTED_AT, 1),
            },
            "runtime": {
                "python": platform.python_version(),
                # Concurrency headroom. available == 0 means sync handlers
                # are queueing -- see /debug endpoints.
                "threadpool_total": limiter.total_tokens,
                "threadpool_available": limiter.available_tokens,
                "http_max_connections": getattr(
                    getattr(pool, "_limits", None), "max_connections", None
                ),
            },
            # Lets a client detect clock skew, the usual cause of
            # "token expired" errors on a device with a wrong clock.
            "server_time": datetime.now(timezone.utc).isoformat(),
        }

    return router