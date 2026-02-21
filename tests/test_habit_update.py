"""Unit tests for habit update functionality."""

import pytest

from src.core.schemas import HabitUpdate

testdata = [
    (" Running ", "  Evening run in the park   "),
    (" Yoga ", "Morning yoga session  "),
    (" Journaling  ", "Write daily journal  "),
]


@pytest.mark.unit
@pytest.mark.parametrize("name, description", testdata)
def test_strip_whitespace_not_none(name: str, description: str) -> None:
    """Test that whitespace is stripped from habit update parameters."""
    habit_update = HabitUpdate()

    stripped_name = habit_update.strip_whitespace(name)
    stripped_description = habit_update.strip_whitespace(description)

    assert name.strip() == stripped_name
    assert description.strip() == stripped_description


def test_strip_whitespace_none() -> None:
    """Test that None input returns None for strip_whitespace."""
    habit_update = HabitUpdate()

    assert habit_update.strip_whitespace(None) is None
