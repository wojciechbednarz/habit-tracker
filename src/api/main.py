"""API application for habit-tracker."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from config import settings
from src.api.v1.routers import admin, habits, security, users
from src.core.exception_handlers import register_exception_handlers
from src.core.habit_async import AsyncUserManager
from src.core.startup import ensure_admin_exists


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[Any, Any]:
    """Run on application startup."""
    user_manager = AsyncUserManager()
    await ensure_admin_exists(user_manager)
    await user_manager.service.async_db.async_engine.dispose()
    yield


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)
app.include_router(habits.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(security.router)
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
def health() -> dict[str, str]:
    """Health check endpoint"""
    db_url: str = str(settings.DATABASE_URL)
    return {
        "status": "healthy",
        "database": db_url.split("@")[1] if "@" in db_url else "Unknown",
    }
