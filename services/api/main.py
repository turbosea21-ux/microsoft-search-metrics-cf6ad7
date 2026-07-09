"""Dashboard API. FastAPI app wiring the metric and trace routers, with a
consistent error envelope, a health probe, and Prometheus instrumentation.
"""
from __future__ import annotations

import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .observability.metrics import REQUESTS, REQUEST_SECONDS, configure_logging, metrics_app
from .routes import metrics, traces

log = configure_logging()
app = FastAPI(title="search-metrics-api")
app.include_router(metrics.router)
app.include_router(traces.router)
app.mount("/metrics", metrics_app)   # Prometheus scrape target


@app.middleware("http")
async def instrument(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - started
    route = request.url.path
    REQUESTS.labels(endpoint=route, status=str(response.status_code // 100) + "xx").inc()
    REQUEST_SECONDS.labels(endpoint=route).observe(elapsed)
    rid = request.headers.get("x-request-id", str(uuid.uuid4()))
    log.info(f"request route={route} status={response.status_code} ms={elapsed*1000:.1f} request_id={rid}")
    return response


@app.get("/health")
def health():
    return {"status": "ok"}


@app.exception_handler(Exception)
async def on_error(request: Request, exc: Exception):
    status = getattr(exc, "status_code", 500)
    return JSONResponse(
        status_code=status,
        content={
            "error": {
                "code": status,
                "message": getattr(exc, "detail", "internal server error"),
                "request_id": request.headers.get("x-request-id", str(uuid.uuid4())),
            }
        },
    )
