"""API application for habit-tracker."""

from fastapi import FastAPI

from src.api.v1.routers import admin, habits, security, users

app = FastAPI()
app.include_router(habits.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(security.router)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint - API health check."""
    return {"message": "Habit Tracker API is running", "version": "1.0"}
