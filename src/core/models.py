"""SQLAlchemy models for habits. Models for Habit and User"""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase

__all__ = ["Base", "HabitBase", "UserBase", "HabitCompletion"]


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models"""

    pass


class HabitBase(Base):
    """Declarative class model for habits POST request"""

    __tablename__ = "habits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    frequency = Column(Text, nullable=False)
    mark_done = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=datetime.now(UTC))

    def __repr__(self) -> str:
        return f"Habit(name={self.name}, description={self.description}, \
        frequency={self.frequency}, mark_done={self.mark_done}, \
        created_at={self.created_at})"


class UserBase(Base):
    """Declarative class model for users"""

    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(Text, nullable=False, unique=True)
    email = Column(Text(60), unique=True, nullable=False)
    nickname = Column(Text(50), nullable=False)
    created_at = Column(DateTime, default=datetime.now(UTC))
    disabled = Column(Boolean, nullable=False, default=False)
    hashed_password = Column(Text, nullable=False)

    def __repr__(self) -> str:
        return (
            f"User(id={self.user_id}, username={self.username}, "
            f"email_address={self.email}, nickname={self.nickname}, "
            f"created_at={self.created_at})"
        )

    def to_dict(self) -> dict[str, Any]:
        """Transform database specific data to dictionary"""
        return {
            column.key: getattr(self, column.key) for column in self.__table__.columns
        }


class HabitCompletion(Base):
    """Declarative class model for habit completion records"""

    __tablename__ = "habit_completion"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    habit_id = Column(UUID(as_uuid=True), ForeignKey("habits.id"))
    completed_at = Column(DateTime, default=datetime.now(UTC))
