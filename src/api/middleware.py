""" "Middleware for API requests."""

import uuid
from collections.abc import Awaitable, Callable, MutableMapping
from typing import Any

import structlog
from aws_xray_sdk.core import xray_recorder
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send
from structlog.stdlib import BoundLogger

from config import settings

logger: BoundLogger = structlog.get_logger()

SKIP_PATHS: set[str] = {"/health", "/docs", "/openapi.json"}


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to add a unique request ID to the logging context for each API request."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
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
            logger.exception(f"Error processing request: {e}")
            raise
        finally:
            structlog.contextvars.clear_contextvars()


class CustomXrayMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        Calls the ASGI application with AWS X-Ray tracing for API requests.
        :scope: The ASGI scope for the incoming request
        :receive: The ASGI receive function
        :send: The ASGI send function
        :return: None
        """
        if not scope["type"] == "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if path in SKIP_PATHS:
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        method = request.method
        subsegment = xray_recorder.begin_subsegment(
            name=f"{method} {path}",
        )
        if subsegment:
            subsegment.put_http_meta("url", str(request.url))
            subsegment.put_http_meta("method", method)

        async def send_wrapper(message: MutableMapping[str, Any]) -> None:
            """"""
            if message["type"] == "http.response.start":
                status = message.get("status", 200)
                if subsegment:
                    subsegment.put_http_meta("status", status)
                headers = list(message.get("headers", []))
                if subsegment:
                    headers.append(
                        (b"x-amzn-trace-id", f"Root={subsegment.trace_id}".encode()),
                    )
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as err:
            if subsegment:
                subsegment.add_exception(err, getattr(err, "__traceback__", None))
            logger.exception("Error processing request in X-Ray middleware", error=str(err))
            raise
        finally:
            xray_recorder.end_subsegment()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to API responses."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Middleware to add security headers to API responses.

        Puts the security fields into the request metadata.
        Security headers:
        - X-Content-Type-Options: Prevents MIME type sniffing.
        - X-Frame-Options: Prevents clickjacking.
        - Strict-Transport-Security: Enforces HTTPS.

        :request: The incoming HTTP request
        :call_next: The next middleware or endpoint to call
        :return: The HTTP response from the next middleware or endpoint
        """
        try:
            response = await call_next(request)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            if request.url.scheme == "https":
                response.headers["Strict-Transport-Security"] = (
                    f"max-age={settings.STRICT_TRANSPORT_SECURITY_MAX_AGE_ONE_YEAR}; includeSubDomains"
                )
            return response
        except Exception as err:
            logger.exception(f"Error encountere during handling security middleware: {err}")
            raise
