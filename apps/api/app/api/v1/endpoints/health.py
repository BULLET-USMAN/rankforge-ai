import time

import redis
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.schemas.health import DependencyHealth, LivenessResponse, ReadinessResponse

router = APIRouter()


@router.get("/health", response_model=LivenessResponse, tags=["Health"])
@router.get("/health/live", response_model=LivenessResponse, tags=["Health"])
def health_live():
    """Liveness probe: verifies that the FastAPI application process is up and responding."""
    return LivenessResponse(
        status="alive",
        version=settings.VERSION,
    )


@router.get("/health/ready", response_model=ReadinessResponse, tags=["Health"])
def health_ready(db: Session = Depends(get_db)):
    """
    Readiness probe: verifies connectivity to PostgreSQL database and Redis broker.
    Returns 200 if dependencies are ready, or 503 Service Unavailable if critical services are down.
    """
    dependencies = {}
    is_ready = True

    # Check Database Connectivity
    db_start = time.perf_counter()
    try:
        db.execute(text("SELECT 1"))
        db_latency = round((time.perf_counter() - db_start) * 1000, 2)
        dependencies["database"] = DependencyHealth(status="ok", latency_ms=db_latency)
    except Exception as exc:
        is_ready = False
        dependencies["database"] = DependencyHealth(
            status="unreachable",
            error=str(exc) if settings.DEBUG else "Database connection failed",
        )

    # Check Redis Connectivity
    redis_start = time.perf_counter()
    try:
        r = redis.from_url(settings.REDIS_URL, socket_timeout=2.0)
        r.ping()
        redis_latency = round((time.perf_counter() - redis_start) * 1000, 2)
        dependencies["redis"] = DependencyHealth(status="ok", latency_ms=redis_latency)
    except Exception as exc:
        is_ready = False
        dependencies["redis"] = DependencyHealth(
            status="unreachable",
            error=str(exc) if settings.DEBUG else "Redis connection failed",
        )

    response_payload = ReadinessResponse(
        status="ready" if is_ready else "not_ready",
        environment=settings.ENVIRONMENT,
        dependencies=dependencies,
    )

    if not is_ready:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=response_payload.model_dump(mode="json"),
        )

    return response_payload
