"""Security API endpoints"""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from src.api.v1.routers.dependencies import authenticate_user, get_user_manager
from src.core.habit_async import AsyncUserManager
from src.core.schemas import Token
from src.core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
)

router = APIRouter(tags=["authentication"])


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_manager: Annotated[AsyncUserManager, Depends(get_user_manager)],
) -> Token:
    """POST request to user login"""
    user = await authenticate_user(form_data.username, form_data.password, user_manager)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.username)}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")
