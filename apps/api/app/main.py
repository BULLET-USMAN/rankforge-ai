from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.endpoints.health import router as health_router
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import logger
from app.core.middleware import RequestTracingMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Production-Oriented SEO Intelligence & Website Optimization Platform API. "
        "Engineered for multi-tenant isolation, automated technical auditing, and safe remediation."
    ),
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Custom Exception Handler for Pydantic Validation Errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning(
        f"Validation error on {request.method} {request.url.path}: {exc.errors()}",
        extra={"request_id": request_id},
    )
    # Sanitize and present clean validation feedback without leaking internal structures
    sanitized_errors = [
        {
            "field": ".".join(str(loc) for loc in err["loc"] if loc != "body"),
            "message": err["msg"],
            "type": err["type"],
        }
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Input validation failed for request payload.",
                "details": sanitized_errors,
                "request_id": request_id,
            }
        },
        headers={"X-Request-ID": request_id},
    )

# Middlewares
app.add_middleware(RequestTracingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Process-Time-Ms"],
)

# Root Health Endpoints (/health/live, /health/ready)
app.include_router(health_router)

# API v1 Router (/api/v1/...)
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
def root():
    """Service identity endpoint."""
    return {
        "service": "RankForge AI API",
        "tagline": "Search intelligence. Engineered for growth.",
        "status": "operational",
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_STR}/docs",
    }
