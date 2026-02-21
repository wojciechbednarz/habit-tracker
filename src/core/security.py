"""Security methods needed for authroziation and authentication resources via API"""

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

from config import settings

password_hash = PasswordHash.recommended()


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Returns encoded JSON Web Token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)
    to_encode.update({"exp": int(expire.timestamp())})
    assert settings.JWT_SECRET_KEY is not None, "JWT_SECRETS_KEY must be set"
    encoded_jwt: str = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies the user password"""
    result: bool = password_hash.verify(plain_password, hashed_password)
    return result


def get_password_hash(password: str) -> str:
    """Returns hashed password"""
    hashed: str = password_hash.hash(password)
    return hashed


def decode_token(token: str) -> dict[str, Any] | None:
    """Decodes JWT token"""
    try:
        assert settings.JWT_SECRET_KEY is not None, "JWT_SECRETS_KEY must be set"
        decoded_token: dict[str, Any] = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return decoded_token
    except jwt.PyJWTError:
        return None
