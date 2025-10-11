import pytest
from core.habit import HabitCore
from core.habit import HabitHandler


@pytest.fixture
def habit_core():
    return HabitCore()


@pytest.fixture
def habit_handler():
    return HabitHandler()