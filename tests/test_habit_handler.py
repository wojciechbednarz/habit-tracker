# tests/test_habit_handler.py
import pytest



@pytest.mark.parametrize("name, description, frequency", [
    ("Exercise", "Morning workout", "Daily"),
    ("Reading", "Read 20 pages", "Daily"),
    ("Meditation", "Meditate for 10 minutes", "Daily"),
])
def test_add_habit(habit_core, name, description, frequency):
    """Test adding a new habit."""
    habit_core.clear_habits()  # Ensure the database is clear before the test
    habit_core.add_habit(name=name, description=description, frequency=frequency)
    habits = habit_core.list_habits()
    assert any(h["name"] == name for h in habits), "Habit not added successfully."


@pytest.mark.parametrize("initial_habit, updated_habit, value_to_update", [
    (
        {"name": "Exercise", "description": "Morning workout", "frequency": "Daily"},
        {"name": "Exercise", "description": "Evening workout", "frequency": "Daily"},
        "Exercise"
    ),
    (
        {"name": "Reading", "description": "Read 20 pages", "frequency": "Daily"},
        {"name": "Reading", "description": "Read 30 pages", "frequency": "Daily"},
        "Reading"
    ),
])
def test_mark_done(habit_core, initial_habit, updated_habit, value_to_update):
    """Test marking a habit as done."""
    habit_core.clear_habits()  # Ensure the database is clear before the test
    habit_core.add_habit(**initial_habit)
    habit_core.mark_done(value_to_update)
    habits = habit_core.list_habits()
    assert any(h["name"] == value_to_update and h.get("done") for h in habits), "Habit not marked as done."