"""Unit test for handler.py methods"""

from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from config import settings
from src.core.events.events import AchievementUnlockedEvent
from src.core.events.handlers import (
    Context,
    send_notification,
)
from src.core.models import HabitCompletion
from src.core.streak_service import BASE_POINTS_COMPLETION, compute_completion_points

HABIT_COMPLETIONS = [
    HabitCompletion(habit_id=uuid4(), completed_at=datetime(2024, 2, 1, 8, 0, 0)),
    HabitCompletion(habit_id=uuid4(), completed_at=datetime(2024, 1, 31, 8, 0, 0)),
    HabitCompletion(habit_id=uuid4(), completed_at=datetime(2024, 1, 30, 8, 0, 0)),
    HabitCompletion(habit_id=uuid4(), completed_at=datetime(2024, 1, 29, 8, 0, 0)),
    HabitCompletion(habit_id=uuid4(), completed_at=datetime(2024, 1, 28, 8, 0, 0)),
    HabitCompletion(habit_id=uuid4(), completed_at=datetime(2024, 1, 27, 8, 0, 0)),
    HabitCompletion(habit_id=uuid4(), completed_at=datetime(2024, 1, 26, 8, 0, 0)),
]


def test_compute_completion_points_7_days_multiplier() -> None:
    """Tests compute_completion_points for the 7-day streak multiplier tier."""
    expected = int(BASE_POINTS_COMPLETION["base_points"] * BASE_POINTS_COMPLETION["streak_multiplier"][7])
    assert compute_completion_points(7) == expected


def test_compute_completion_points_30_days_multiplier() -> None:
    """Tests compute_completion_points for the 30-day streak multiplier tier."""
    expected = int(BASE_POINTS_COMPLETION["base_points"] * BASE_POINTS_COMPLETION["streak_multiplier"][30])
    assert compute_completion_points(30) == expected


def test_compute_completion_points_100_days_multiplier() -> None:
    """Tests compute_completion_points for the 100-day streak multiplier tier."""
    expected = int(BASE_POINTS_COMPLETION["base_points"] * BASE_POINTS_COMPLETION["streak_multiplier"][100])
    assert compute_completion_points(100) == expected


@pytest.mark.asyncio
async def test_send_notification(mock_handler_context: Context, create_user_entity) -> None:
    """Tests the send_notificaiton method"""
    user_id = uuid4()
    event = AchievementUnlockedEvent(
        user_id=user_id,
        achievement_type="Some achievement",
        timestamp=datetime.now(),
        event_id=uuid4(),
    )
    user_data = create_user_entity()
    mock_handler_context.user_repo.get_by_id = AsyncMock(return_value=user_data)
    await send_notification(event, mock_handler_context)
    mock_handler_context.ses_client.send_congratulation_email.assert_called_once_with(
        achievement_type="Some achievement",
        recipient=user_data.email,
        sender=settings.AWS_SES_SENDER_EMAIL,
    )
