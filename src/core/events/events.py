from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class BaseEvent(BaseModel):
    """Base class for all events"""

    timestamp: datetime
    user_id: UUID
    event_id: UUID


class HabitCompletedEvent(BaseEvent):
    """
    Class for event when habit is completed e.g. count how many streaks there are for
    a user.
    """

    habit_id: UUID
    completed_date: datetime
    streak_count: int = Field(ge=0)


class AchievementUnlockedEvent(BaseEvent):
    """
    Class for achievements for a user
    """

    achievement_type: str
