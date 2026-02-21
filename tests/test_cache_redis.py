"""Integration tests related to testing Redis functionalities"""

from typing import Any

import pytest

from src.core.cache import RedisManager

REDIS_HABIT_TEST_DATA = [
    ("user:123:habits", [{"habit_id": "habit1", "name": "Read a book"}]),
    ("user:456:habits", [{"habit_id": "habit2", "name": "Play chess"}]),
    ("user:789:habits", [{"habit_id": "habit3", "name": "Meditation"}]),
]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_initialize(redis_instance: str) -> None:
    """Checks if redis connection is initialized successfully"""
    cache_manager = RedisManager()
    result = await cache_manager.initialize(redis_instance)
    assert result is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_close(redis_instance: str) -> None:
    """Checks if redis connection is closed successfully"""
    cache_manager = RedisManager()
    await cache_manager.initialize(redis_instance)
    close = await cache_manager.close()
    assert close is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ping(cache_manager: "RedisManager") -> None:
    """Checks if connection to redis server can be established"""
    ping = await cache_manager.service.ping()
    assert ping is True


@pytest.mark.parametrize("key, data", REDIS_HABIT_TEST_DATA)
@pytest.mark.integration
@pytest.mark.asyncio
async def test_set_object(cache_manager: "RedisManager", key: str, data: Any) -> None:
    """Checks if an object can be set in the redis server"""
    await cache_manager.service.set_object(key, data)
    result = await cache_manager.service.get_object(key)
    assert result == data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_not_existing_object(cache_manager: "RedisManager") -> None:
    """Checks if getting a non-existing object returns None"""
    key = "user:not_exist:habits"
    result = await cache_manager.service.get_object(key)
    assert result is None


@pytest.mark.parametrize("key, data", REDIS_HABIT_TEST_DATA)
@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_object(cache_manager: "RedisManager", key: str, data: Any) -> None:
    """Checks if an object can be deleted from the redis server"""
    await cache_manager.service.set_object(key, data)
    await cache_manager.service.delete_object(key)
    result = await cache_manager.service.get_object(key)
    assert result is None


# PUT (Invalidate) -> GET (New Data).
