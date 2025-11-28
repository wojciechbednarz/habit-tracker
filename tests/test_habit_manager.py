# tests/test_habit_handler.py
from uuid import UUID

import pytest

from src.core.habit import HabitManager


@pytest.mark.parametrize(
    "name, description, frequency",
    [
        ("Exercise", "Morning workout", "daily"),
        ("Reading", "Read 20 pages", "daily"),
        ("Meditation", "Meditate for 10 minutes", "daily"),
    ],
)
def test_add_habit(
    habit_manager: HabitManager,
    user_id: UUID,
    name: str,
    description: str,
    frequency: str,
):
    """Test adding a new habit."""
    new_user_id = user_id
    habit = habit_manager.add_habit(
        habit_name=name,
        description=description,
        frequency=frequency,
        user_id=new_user_id,
    )
    assert (name, new_user_id, description, frequency) == (
        habit.name,
        habit.user_id,
        habit.description,
        habit.frequency,
    )


@pytest.mark.parametrize(
    "initial_habit",
    [
        (
            {
                "habit_name": "Exercise",
                "description": "Morning workout",
                "frequency": "daily",
            }
        ),
        (
            {
                "habit_name": "Reading",
                "description": "Read 20 pages",
                "frequency": "daily",
            }
        ),
        (
            {
                "habit_name": "Meditation",
                "description": "Meditate for 10 minutes",
                "frequency": "daily",
            }
        ),
    ],
)
def test_complete_habit(habit_manager, user_id, initial_habit):
    """Test marking a habit as done."""
    new_user_id = user_id
    new_habit_name = initial_habit["habit_name"]
    habit_manager.add_habit(**initial_habit, user_id=new_user_id)
    habit_manager.complete_habit(habit_name=new_habit_name, user_id=new_user_id)
    habits = habit_manager.list_habits(new_user_id)
    assert "✓ Done" in habits, "Habit not marked as done."


testdata = [
    {"habit_name": "Exercise", "description": "Morning workout", "frequency": "daily"},
    {"habit_name": "Reading", "description": "Read 20 pages", "frequency": "daily"},
    {
        "habit_name": "Meditation",
        "description": "Meditate for 10 minutes",
        "frequency": "daily",
    },
]


@pytest.mark.parametrize("habit_to_add", testdata)
def test_clear_all_habits(habit_manager, habit_to_add, user_id):
    """Test clearing all habits."""
    new_user_id = user_id
    habit_manager.add_habit(**habit_to_add, user_id=new_user_id)
    habit_manager.clear_all_habits()
    all_habits = habit_manager.list_habits(new_user_id)
    print(all_habits)
    assert "No habits found." in all_habits, "Habits were not cleared."


testdata = [
    {
        "habit_name": "Playing chess",
        "description": "Play for 30 minutes",
        "frequency": "daily",
    },
    {
        "habit_name": "Playing football",
        "description": "Play for 40 minutes",
        "frequency": "daily",
    },
    {
        "habit_name": "Sleeping 8 hours",
        "description": "Sleep for 8 hours",
        "frequency": "daily",
    },
]


@pytest.mark.parametrize("habit_to_add", testdata)
def test_list_habits(
    habit_manager: HabitManager, habit_to_add: dict, user_id: UUID, mock_db
):
    """Test listing all habits."""
    habit_manager.clear_all_habits()
    new_user_id = user_id
    habit_manager.add_habit(
        **habit_to_add,
        user_id=new_user_id,
    )
    habits = habit_manager.list_habits(new_user_id)
    assert habit_to_add["habit_name"] in habits, "Habits not listed correctly."
