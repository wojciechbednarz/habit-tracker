"""Unit tests for habit service functionality."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.core.exceptions import HabitAlreadyExistsException
from src.core.models import HabitBase
from src.core.schemas import HabitCreate, HabitUpdate

testdata = [
    ("Exercise", "Morning workout", "daily", False),
    ("Reading", "Read 20 pages", "daily", True),
    ("Meditation", "Meditate for 10 minutes", "daily", False),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("habit_name, description, frequency, mark_done", testdata)
async def test_create_habit_success(
    mocked_habit_service,
    create_user_entity,
    habit_name,
    description,
    frequency,
    mark_done,
):
    """Test creating a habit successfully."""
    user = create_user_entity()

    expected_habit = HabitBase(
        id=uuid4(),
        user_id=user.user_id,
        name=habit_name,
        description=description,
        frequency=frequency,
        mark_done=mark_done,
    )
    mocked_habit_service.habit_repo.add.return_value = expected_habit

    habit_data = HabitCreate(
        name=habit_name,
        description=description,
        frequency=frequency,
        mark_done=mark_done,
        email=user.email,
    )

    result = await mocked_habit_service.create_habit(habit_data, user.user_id)

    mocked_habit_service.habit_repo.add.assert_called_once()
    assert result == expected_habit


@pytest.mark.asyncio
async def test_create_habit_duplicate_raises_exception(
    mocked_habit_service, create_user_entity
):
    """Test creating a duplicate habit raises HabitAlreadyExistsException."""
    user = create_user_entity()

    mocked_habit_service.habit_repo.add.side_effect = HabitAlreadyExistsException(
        "Habit already exists"
    )

    habit_data = HabitCreate(
        name="Exercise",
        description="Morning workout",
        frequency="daily",
        mark_done=False,
    )

    with pytest.raises(HabitAlreadyExistsException):
        await mocked_habit_service.create_habit(habit_data, user.user_id)


@pytest.mark.asyncio
async def test_update_habit_logging(
    caplog, mocked_habit_service, create_habit_entity, create_user_entity
):
    """Test updating a habit and logging the update."""
    user = create_user_entity()
    habit = create_habit_entity(user_id=user.user_id, name="Exercise")

    mocked_habit_service.habit_repo.get_specific_habit_for_user = AsyncMock(
        return_value=habit
    )
    mocked_habit_service.habit_repo.update.return_value = True

    updates = HabitUpdate(description="New description")
    await mocked_habit_service.update_habit(updates, habit.id)

    log_messages = [record.message for record in caplog.records]
    assert any("Updating habit:" in message for message in log_messages)
    assert any("updated successfully" in message for message in log_messages)

    mocked_habit_service.habit_repo.get_specific_habit_for_user.assert_called_once_with(
        habit.id
    )
    mocked_habit_service.habit_repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_get_all_habits_for_user(
    mocked_habit_service, create_habit_entity, create_user_entity
):
    """Test getting all habits for a specific user."""
    user = create_user_entity()
    habits = [create_habit_entity(user_id=user.user_id) for _ in range(3)]

    mocked_habit_service.habit_repo.get_all_habits_for_user.return_value = habits

    result = await mocked_habit_service.get_all_habits_for_user(user.user_id)

    assert len(result) == 3
    mocked_habit_service.habit_repo.get_all_habits_for_user.assert_called_once_with(
        user.user_id
    )


@pytest.mark.asyncio
async def test_delete_habit(mocked_habit_service, create_habit_entity):
    """Test deleting a specific habit."""
    habit = create_habit_entity()

    mocked_habit_service.habit_repo.delete.return_value = True

    result = await mocked_habit_service.delete_habit_for_specific_user(habit.id)

    assert result is True
    mocked_habit_service.habit_repo.delete.assert_called_once_with(habit.id)
