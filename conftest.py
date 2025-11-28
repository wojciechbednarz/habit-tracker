"""conftest.py - Pytest fixtures for habit tracker tests."""

import pytest
from faker import Faker

from src.core.habit import HabitManager, UserManager


@pytest.fixture
def fake_data(scope="function") -> tuple[str, str, str]:
    """Generate fake user data for testing."""
    faker = Faker()
    user_data = faker.user_name(), faker.email(), faker.first_name()
    return user_data


@pytest.fixture()
def mock_db(tmp_path: str) -> str:
    """Mocks a database where habits are stored"""
    test_db = "test_habits.db"
    test_db_url = tmp_path / test_db
    test_db_url = f"sqlite:///{test_db_url}"
    return test_db_url


@pytest.fixture(scope="function")
def habit_manager(mock_db: str) -> HabitManager:
    """Create HabitManager with isolated test database."""
    manager = HabitManager(db_path=mock_db)
    yield manager
    manager.clear_all_habits()


@pytest.fixture(scope="function")
def user_manager(mock_db: str) -> UserManager:
    """Create HabitManager with isolated test database."""
    manager = UserManager(db_path=mock_db)
    yield manager


@pytest.fixture(scope="function")
def user_id(user_manager: UserManager, fake_data: tuple[str, str, str]) -> str:
    """Create a test user and return the user_id."""
    user_name, email_address, nickname = fake_data
    user = user_manager.create_user(
        user_name=user_name, email_address=email_address, nickname=nickname
    )
    return user.user_id
