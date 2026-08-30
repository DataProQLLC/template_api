"""Load-testing endpoints. NEVER enabled in prod (see api/v1/__init__.py).

Three ways to wait 15 seconds. They behave identically with one caller and
very differently under concurrency -- which is the point.

Deploy to a dev Cloud Run service, then fire N concurrent requests at each
and watch what /debug/fast does while they run.
"""
import asyncio
import os
import time
import uuid

import anyio
from fastapi import APIRouter, Query

router = APIRouter()

# New value every process start -> a proxy for "which Cloud Run instance
# served this". Watch it change to see autoscaling happen.
INSTANCE = uuid.uuid4().hex[:8]

Seconds = Query(default=15.0, ge=0, le=600, description="How long to wait.")


def _meta(mode: str, seconds: float, started: float) -> dict:
    return {
        "mode": mode,
        "requested_seconds": seconds,
        "actual_seconds": round(time.perf_counter() - started, 3),
        "instance": INSTANCE,
        "revision": os.getenv("K_REVISION", "local"),
    }


@router.get("/fast")
async def fast():
    """The canary. Hit this while the slow ones are running."""
    return {"ok": True, "instance": INSTANCE, "revision": os.getenv("K_REVISION", "local")}


@router.get("/slow-async")
async def slow_async(seconds: float = Seconds):
    """CORRECT: async def + awaited sleep. Event loop stays free."""
    t0 = time.perf_counter()
    await asyncio.sleep(seconds)
    return _meta("async def + await (correct)", seconds, t0)


@router.get("/slow-sync")
def slow_sync(seconds: float = Seconds):
    """CORRECT: plain def -> FastAPI runs it in the threadpool (40 by
    default), so the event loop stays free. Caps out at 40 concurrent."""
    t0 = time.perf_counter()
    time.sleep(seconds)
    return _meta("def + blocking (threadpool)", seconds, t0)


@router.get("/slow-threaded")
async def slow_threaded(seconds: float = Seconds):
    """CORRECT: async def + explicit thread handoff. This is the pattern for
    a sync-only vendor SDK (see clients/plaid.py)."""
    t0 = time.perf_counter()
    await anyio.to_thread.run_sync(lambda: time.sleep(seconds))
    return _meta("async def + to_thread (sync SDK pattern)", seconds, t0)


@router.get("/slow-blocking")
async def slow_blocking(seconds: float = Seconds):
    """THE BUG: async def + blocking call. Stalls the event loop for EVERY
    user of this instance. /debug/fast will hang behind it."""
    t0 = time.perf_counter()
    time.sleep(seconds)
    return _meta("async def + blocking (BROKEN)", seconds, t0)


@router.get("/threadpool")
async def threadpool():
    limiter = anyio.to_thread.current_default_thread_limiter()
    return {
        "total_tokens": limiter.total_tokens,
        "available": limiter.available_tokens,
        "instance": INSTANCE,
    }