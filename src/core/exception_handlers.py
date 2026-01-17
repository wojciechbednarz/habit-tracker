"""Custom exception handlers for API endpoints"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.core.exceptions import (
    HabitAlreadyExistsException,
    HabitNotFoundException,
    UserAlreadyExistsException,
    UserNotFoundException,
)


async def user_exists_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handles user already exists exception"""
    return JSONResponse(status_code=409, content={"detail": str(exc)})


async def habit_exists_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handles habit already exists exception"""
    return JSONResponse(status_code=409, content={"detail": str(exc)})


async def user_not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handles user not found exception"""
    return JSONResponse(status_code=404, content={"detail": str(exc)})


async def habit_not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handles habit not found exception"""
    return JSONResponse(status_code=404, content={"detail": str(exc)})


def register_exception_handlers(app: FastAPI) -> None:
    """Registers all exception handlers for FastAPI"""
    app.add_exception_handler(UserNotFoundException, user_not_found_handler)
    app.add_exception_handler(HabitNotFoundException, habit_not_found_handler)
    app.add_exception_handler(HabitAlreadyExistsException, habit_exists_handler)
    app.add_exception_handler(UserAlreadyExistsException, user_exists_handler)
