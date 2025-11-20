"""conftest.py - Pytest fixtures for habit tracker tests."""

import random
from unittest.mock import MagicMock
import pytest
from src.core.habit import HabitCore
from src.core.habit import HabitHandler


@pytest.fixture
def mock_habit_data():
    """Generate mock habit data."""
    return {
        "name": "TestHabit",
        "description": "Test description for habit",
        "frequency": random.choice(["Daily", "Weekly", "Monthly"]),
        "done": random.choice([True, False]),
    }


@pytest.fixture
def mock_db():
    """Mocks a database where habits are stored"""
    return MagicMock()


@pytest.fixture
def habit_core(tmp_path, monkeypatch):
    """Create HabitCore with isolated test database."""
    test_db = tmp_path / "test_habits.db"
    monkeypatch.setattr("src.core.habit.DATABASE_NAME", str(test_db))
    core = HabitCore(user_data="test_user")
    core.initialize_database()
    yield core
    core.clear_habits()


@pytest.fixture
def habit_handler(mock_habit_data):
    """Fixture for HabitHandler with mock habit data."""
    return HabitHandler(mock_habit_data)
