"""Metric endpoints. Read-heavy and cacheable."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ..cache.redis_cache import cached
from ..storage import db

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@cached("metrics_range", ttl=60)
def _load_metrics(service: str, endpoint: str, start: str, end: str) -> list[dict]:
    return db.metrics_in_range(service, endpoint, start, end)


@router.get("")
def get_metrics(
    service: str = Query(...),
    endpoint: str = Query(...),
    start: str = Query(..., description="ISO-8601 inclusive"),
    end: str = Query(..., description="ISO-8601 exclusive"),
):
    if start >= end:
        raise HTTPException(status_code=400, detail="start must be before end")
    return {"service": service, "endpoint": endpoint, "windows": _load_metrics(service, endpoint, start, end)}


@router.get("/errors")
@cached("top_errors", ttl=60)
def top_errors(
    start: str = Query(...),
    end: str = Query(...),
    limit: int = Query(10, ge=1, le=50),
):
    return {"errors": db.top_error_types(start, end, limit)}
