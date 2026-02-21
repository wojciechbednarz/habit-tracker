"""API endpoints related to the admin operations"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.core.habit_async import AsyncUserManager
from src.core.models import UserRole
from src.core.schemas import (
    User,
    UserAdminReadAllUsers,
    UserAdminReadUser,
    UserUpdate,
    UserWithRole,
)

from .dependencies import get_user_manager, require_admin

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users")
async def read_all_users(
    current_user: Annotated[UserWithRole, Depends(require_admin)],
    user_manager: Annotated[AsyncUserManager, Depends(get_user_manager)],
) -> UserAdminReadAllUsers:
    """GET request to read all users as admin"""
    users = await user_manager.read_all_users()
    users_data = [User.model_validate(user, from_attributes=True) for user in users]
    return UserAdminReadAllUsers(message="Reading all users successful", users=users_data, total=len(users))


@router.get("/users/{user_id}")
async def read_user(
    user_id: UUID,
    current_user: Annotated[UserWithRole, Depends(require_admin)],
    user_manager: Annotated[AsyncUserManager, Depends(get_user_manager)],
) -> UserAdminReadUser:
    """GET request to read a user as admin"""
    user = await user_manager.get_user_by_id(user_id)
    user_data = User.model_validate(user, from_attributes=True)
    return UserAdminReadUser(message=f"Reading a user with ID {user_id} successful", user=user_data)


@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: UUID,
    new_role: str,
    current_user: Annotated[UserWithRole, Depends(require_admin)],
    user_manager: Annotated[AsyncUserManager, Depends(get_user_manager)],
) -> dict[str, str]:
    """Admin usage only: Update a user's role"""
    if user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own admin role",
        )
    if new_role not in [UserRole.USER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {new_role}. Must be 'user' or 'admin'",
        )
    update = UserUpdate(role=new_role)
    await user_manager.update_user(user_id, update)
    return {"message": f"User role updated to {new_role}"}
