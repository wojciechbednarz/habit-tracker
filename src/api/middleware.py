""" "Middleware for API requests."""

import uuid
from collections.abc import Awaitable, Callable
from typing import Any

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to add a unique request ID to the logging context for each API request."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request[Any]], Awaitable[Response]]
    ) -> Any[Response]:
        """
        Middleware to add a unique request ID to the logging context for each API request.

        :request: The incoming HTTP request
        :call_next: The next middleware or endpoint to call
        :return: The HTTP response from the next middleware or endpoint
        """
        try:
            request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
            structlog.contextvars.bind_contextvars(request_id=request_id)
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception as e:
            logger = structlog.get_logger()
            logger.error(f"Error processing request: {e}")
            raise
        finally:
            structlog.contextvars.clear_contextvars()
