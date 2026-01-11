"""Security methods needed for authroziation and authentication resources via API"""

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

SECRET_KEY = "d1b57d43528e4078b9b90196437781add052e19109acbcf0f9150d250dfce652"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


password_hash = PasswordHash.recommended()


def create_access_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    """Returns encoded JSON Web Token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)
    to_encode.update({"exp": int(expire.timestamp())})
    encoded_jwt: str = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
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
        decoded_token: dict[str, Any] = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM]
        )
        return decoded_token
    except jwt.PyJWTError:
        return None
