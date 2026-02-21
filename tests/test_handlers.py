"""Unit test for handler.py methods"""

from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from config import settings
from src.core.events.events import AchievementUnlockedEvent
from src.core.events.handlers import (
    BASE_POINTS_COMPLETION,
    Context,
    award_points,
    check_streaks,
    mocked_dynamo_db,
    send_notification,
)
from src.core.models import HabitCompletion

HABIT_COMPLETIONS = [
    HabitCompletion(habit_id=uuid4(), completed_at=datetime(2024, 2, 1, 8, 0, 0)),
    HabitCompletion(habit_id=uuid4(), completed_at=datetime(2024, 1, 31, 8, 0, 0)),
    HabitCompletion(habit_id=uuid4(), completed_at=datetime(2024, 1, 30, 8, 0, 0)),
    HabitCompletion(habit_id=uuid4(), completed_at=datetime(2024, 1, 29, 8, 0, 0)),
    HabitCompletion(habit_id=uuid4(), completed_at=datetime(2024, 1, 28, 8, 0, 0)),
    HabitCompletion(habit_id=uuid4(), completed_at=datetime(2024, 1, 27, 8, 0, 0)),
    HabitCompletion(habit_id=uuid4(), completed_at=datetime(2024, 1, 26, 8, 0, 0)),
]


@pytest.mark.asyncio
async def test_check_streaks_update_to_7_streak(mock_handler_context: Context, habit_completed_event_factory) -> None:
    """Tests check_streaks method"""
    mock_handler_context.habit_repo.get_completions_by_habit.return_value = HABIT_COMPLETIONS
    event = habit_completed_event_factory(streak_count=5)
    await check_streaks(event, mock_handler_context)
    assert mocked_dynamo_db["streak_count"] == 7
    mocked_dynamo_db.clear()


@pytest.mark.asyncio
async def test_award_points_7_days_multiplier(mock_handler_context: Context, habit_completed_event_factory) -> None:
    """Tests the award_points method"""
    seven_days_points = BASE_POINTS_COMPLETION["base_points"] * BASE_POINTS_COMPLETION["streak_multiplier"][7]
    event = habit_completed_event_factory(streak_count=7)
    await award_points(event, mock_handler_context)
    assert mocked_dynamo_db["award_points"] == seven_days_points


@pytest.mark.asyncio
async def test_award_points_30_days_multiplier(mock_handler_context: Context, habit_completed_event_factory) -> None:
    """Tests the award_points method for 30 days multiplier"""
    thirty_days_points = BASE_POINTS_COMPLETION["base_points"] * BASE_POINTS_COMPLETION["streak_multiplier"][30]
    event = habit_completed_event_factory(streak_count=30)
    await award_points(event, mock_handler_context)
    assert mocked_dynamo_db["award_points"] == thirty_days_points


@pytest.mark.asyncio
async def test_award_points_100_days_multiplier(mock_handler_context: Context, habit_completed_event_factory) -> None:
    """Tests the award_points method for 100 days multiplier"""
    hundred_days_points = BASE_POINTS_COMPLETION["base_points"] * BASE_POINTS_COMPLETION["streak_multiplier"][100]
    event = habit_completed_event_factory(streak_count=100)
    await award_points(event, mock_handler_context)
    assert mocked_dynamo_db["award_points"] == hundred_days_points


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
