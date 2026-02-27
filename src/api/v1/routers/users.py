"""User-related API endpoints."""

from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from src.api.v1.routers.dependencies import get_current_active_user, get_user_manager
from src.core.habit_async import AsyncUserManager
from src.core.schemas import User, UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/api/v1/users", tags=["users"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post("/")
async def create_user(
    request: UserCreate,
    user_manager: Annotated[AsyncUserManager, Depends(get_user_manager)],
) -> UserResponse:
    """Creates a user by sending a POST request"""
    user = await user_manager.create_user(request.username, request.email, request.nickname, request.password)
    return UserResponse(message="User successfully created", user_id=cast(UUID, user.user_id))


@router.put("/{user_id}")
async def update_user(
    user_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    updates: UserUpdate,
    user_manager: Annotated[AsyncUserManager, Depends(get_user_manager)],
) -> dict[str, str]:
    """Updates a user by sending a PUT request"""
    if current_user.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update user for other users",
        )
    await user_manager.update_user(user_id, updates)
    return {"message": "User updated successfully"}


@router.delete("/me", status_code=204)
async def delete_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
    user_manager: Annotated[AsyncUserManager, Depends(get_user_manager)],
) -> None:
    """Deletes a user by sending a DELETE request"""
    await user_manager.delete_user(current_user.user_id)


@router.get("/me")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """Return the current user via GET request"""
    return current_user
