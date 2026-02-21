"""SQLAlchemy models for habits. Models for Habit and User"""

import uuid
from enum import StrEnum
from typing import Any

from sqlalchemy import VARCHAR, Boolean, Column, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase

__all__ = ["Base", "HabitBase", "UserBase", "HabitCompletion"]


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models"""

    pass


class UserRole(StrEnum):
    """User role for authorization"""

    USER = "user"
    ADMIN = "admin"


class HabitBase(Base):
    """Declarative class model for habits POST request"""

    __tablename__ = "habits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    name = Column(VARCHAR, nullable=False)
    description = Column(VARCHAR, nullable=False)
    frequency = Column(VARCHAR, nullable=False)
    mark_done = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    tags = Column(VARCHAR, nullable=True)

    def __repr__(self) -> str:
        return f"Habit(name={self.name}, description={self.description}, \
        frequency={self.frequency}, mark_done={self.mark_done}, \
        created_at={self.created_at})"


class UserBase(Base):
    """Declarative class model for users"""

    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(VARCHAR, nullable=False, unique=True)
    email = Column(VARCHAR(60), unique=True, nullable=False)
    nickname = Column(VARCHAR(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    disabled = Column(Boolean, nullable=False, default=False)
    hashed_password = Column(VARCHAR, nullable=False)
    role = Column(String(20), nullable=False, default=UserRole.USER)

    def __repr__(self) -> str:
        return (
            f"User(id={self.user_id}, username={self.username}, "
            f"email_address={self.email}, nickname={self.nickname}, "
            f"role={self.role}, created_at={self.created_at})"
        )

    def to_dict(self) -> dict[str, Any]:
        """Transform database specific data to dictionary"""
        return {column.key: getattr(self, column.key) for column in self.__table__.columns}


class HabitCompletion(Base):
    """Declarative class model for habit completion records"""

    __tablename__ = "habit_completion"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    habit_id = Column(UUID(as_uuid=True), ForeignKey("habits.id"))
    completed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
