"""
Logging middleware and request timing.
"""
import time
import logging
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every request with method, path, status, and duration."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())[:8]
        start = time.perf_counter()

        # Attach request_id to request state
        request.state.request_id = request_id

        logger.info(
            f"[{request_id}] → {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.error(
                f"[{request_id}] ✗ {request.method} {request.url.path} "
                f"ERROR {exc} ({duration_ms:.1f}ms)"
            )
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            f"[{request_id}] ← {response.status_code} "
            f"{request.method} {request.url.path} ({duration_ms:.1f}ms)"
        )

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms:.1f}ms"
        return response
