"""Pydantic schemas for habit tracker application."""

from collections.abc import Sequence
from datetime import datetime
from typing import overload
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)

from src.core.db import HabitBase


class HabitHistory(Sequence[HabitBase]):
    """To be used in future to store habit history e.g. how many completions
    it was for given habit and in which days.
    """

    def __init__(self, *habits: HabitBase) -> None:
        self._habits = list(habits)

    def __len__(self) -> int:
        return len(self._habits)

    @overload
    def __getitem__(self, item: int) -> HabitBase: ...
    @overload
    def __getitem__(self, item: slice) -> Sequence[HabitBase]: ...
    def __getitem__(self, item: int | slice) -> HabitBase | Sequence[HabitBase]:
        return self._habits[item]


class HabitCreate(BaseModel):
    """Schema for creating a new habit"""

    name: str = Field(..., min_length=1, max_length=30)
    description: str = Field(..., max_length=255)
    frequency: str = Field(
        ..., min_length=1, max_length=20, pattern="^(daily|weekly|monthly|yearly)$"
    )
    mark_done: bool = Field(default=False)

    @field_validator("name", "description")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Remove leading/trailing whitespace."""
        return v.strip()


class HabitUpdate(BaseModel):
    """Pydantic class describing types of the habit data"""

    name: str | None = Field(None, min_length=1, max_length=30)
    description: str | None = Field(None, max_length=255)
    frequency: str | None = Field(
        None, min_length=1, max_length=20, pattern="^(daily|weekly|monthly|yearly)$"
    )
    mark_done: bool | None = None

    @field_validator("name", "description")
    @classmethod
    def strip_whitespace(cls, v: str) -> str | None:
        """Remove leading/trailing whitespace."""
        if v is not None:
            return v.strip()
        return v


class HabitResponse(BaseModel):
    """Schema for habit response."""

    id: UUID = Field(..., description="Unique habit identifier")
    user_id: UUID = Field(..., description="User ID who owns this habit")
    name: str = Field(..., description="Habit name")
    description: str = Field(..., description="Habit description")
    frequency: str = Field(..., description="Habit frequency (daily/weekly/monthly)")
    mark_done: bool = Field(..., description="Whether habit is completed")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class User(BaseModel):
    """Pydantic base class describing types of the general user data"""

    user_id: UUID = Field(..., description="Generated user ID in form of UUID")
    username: str | None = Field(
        min_length=3,
        max_length=50,
        description="Username must be between 3 and 50 characters",
    )
    email: EmailStr = Field(..., description="Valid email address required")
    nickname: str | None = Field(
        min_length=3,
        max_length=50,
        description="Nickname must be between 3 and 50 characters",
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    disabled: bool | None = Field(
        description="Flag to check if user is currently active"
    )


class UserCreate(BaseModel):
    """
    Pydantic class describing types of the user data needed during registration process
    """

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Username must be between 3 and 50 characters",
    )
    email: EmailStr = Field(..., description="Valid email address required")
    nickname: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Nickname must be between 3 and 50 characters",
    )
    password: str = Field(
        ..., min_length=6, description="Password must be at least 6 characters"
    )


class UserResponse(BaseModel):
    """Pydantic class describing types of the user data obtained from POST request
    as response.
    """

    message: str = Field(
        ...,
        description="Message send from server to "
        "validate if user was successfully created",
        min_length=1,
    )
    user_id: UUID = Field(..., description="Generated user ID in form of UUID")


class UserUpdate(BaseModel):
    """Pydantic scheme for validation of the user data related to PUT request"""

    username: str | None = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Username must be between 3 and 50 characters",
    )
    nickname: str | None = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Nickname must be between 3 and 50 characters",
    )


class UserAdminRead(BaseModel):
    """Pydantic scheme to validate response related to getting all users data"""

    message: str
    users: list[User]
    total: int


class Token(BaseModel):
    """Pydantic class describing types of the token data"""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Pydantic class describing token data"""

    username: str


class UserInDB(User):
    """Pydantic class describing user in database"""

    hashed_password: str
