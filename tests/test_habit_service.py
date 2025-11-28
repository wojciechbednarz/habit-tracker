"""Unit tests for habit service functionality."""

import pytest

from src.core.habit import HabitCreate, HabitService, HabitUpdate

testdata = [
    ("Exercise", "Morning workout", "daily", False),
    ("Reading", "Read 20 pages", "daily", True),
    ("Meditation", "Meditate for 10 minutes", "daily", False),
]


@pytest.mark.parametrize("habit_name, description, frequency, mark_done", testdata)
def test_create_habit_and_check_if_exists(
    user_id, mock_db, habit_name, description, frequency, mark_done
):
    """Test creating a habit and checking its existence."""
    habit_service = HabitService(mock_db)
    new_user_id = user_id
    habit_data = HabitCreate(
        name=habit_name,
        description=description,
        frequency=frequency,
        mark_done=mark_done,
        user_id=new_user_id,
    )

    habit_service.create_habit(habit_data)
    with pytest.raises(ValueError):
        habit_service.create_habit(habit_data)


def test_update_habit_loggging(caplog, mock_db, user_id):
    """Test updating a habit and logging the update."""
    habit_service = HabitService(mock_db)
    new_user_id = user_id
    habit_data = HabitCreate(
        name="Exercise",
        description="Morning workout",
        frequency="daily",
        mark_done=False,
        user_id=new_user_id,
    )

    habit_service.create_habit(habit_data)
    updates = HabitUpdate(description="New description")
    habit_service.update_habit(
        habit_name="Exercise", updates=updates, user_id=new_user_id
    )

    log_messages = [record.message for record in caplog.records]
    assert any("Updating habit:" in message for message in log_messages)
