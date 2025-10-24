"""Middleware for capturing structured request and response logs."""

from __future__ import annotations

import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.core.config import settings
from app.core.logging import api_logger
from app.monitoring.metrics import api_request_duration, api_requests_total


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Record inbound API requests and their responses."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.perf_counter()
        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"

        api_logger.info(
            "API request received",
            method=method,
            path=path,
            client_ip=client_ip,
            user_agent=request.headers.get("user-agent", "unknown"),
        )

        try:
            response = await call_next(request)
        except Exception as exc:  # pragma: no cover - handled by FastAPI exception handlers
            duration = time.perf_counter() - start_time
            api_logger.error(
                "API request failed",
                method=method,
                path=path,
                client_ip=client_ip,
                duration_ms=round(duration * 1000, 2),
                error=str(exc),
            )
            if settings.enable_metrics:
                api_requests_total.labels(method=method, endpoint=path, status="error").inc()
                api_request_duration.labels(method=method, endpoint=path).observe(duration)
            raise

        duration = time.perf_counter() - start_time
        api_logger.info(
            "API request completed",
            method=method,
            path=path,
            client_ip=client_ip,
            status_code=response.status_code,
            duration_ms=round(duration * 1000, 2),
        )

        if settings.enable_metrics:
            api_requests_total.labels(
                method=method,
                endpoint=path,
                status=str(response.status_code),
            ).inc()
            api_request_duration.labels(method=method, endpoint=path).observe(duration)

        return response


__all__ = ["RequestLoggingMiddleware"]
