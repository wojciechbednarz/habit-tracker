"""
Integration tests for UserRepository entity manipulation methods.
Real postgres database with testcontainers usage.
"""

from collections.abc import Callable
from uuid import uuid4

import pytest

from src.core.exceptions import UserAlreadyExistsException
from src.core.models import UserBase
from src.repository.user_repository import UserRepository


@pytest.mark.integration
@pytest.mark.asyncio
async def test_add_user_success(
    user_repository_real_db: UserRepository, create_user_entity: Callable[..., UserBase]
) -> UserBase | None:
    """Tests if user is successfully added to the database"""
    user = create_user_entity()
    add_user = await user_repository_real_db.add(user)
    assert add_user == user


@pytest.mark.integration
@pytest.mark.asyncio
async def test_add_user_duplicate_email(
    user_repository_real_db: UserRepository, create_user_entity: Callable[..., UserBase]
) -> None:
    """Tests adding a user with duplicate email raises exception"""
    email = "test@example.com"
    user_1 = create_user_entity(email=email)
    await user_repository_real_db.add(user_1)
    user_2 = create_user_entity(email=email)
    with pytest.raises(UserAlreadyExistsException) as exc_info:
        await user_repository_real_db.add(user_2)
    assert "already exists" in str(exc_info.value)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_by_email_found(
    user_repository_real_db: UserRepository, create_user_entity: Callable[..., UserBase]
) -> None:
    """Tests retrieving a user by email when the user exists"""
    email = "test@example.com"
    user = create_user_entity(email=email)
    await user_repository_real_db.add(user)
    retrieved_user = await user_repository_real_db.get_by_email(email)
    assert retrieved_user is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_by_email_not_found(user_repository_real_db: UserRepository) -> None:
    """Tests retrieving a user by email when the user doesn't exist"""
    email = "test@example.com"
    retrieved_user = await user_repository_real_db.get_by_email(email)
    assert retrieved_user is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_by_username_found(
    user_repository_real_db: UserRepository, create_user_entity: Callable[..., UserBase]
) -> None:
    """Tests retrieving a user by username when the user exists"""
    username = "testuser"
    user = create_user_entity(username=username)
    await user_repository_real_db.add(user)
    retrieved_user = await user_repository_real_db.get_by_username(username)
    assert retrieved_user is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_by_username_not_found(
    user_repository_real_db: UserRepository,
) -> None:
    """Tests retrieving a user by username when the user doesn't exist"""
    username = "testuser"
    retrieved_user = await user_repository_real_db.get_by_username(username)
    assert retrieved_user is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_user_success(
    user_repository_real_db: UserRepository,
    create_user_entity: Callable[..., UserBase],
):
    """Tests updating a user's details successfully"""
    user = create_user_entity()
    added_user = await user_repository_real_db.add(user)
    update_params = {"nickname": "UpdatedNickname"}
    update = await user_repository_real_db.update(
        entity_id=added_user.user_id, params=update_params
    )
    assert update is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_user_not_found(user_repository_real_db: UserRepository):
    """Tests updating a non-existent user raises exception"""
    non_existent_user_id = uuid4()
    update_params = {"nickname": "UpdatedNickname"}
    updated_user = await user_repository_real_db.update(
        entity_id=non_existent_user_id, params=update_params
    )
    assert not updated_user


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_user_success(
    user_repository_real_db: UserRepository,
    create_user_entity: Callable[..., UserBase],
):
    """Tests deleting a user successfully"""
    user = create_user_entity()
    added_user = await user_repository_real_db.add(user)
    deleted = await user_repository_real_db.delete(entity_id=added_user.user_id)
    assert deleted


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_user_not_found(
    user_repository_real_db: UserRepository,
):
    """Tests deleting a non-existent user raises exception"""
    non_existent_user_id = uuid4()
    deleted = await user_repository_real_db.delete(entity_id=non_existent_user_id)
    assert not deleted


@pytest.mark.integration
@pytest.mark.asyncio
async def test_exists_by_email(
    user_repository_real_db: UserRepository,
    create_user_entity: Callable[..., UserBase],
):
    """Tests checking existence of user by email"""
    email = "test@example.com"
    user = create_user_entity(email=email)
    await user_repository_real_db.add(user)
    exists = await user_repository_real_db.exists_by_email(email=email)
    assert exists


@pytest.mark.integration
@pytest.mark.asyncio
async def test_exists_by_username(
    user_repository_real_db: UserRepository,
    create_user_entity: Callable[..., UserBase],
):
    """Tests checking existence of user by username"""
    username = "testuser"
    user = create_user_entity(username=username)
    await user_repository_real_db.add(user)
    exists = await user_repository_real_db.exists_by_username(username=username)
    assert exists


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_all_users(
    user_repository_real_db: UserRepository,
    create_user_entity: Callable[..., UserBase],
):
    """Tests retrieving all users"""
    user1 = create_user_entity(username="user1")
    user2 = create_user_entity(username="user2")
    await user_repository_real_db.add(user1)
    await user_repository_real_db.add(user2)
    users = await user_repository_real_db.get_all()
    assert len(users) >= 2
