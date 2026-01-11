"""Unit tests for the HabitManager class."""

from unittest.mock import AsyncMock

import pytest

from src.core.schemas import HabitUpdate


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "name, description, frequency",
    [
        ("Exercise", "Morning workout", "daily"),
        ("Reading", "Read 20 pages", "daily"),
        ("Meditation", "Meditate for 10 minutes", "daily"),
    ],
)
async def test_add_habit(
    mocked_habit_manager,
    create_user_entity,
    create_habit_entity,
    name: str,
    description: str,
    frequency: str,
):
    """Test adding a new habit through manager layer."""
    user = create_user_entity()
    expected_habit = create_habit_entity(
        user_id=user.user_id, name=name, description=description, frequency=frequency
    )

    mocked_habit_manager.service.habit_repo.add.return_value = expected_habit

    habit = await mocked_habit_manager.add_habit(
        habit_name=name,
        description=description,
        frequency=frequency,
        user_id=user.user_id,
    )

    assert habit.name == name
    assert habit.description == description
    assert habit.frequency == frequency
    assert habit.user_id == user.user_id

    mocked_habit_manager.service.habit_repo.add.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "initial_habit",
    [
        {
            "habit_name": "Exercise",
            "description": "Morning workout",
            "frequency": "daily",
        },
        {"habit_name": "Reading", "description": "Read 20 pages", "frequency": "daily"},
        {
            "habit_name": "Meditation",
            "description": "Meditate for 10 minutes",
            "frequency": "daily",
        },
    ],
)
async def test_complete_habit(mocked_habit_manager, create_habit_entity, initial_habit):
    """Test marking a habit as done through manager layer."""
    habit = create_habit_entity(**initial_habit)

    mocked_habit_manager.service.habit_repo.get_specific_habit_for_user.return_value = (
        habit
    )
    mocked_habit_manager.service.habit_repo.update = AsyncMock(return_value=True)

    await mocked_habit_manager.complete_habit(habit_id=habit.id, mark_done=True)

    mocked_habit_manager.service.habit_repo.update.assert_called_once_with(
        habit.id, {"mark_done": True}
    )


@pytest.mark.asyncio
async def test_clear_all_habits(mocked_habit_manager):
    """Test clearing all habits through manager layer."""
    mocked_habit_manager.service.habit_repo.execute_query.return_value = 5

    await mocked_habit_manager.clear_all_habits()

    mocked_habit_manager.service.habit_repo.execute_query.assert_called_once_with(
        "DELETE FROM habits"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "habit_data",
    [
        {
            "name": "Playing chess",
            "description": "Play for 30 minutes",
            "frequency": "daily",
        },
        {
            "name": "Playing football",
            "description": "Play for 40 minutes",
            "frequency": "daily",
        },
        {
            "name": "Sleeping 8 hours",
            "description": "Sleep for 8 hours",
            "frequency": "daily",
        },
    ],
)
async def test_get_all_habits_for_user(
    mocked_habit_manager, create_user_entity, create_habit_entity, habit_data
):
    """Test getting all habits for a user through manager layer."""
    user = create_user_entity()
    habits = [create_habit_entity(user_id=user.user_id, **habit_data)]

    mocked_habit_manager.service.habit_repo.get_all_habits_for_user.return_value = (
        habits
    )

    result = await mocked_habit_manager.get_all_habits_for_user(user.user_id)

    assert len(result) == 1
    assert result[0].name == habit_data["name"]

    mocked_habit_manager.service.habit_repo.get_all_habits_for_user.assert_called_once_with(
        user.user_id
    )


@pytest.mark.asyncio
async def test_delete_habit(mocked_habit_manager, create_habit_entity):
    """Test deleting a specific habit through manager layer."""
    habit = create_habit_entity()

    mocked_habit_manager.service.habit_repo.delete.return_value = True

    result = await mocked_habit_manager.delete_habit(habit.id)

    assert result is True
    mocked_habit_manager.service.habit_repo.delete.assert_called_once_with(habit.id)


@pytest.mark.asyncio
async def test_update_habit(mocked_habit_manager, create_habit_entity):
    """Test updating a habit through manager layer."""
    habit = create_habit_entity(name="Exercise")

    mocked_habit_manager.service.habit_repo.get_specific_habit_for_user = AsyncMock(
        return_value=habit
    )
    mocked_habit_manager.service.habit_repo.update.return_value = True

    updates = HabitUpdate(description="Updated description")

    result = await mocked_habit_manager.update_habit(updates, habit.id)

    assert result is True
    mocked_habit_manager.service.habit_repo.update.assert_called_once()
