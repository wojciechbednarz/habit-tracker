"""API endpoints related to the admin operations"""

from typing import Annotated

from fastapi import APIRouter, Depends

from src.core.habit_async import AsyncUserManager
from src.core.schemas import User, UserAdminRead

from .dependencies import get_user_manager

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/")
async def read_all_users(
    user_manager: Annotated[AsyncUserManager, Depends(get_user_manager)],
) -> UserAdminRead:
    """GET request to read all users as admin"""
    users = await user_manager.read_all_users()
    total = len(users)
    users_data = [User.model_validate(user, from_attributes=True) for user in users]
    return UserAdminRead(
        message="Reading all users successful", users=users_data, total=total
    )
