# app/core/middleware.py
"""
Centralized middleware for the application.
"""
import time
import traceback
from typing import Callable

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import APIException
from app.core.logging_config import LogConfig

logger = LogConfig.get_logger()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging all requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable):
        """Log request details and response time."""
        start_time = time.time()

        # Log request
        logger.debug(
            "Request started",
            extra={
                "event_type": "request_started",
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
            },
        )

        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Log response
            logger.info(
                "Request completed",
                extra={
                    "event_type": "request_completed",
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "process_time_ms": round(process_time * 1000, 2),
                },
            )

            # Add process time header
            response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
            return response

        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                "Request failed",
                extra={
                    "event_type": "request_failed",
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "process_time_ms": round(process_time * 1000, 2),
                },
            )
            raise


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Configure all exception handlers for the application.

    Args:
        app: FastAPI application instance
    """

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle Pydantic validation errors."""
        logger.warning(
            "Validation error",
            extra={
                "event_type": "validation_error",
                "path": request.url.path,
                "method": request.method,
                "errors": exc.errors(),
            },
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "ValidationError",
                "message": "Invalid request data",
                "details": exc.errors(),
            },
        )

    @app.exception_handler(APIException)
    async def api_exception_handler(
        request: Request, exc: APIException
    ) -> JSONResponse:
        """Handle custom API exceptions."""
        logger.warning(
            "API exception",
            extra={
                "event_type": "api_exception",
                "path": request.url.path,
                "method": request.method,
                "status_code": exc.status_code,
                "detail": exc.detail,
            },
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle unhandled exceptions."""
        logger.error(
            "Unhandled exception",
            extra={
                "event_type": "unhandled_exception",
                "path": request.url.path,
                "method": request.method,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            },
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "InternalServerError",
                "message": "An unexpected error occurred",
            },
        )
