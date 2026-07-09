"""Trace lookup endpoints. Not cached — debugging wants fresh data."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..storage import db

router = APIRouter(prefix="/api/traces", tags=["traces"])


@router.get("/{trace_id}")
def get_trace(trace_id: str):
    rows = db.trace_by_id(trace_id)
    if not rows:
        raise HTTPException(status_code=404, detail="trace not found")
    return {"trace_id": trace_id, "events": rows}
