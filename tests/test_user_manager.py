"""Integration tests for AsyncUserManager - uses real database."""

from unittest.mock import patch

import pytest

from src.core.exceptions import UserNotFoundException
from src.core.habit_async import AsyncUserManager


@pytest.mark.parametrize(
    "username, email, nickname, password",
    [
        ("testuser1", "testuser1@example.com", "TestUserOne", "password123"),
        ("testuser2", "testuser2@example.com", "TestUserTwo", "password456"),
        ("testuser3", "testuser3@example.com", "TestUserThree", "password789"),
    ],
)
@pytest.mark.asyncio
async def test_create_user_with_default_habit_success(
    async_user_manager: AsyncUserManager, username: str, email: str, nickname: str, password: str
) -> None:
    """Integration test: successfully create user with default habit."""
    user = await async_user_manager.create_user_with_default_habit(username, email, nickname, password)
    assert user.username == username
    assert user.email == email
    assert user.nickname == nickname
    assert user.user_id is not None
    fetched_user = await async_user_manager.get_user_by_username(username)
    assert fetched_user.user_id == user.user_id
    habits = await async_user_manager.service.habit_repo.get_all_habits_for_user(user.user_id)
    assert len(habits) == 1
    assert habits[0].name == "Welcome Habit"
    assert habits[0].user_id == user.user_id


@pytest.mark.asyncio
async def test_create_user_with_default_habit_rollback(
    async_user_manager: AsyncUserManager, fake_user_data: tuple[str, str, str, str]
) -> None:
    """Integration test: verify transaction rollback when habit creation fails."""
    username, email, nickname, password = fake_user_data
    with patch(
        "src.core.models.HabitBase.__init__",
        side_effect=ValueError("Simulated failure"),
    ):
        with pytest.raises(ValueError, match="Simulated failure"):
            await async_user_manager.create_user_with_default_habit(username, email, nickname, password)
    with pytest.raises(UserNotFoundException):
        await async_user_manager.get_user_by_username(username)


@pytest.mark.asyncio
async def test_create_user(async_user_manager: AsyncUserManager, fake_user_data: tuple[str, str, str, str]) -> None:
    """Integration test: create a user without default habit."""
    username, email, nickname, password = fake_user_data
    user = await async_user_manager.create_user(username, email, nickname, password)
    assert user.username == username
    assert user.email == email
    habits = await async_user_manager.service.habit_repo.get_all_habits_for_user(user.user_id)
    assert len(habits) == 0


@pytest.mark.asyncio
async def test_delete_user(async_user_manager: "AsyncUserManager", fake_user_data: tuple[str, str, str, str]) -> None:
    """Integration test: delete a user from database."""
    username, email, nickname, password = fake_user_data
    user = await async_user_manager.create_user(username, email, nickname, password)
    deleted = await async_user_manager.delete_user(user.user_id)
    assert deleted is True
    with pytest.raises(UserNotFoundException):
        await async_user_manager.get_user_by_username(username)
