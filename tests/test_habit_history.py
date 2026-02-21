"""Unit tests for habit history functionality."""

from uuid import uuid4

import pytest

from src.core.models import HabitBase
from src.core.schemas import HabitHistory

testdata = [
    {"habit_name": "Exercise", "description": "Morning workout", "frequency": "daily"},
    {"habit_name": "Swimming", "description": "Evening swim", "frequency": "weekly"},
    {
        "habit_name": "Cleaning room",
        "description": "Clean the room",
        "frequency": "weekly",
    },
]


@pytest.mark.unit
@pytest.mark.parametrize("habit", testdata)
def test_habit_history_init(habit: dict[str, str]) -> None:
    """Test initialization of HabitHistory with habits."""
    habit_obj = HabitBase(
        id=uuid4(),
        name=habit["habit_name"],
        description=habit["description"],
        frequency=habit["frequency"],
        mark_done=False,
        user_id=uuid4(),
    )
    habit_history = HabitHistory(habit_obj)
    assert habit_obj in habit_history._habits


@pytest.mark.unit
@pytest.mark.parametrize("habit", testdata)
def test_habit_history_len(habit: dict[str, str]) -> None:
    """Test length of HabitHistory."""
    habit1 = HabitBase(
        id=uuid4(),
        name=HabitBase(
            id=uuid4(),
            name=habit["habit_name"],
            description=habit["description"],
            frequency=habit["frequency"],
            mark_done=False,
            user_id=uuid4(),
        ),
    )
    habit2 = HabitBase(
        id=uuid4(),
        name=HabitBase(
            id=uuid4(),
            name=habit["habit_name"],
            description=habit["description"],
            frequency=habit["frequency"],
            mark_done=False,
            user_id=uuid4(),
        ),
    )

    habit_history = HabitHistory(habit1, habit2)
    assert len(habit_history) == 2


@pytest.mark.unit
@pytest.mark.parametrize("habit", testdata)
def test_habit_history_getitem(habit: dict[str, str]) -> None:
    """Test getting habit by index from HabitHistory."""
    habit_obj = HabitBase(
        id=uuid4(),
        name=habit["habit_name"],
        description=habit["description"],
        frequency=habit["frequency"],
        mark_done=False,
        user_id=uuid4(),
    )
    habit_history = HabitHistory(habit_obj)
    assert habit_history[0] == habit_obj
