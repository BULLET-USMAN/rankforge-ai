import time
import uuid
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.logging import logger


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that assigns a unique X-Request-ID, measures request duration,
    enforces request body size limits, and attaches security headers.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        # Enforce content-length safeguard
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.MAX_REQUEST_BODY_BYTES:
            logger.warning(
                f"Request body exceeded max size: {content_length} bytes",
                extra={"request_id": request_id},
            )
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={
                    "error": {
                        "code": "REQUEST_TOO_LARGE",
                        "message": "Request body exceeds allowed limit.",
                        "request_id": request_id,
                    }
                },
            )

        start_time = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                f"Unhandled exception during request {request.method} {request.url.path}: {str(exc)}",
                exc_info=True,
                extra={"request_id": request_id, "duration_ms": duration_ms},
            )
            # Safe standardized error response: never expose stack traces to client
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "An unexpected error occurred. Please contact support with this request ID.",
                        "request_id": request_id,
                    }
                },
                headers={"X-Request-ID": request_id},
            )

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Attach standard security & tracing headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-Ms"] = str(duration_ms)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        logger.info(
            f"{request.method} {request.url.path} - {response.status_code} ({duration_ms}ms)",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response
