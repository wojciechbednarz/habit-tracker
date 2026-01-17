"""Dependency injection for API routers."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError

from src.core.habit_async import AsyncHabitManager, AsyncUserManager
from src.core.models import UserBase
from src.core.schemas import TokenData, User, UserInDB, UserWithRole
from src.core.security import decode_token, verify_password
from src.utils.logger import setup_logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

logger = setup_logger(__name__)


async def get_user_manager() -> AsyncUserManager:
    """Returns user manager class for dependency injection"""
    return AsyncUserManager()


async def get_habit_manager() -> AsyncHabitManager:
    """Returns habit manager class  for dependency injection"""
    return AsyncHabitManager()


async def authenticate_user(
    username: str,
    password: str,
    user_manager: Annotated[AsyncUserManager, Depends(get_user_manager)],
) -> UserBase | None:
    """Authenticates a user given a username and password"""
    user = await user_manager.get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, str(user.hashed_password)):
        print("WRONG PASSWORD")
        return None
    return user


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_manager: Annotated[AsyncUserManager, Depends(get_user_manager)],
) -> UserInDB:
    """Returns the current user"""
    credentials_exceptions = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        if payload is None:
            raise credentials_exceptions
        username = payload.get("sub")
        if username is None:
            raise credentials_exceptions
        token_data = TokenData(username=username)
    except InvalidTokenError as exc:
        raise credentials_exceptions from exc
    user_obj = await user_manager.get_user_by_username(username=token_data.username)
    user = UserInDB(**user_obj.to_dict())
    if user is None:
        raise credentials_exceptions
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Returns the currently active user"""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_user_with_role(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserWithRole:
    """Returns the currently active user"""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return UserWithRole(**current_user.model_dump())


async def require_admin(
    current_user: Annotated[UserWithRole, Depends(get_current_user_with_role)],
) -> UserWithRole:
    """Dependency to ensure user is an admin."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required"
        )
    return current_user
