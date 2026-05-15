"""API application for habit-tracker."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from aws_xray_sdk.core import patch, xray_recorder
from fastapi import FastAPI
from sqlalchemy import text

from config import settings
from src.api.middleware import CustomXrayMiddleware, LoggingMiddleware, SecurityHeadersMiddleware
from src.api.v1.routers import admin, ai, habits, reports, security, users
from src.core.cache import RedisManager
from src.core.db import get_async_engine
from src.core.exception_handlers import register_exception_handlers
from src.core.habit_async import AsyncUserManager
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[Any, Any]:
    """Run on application startup."""
    user_manager = AsyncUserManager()
    await user_manager.service.async_db.async_engine.dispose()
    cache = RedisManager()
    await cache.initialize(settings.REDIS_URL)
    app.state.redis_manager = cache
    logger.info(f"XRAY_ENABLED: {settings.XRAY_ENABLED}")
    if settings.XRAY_ENABLED:
        xray_recorder.configure(
            service="habit-tracker-api",
            daemon_address="xray-daemon:2000",
            context_missing="LOG_ERROR",
        )
        patch(["requests", "botocore"])
    yield
    await cache.close()
    logger.info("Redis connection closed")


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)
app.include_router(habits.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(security.router)
app.include_router(ai.router)
app.include_router(reports.router)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CustomXrayMiddleware)
app.add_middleware(LoggingMiddleware)
register_exception_handlers(app)


@app.get("/")
def root() -> dict[str, str]:
    """Root app endpoint."""
    return {
        "app": settings.APP_NAME,
        "environment": "development" if settings.DEBUG else "production",
        "version": settings.VERSION,
    }


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint"""
    try:
        engine = get_async_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "ok"}
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "error",
            "error_class": type(e).__name__,
        }
