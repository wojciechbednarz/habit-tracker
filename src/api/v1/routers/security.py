"""Security API endpoints"""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, OAuth2PasswordRequestForm

from config import settings
from src.api.v1.routers.dependencies import (
    authenticate_user,
    get_redis_manager,
    get_user_manager,
    refresh_token_scheme,
)
from src.core.cache import RedisManager
from src.core.habit_async import AsyncUserManager
from src.core.schemas import Token
from src.core.security import create_access_token, create_refresh_token, decode_token

router = APIRouter(tags=["authentication"])


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_manager: Annotated[AsyncUserManager, Depends(get_user_manager)],
    redis_cache: Annotated[RedisManager, Depends(get_redis_manager)],
) -> Token:
    """POST request to user login"""
    user = await authenticate_user(form_data.username, form_data.password, user_manager)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": str(user.username)}, expires_delta=access_token_expires)
    refresh_token = create_refresh_token(data={"sub": str(user.username)}, expires_delta=refresh_token_expires)
    decoded = decode_token(refresh_token)
    assert decoded is not None, "Freshly created refresh token failed to decode"
    await redis_cache.service.set_object(
        f"refresh_token:{str(user.username)}", decoded["jti"], settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60
    )
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


@router.post("/refresh", response_model=Token)
async def refresh_token(
    auth: Annotated[HTTPAuthorizationCredentials, Depends(refresh_token_scheme)],
    redis_cache: Annotated[RedisManager, Depends(get_redis_manager)],
) -> Token:
    """Refreshes the access token"""
    if not auth:
        raise HTTPException(status_code=401, detail="Missing refresh token")
    token = auth.credentials
    decoded = decode_token(token)
    if not decoded:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    username = decoded.get("sub")
    jti = decoded.get("jti")
    if not jti:
        raise HTTPException(status_code=401, detail="Token is not a valid refresh token")
    stored_jti = await redis_cache.service.get_object(f"refresh_token:{str(username)}")
    if stored_jti == jti:
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
        new_refresh_token = create_refresh_token(data={"sub": str(username)}, expires_delta=refresh_token_expires)
        new_acccess_token = create_access_token(data={"sub": str(username)}, expires_delta=access_token_expires)
        new_decoded = decode_token(new_refresh_token)
        assert new_decoded is not None, "Freshly created refresh token failed to decode"
        await redis_cache.service.set_object(
            f"refresh_token:{str(username)}", new_decoded["jti"], settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60
        )
        return Token(access_token=new_acccess_token, refresh_token=new_refresh_token, token_type="bearer")
    else:
        await redis_cache.service.delete_object(f"refresh_token:{str(username)}")
        raise HTTPException(status_code=401, detail="Token reuse detected. Please login again.")
