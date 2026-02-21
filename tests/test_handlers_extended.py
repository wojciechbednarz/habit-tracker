"""Extended Unit tests for handler.py methods"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from src.core.events.events import AchievementUnlockedEvent
from src.core.events.handlers import (
    Context,
    _check_habit_consecutive_days,
    award_points,
    mocked_dynamo_db,
)
from src.core.models import HabitCompletion


@pytest.mark.unit
def test_check_habit_consecutive_days_basic() -> None:
    """Tests _check_habit_consecutive_days with normal daily completions"""
    completions = [
        HabitCompletion(habit_id=uuid4(), completed_at=datetime(2024, 2, 5, 8, 0, 0)),
        HabitCompletion(habit_id=uuid4(), completed_at=datetime(2024, 2, 4, 8, 0, 0)),
        HabitCompletion(habit_id=uuid4(), completed_at=datetime(2024, 2, 3, 8, 0, 0)),
    ]
    assert _check_habit_consecutive_days(completions) == 3


@pytest.mark.unit
def test_check_habit_consecutive_days_with_same_day() -> None:
    """Tests _check_habit_consecutive_days with multiple completions on same day"""
    completions = [
        HabitCompletion(habit_id=uuid4(), completed_at=datetime(2024, 2, 5, 12, 0, 0)),
        HabitCompletion(habit_id=uuid4(), completed_at=datetime(2024, 2, 5, 8, 0, 0)),
        HabitCompletion(habit_id=uuid4(), completed_at=datetime(2024, 2, 4, 8, 0, 0)),
    ]
    # Current implementation skips diff == 0, so streak should be 2
    assert _check_habit_consecutive_days(completions) == 2


@pytest.mark.unit
def test_check_habit_consecutive_days_with_gap() -> None:
    """Tests _check_habit_consecutive_days with a gap that breaks the streak"""
    completions = [
        HabitCompletion(habit_id=uuid4(), completed_at=datetime(2024, 2, 5, 8, 0, 0)),
        HabitCompletion(habit_id=uuid4(), completed_at=datetime(2024, 2, 3, 8, 0, 0)),
        HabitCompletion(habit_id=uuid4(), completed_at=datetime(2024, 2, 2, 8, 0, 0)),
    ]
    # Gap between 5th and 3rd breaks streak, should be 1
    assert _check_habit_consecutive_days(completions) == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_check_streaks_triggers_achievement(mock_handler_context: Context, habit_completed_event_factory) -> None:
    """Tests check_streaks triggers AchievementUnlockedEvent for milestones"""
    # 7-day streak
    completions = [HabitCompletion(habit_id=uuid4(), completed_at=datetime.now() - timedelta(days=i)) for i in range(7)]
    mock_handler_context.habit_repo.get_completions_by_habit.return_value = completions

    event = habit_completed_event_factory(streak_count=6)

    # We need to mock dispatch to see if it was called with AchievementUnlockedEvent
    with patch("src.core.events.dispatcher.dispatch", new_callable=AsyncMock) as mock_dispatch:
        from src.core.events.handlers import check_streaks

        await check_streaks(event, mock_handler_context)

        # Check if dispatch was called
        assert mock_dispatch.called
        # Check the type of the first argument of the first call
        args, _ = mock_dispatch.call_args
        assert isinstance(args[0], AchievementUnlockedEvent)
        assert args[0].achievement_type == "1 Week Streak"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_award_points_multipliers(mock_handler_context: Context, habit_completed_event_factory) -> None:
    """Verify correct point multipliers are applied in award_points"""
    # Base points
    event = habit_completed_event_factory(streak_count=1)
    await award_points(event, mock_handler_context)
    assert mocked_dynamo_db["award_points"] == 10

    # 7-day multiplier (2.0x)
    event = habit_completed_event_factory(streak_count=7)
    await award_points(event, mock_handler_context)
    assert mocked_dynamo_db["award_points"] == 20

    # 30-day multiplier (5.0x)
    event = habit_completed_event_factory(streak_count=30)
    await award_points(event, mock_handler_context)
    assert mocked_dynamo_db["award_points"] == 50

    # 100-day multiplier (10.0x)
    event = habit_completed_event_factory(streak_count=100)
    await award_points(event, mock_handler_context)
    assert mocked_dynamo_db["award_points"] == 100
