import logging
import time
import uuid
from contextlib import asynccontextmanager
from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import __version__
from app.config import get_settings
from app.conversion import refresh_conversions
from app.database import get_db, init_db, seed_store_from_layout
from app.funnel import compute_funnel
from app.health import build_health_response
from app.heatmap import compute_heatmap
from app.ingestion import ingest_events
from app.logging_config import configure_logging, log_request
from app.metrics import compute_metrics
from app.models import (
    AnomalyResponse,
    ErrorResponse,
    EventIngestRequest,
    EventIngestResponse,
    FunnelResponse,
    HeatmapResponse,
    HealthResponse,
    MetricsResponse,
)
from app.pos_loader import load_pos_transactions
from app.stores import ensure_store_exists
from app.anomalies import compute_anomalies

logger = logging.getLogger("store_intelligence.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    settings = get_settings()
    logger.info(
        "application_starting version=%s database_url=%s layout=%s",
        __version__,
        settings.database_url,
        settings.store_layout_path,
    )
    init_db()
    from app.database import db_session

    with db_session() as session:
        seed_store_from_layout(session)
        load_pos_transactions(session)
        refresh_conversions(session, "ST1008")
    logger.info("database_initialized")
    yield
    logger.info("application_shutdown")


app = FastAPI(
    title="Store Intelligence API",
    description="Purplle Store Intelligence Challenge — Intelligence API",
    version=__version__,
    lifespan=lifespan,
)

# Enable CORS globally for diagnostics while debugging Render deployment issues
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def structured_request_logging(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-Id", str(uuid.uuid4()))
    request.state.trace_id = trace_id
    start = time.perf_counter()
    response = await call_next(request)
    latency_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Trace-Id"] = trace_id
    log_request(
        logger,
        trace_id=trace_id,
        endpoint=request.url.path,
        latency_ms=latency_ms,
        status_code=response.status_code,
        store_id=getattr(request.state, "store_id", None),
        event_count=getattr(request.state, "event_count", None),
    )
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error="validation_error",
            detail=str(exc.errors()),
            trace_id=trace_id,
        ).model_dump(),
    )


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
    logger.exception("database_error trace_id=%s", trace_id)
    return JSONResponse(
        status_code=503,
        content=ErrorResponse(
            error="database_unavailable",
            detail="Database operation failed.",
            trace_id=trace_id,
        ).model_dump(),
    )


def _parse_date_param(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid date: {value}") from exc


@app.post("/events/ingest", response_model=EventIngestResponse, tags=["events"])
def ingest_event_batch(
    request: Request,
    body: EventIngestRequest,
    db: Session = Depends(get_db),
) -> EventIngestResponse:
    """Accept up to 500 events; idempotent by event_id; partial per-event validation failures."""
    request.state.event_count = len(body.events)
    if len(body.events) > 500:
        raise HTTPException(status_code=422, detail="Batch exceeds maximum of 500 events")
    return ingest_events(db, body.events)


@app.get("/stores/{store_id}/metrics", response_model=MetricsResponse, tags=["analytics"])
def store_metrics(
    request: Request,
    store_id: str,
    metric_date: str | None = Query(default=None, alias="date"),
    db: Session = Depends(get_db),
) -> MetricsResponse:
    request.state.store_id = store_id
    canonical = ensure_store_exists(db, store_id)
    return compute_metrics(db, canonical, _parse_date_param(metric_date))


@app.get("/stores/{store_id}/funnel", response_model=FunnelResponse, tags=["analytics"])
def store_funnel(
    request: Request,
    store_id: str,
    metric_date: str | None = Query(default=None, alias="date"),
    db: Session = Depends(get_db),
) -> FunnelResponse:
    request.state.store_id = store_id
    canonical = ensure_store_exists(db, store_id)
    return compute_funnel(db, canonical, _parse_date_param(metric_date))


@app.get("/stores/{store_id}/heatmap", response_model=HeatmapResponse, tags=["analytics"])
def store_heatmap(
    request: Request,
    store_id: str,
    metric_date: str | None = Query(default=None, alias="date"),
    db: Session = Depends(get_db),
) -> HeatmapResponse:
    request.state.store_id = store_id
    canonical = ensure_store_exists(db, store_id)
    return compute_heatmap(db, canonical, _parse_date_param(metric_date))


@app.get("/stores/{store_id}/anomalies", response_model=AnomalyResponse, tags=["analytics"])
def store_anomalies(
    request: Request,
    store_id: str,
    metric_date: str | None = Query(default=None, alias="date"),
    db: Session = Depends(get_db),
) -> AnomalyResponse:
    request.state.store_id = store_id
    canonical = ensure_store_exists(db, store_id)
    return compute_anomalies(db, canonical, _parse_date_param(metric_date))


@app.get("/health", response_model=HealthResponse, tags=["operations"])
def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    return build_health_response(db)


@app.get("/", tags=["operations"])
def root() -> dict[str, str]:
    return {
        "service": "store-intelligence-api",
        "version": __version__,
        "health": "/health",
        "docs": "/docs",
    }


@app.get("/headers-test", tags=["operations"])
async def headers_test() -> dict[str, bool]:
    return {"ok": True}


@app.get("/cors-test", tags=["operations"])
def cors_test() -> dict[str, str]:
    return {"status": "ok"}
