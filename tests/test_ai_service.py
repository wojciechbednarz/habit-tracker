"""Unit test for AIService modules"""

from datetime import datetime
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from src.core.ai_service import AIService
from src.core.exceptions import DatabaseException
from src.core.models import HabitBase, UserBase


@pytest.mark.parametrize(
    "habit_data, user_data",
    [
        (
            [
                HabitBase(name="Test Habit", description="Test Description", frequency="Daily", mark_done=False),
                HabitBase(name="Another Habit", description="Another Description", frequency="Weekly", mark_done=True),
            ],
            UserBase(
                user_id=UUID("00000000-0000-0000-0000-000000000000"),
                username="testuser",
                email="testuser@example.com",
                nickname="TestUser",
                created_at=datetime.now(),
            ),
        ),
        (
            [
                HabitBase(name="Another Habit", description="Another Description", frequency="Weekly", mark_done=True),
                HabitBase(name="Second Habit", description="Second Description", frequency="Monthly", mark_done=False),
            ],
            UserBase(
                user_id=UUID("11111111-1111-1111-1111-111111111111"),
                username="anotheruser",
                email="anotheruser@example.com",
                nickname="AnotherUser",
                created_at=datetime.now(),
            ),
        ),
    ],
)
@pytest.mark.asyncio
async def test_get_user_context_user_and_habit_data_returned_correctly(
    ai_service: AIService, habit_data: HabitBase, user_data: UserBase
) -> None:
    """Test that get_user_context returns the correct user and habit data."""
    ai_service.user_repo.get_by_id = AsyncMock(return_value=user_data)
    ai_service.habit_repo.get_all_habits_for_user = AsyncMock(return_value=habit_data)

    result = await ai_service.get_user_context(user_data.user_id)
    print(f"RESULT: {result}")
    assert result["user_profile"]["user_id"] == user_data.user_id
    assert result["user_profile"]["username"] == user_data.username
    assert result["habits"][0]["name"] == habit_data[0].name


@pytest.mark.asyncio
async def test_get_user_context_exception_raised_by_repo(ai_service: AIService) -> None:
    """Test that get_user_context propagates exceptions from the habit repository."""
    user_data = UserBase(
        user_id=UUID("00000000-0000-0000-0000-000000000001"),
        username="testuser",
        email="testuse1r@example.com",
        nickname="TestUser1",
        created_at=datetime.now(),
    )
    ai_service.user_repo.get_by_id = AsyncMock(return_value=user_data)
    ai_service.habit_repo.get_all_habits_for_user.side_effect = DatabaseException()
    with pytest.raises(DatabaseException):
        await ai_service.get_user_context(user_data.user_id)
