"""
Integration tests for HabitRepository entity manipulation methods.
Real in-memory database usage.
"""

from collections.abc import Callable
from uuid import uuid4

import pytest

from src.core.exceptions import HabitNotFoundException
from src.core.models import HabitBase
from src.repository.habit_repository import HabitRepository


@pytest.mark.asyncio
async def test_add_habit_success(
    create_habit_entity: Callable[..., HabitBase],
    habit_repository_real_db: HabitRepository,
) -> HabitBase | None:
    """Tests if habit is successfully added to the database"""
    habit = create_habit_entity()
    added_habit = await habit_repository_real_db.add(habit)
    assert added_habit == habit


@pytest.mark.asyncio
async def test_delete_habit_success(
    create_habit_entity: Callable[..., HabitBase],
    habit_repository_real_db: HabitRepository,
) -> None:
    """Tests deleting an existing habit"""
    habit = create_habit_entity()
    await habit_repository_real_db.add(habit)
    deleted = await habit_repository_real_db.delete(entity_id=habit.id)
    assert deleted


@pytest.mark.asyncio
async def test_delete_habit_not_found(
    habit_repository_real_db: HabitRepository,
) -> None:
    """Tests deleting a non-existent habit returns False"""
    non_existent_habit_id = uuid4()
    result = await habit_repository_real_db.delete(entity_id=non_existent_habit_id)
    assert result is False


@pytest.mark.asyncio
async def test_delete_all_habits_for_user(
    create_habit_entity: Callable[..., HabitBase],
    habit_repository_real_db: HabitRepository,
) -> None:
    """Tests deleting all habits for a specific user"""
    user_id = uuid4()
    habit1 = create_habit_entity(user_id=user_id)
    habit2 = create_habit_entity(user_id=user_id)
    await habit_repository_real_db.add(habit1)
    await habit_repository_real_db.add(habit2)
    deleted_count = await habit_repository_real_db.delete_all(entity_id=user_id)
    assert deleted_count == 2


@pytest.mark.asyncio
async def test_update_habit_success(
    create_habit_entity: Callable[..., HabitBase],
    habit_repository_real_db: HabitRepository,
) -> None:
    """Tests updating an existing habit"""
    habit = create_habit_entity()
    await habit_repository_real_db.add(habit)
    update_params = {"description": "Updated Description"}
    updated = await habit_repository_real_db.update(
        entity_id=habit.id, params=update_params
    )
    assert updated is True


@pytest.mark.asyncio
async def test_update_habit_not_found(
    habit_repository_real_db: HabitRepository,
) -> None:
    """Tests updating a non-existent habit raises exception"""
    non_existent_habit_id = uuid4()
    update_params = {"description": "Updated Description"}
    with pytest.raises(HabitNotFoundException) as exc_info:
        await habit_repository_real_db.update(
            entity_id=non_existent_habit_id, params=update_params
        )
    assert "not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_specific_habit_for_user(
    create_habit_entity: Callable[..., HabitBase],
    habit_repository_real_db: HabitRepository,
) -> None:
    """Tests retrieving a habit by ID when the habit exists"""
    habit = create_habit_entity()
    await habit_repository_real_db.add(habit)
    retrieved_habit = await habit_repository_real_db.get_specific_habit_for_user(
        habit.id
    )
    assert retrieved_habit.id == habit.id
    assert retrieved_habit.name == habit.name
    assert retrieved_habit.description == habit.description


@pytest.mark.asyncio
async def test_get_specific_habit_for_user_not_found(
    habit_repository_real_db: HabitRepository,
) -> None:
    """Tests retrieving a habit by ID when the habit does not exist"""
    non_existent_habit_id = uuid4()
    with pytest.raises(HabitNotFoundException) as exc_info:
        await habit_repository_real_db.get_specific_habit_for_user(
            non_existent_habit_id
        )
    assert "not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_exists_by_id(
    create_habit_entity: Callable[..., HabitBase],
    habit_repository_real_db: HabitRepository,
) -> None:
    """Tests checking existence of a habit by ID"""
    habit = create_habit_entity()
    await habit_repository_real_db.add(habit)
    exists = await habit_repository_real_db.exists_by_id(habit.id)
    assert exists is True


@pytest.mark.asyncio
async def test_get_all_habits(
    create_habit_entity: Callable[..., HabitBase],
    habit_repository_real_db: HabitRepository,
) -> None:
    """Tests retrieving all habits from the database"""
    habit1 = create_habit_entity()
    habit2 = create_habit_entity()
    await habit_repository_real_db.add(habit1)
    await habit_repository_real_db.add(habit2)
    all_habits = await habit_repository_real_db.get_all()
    assert len(all_habits) >= 2
