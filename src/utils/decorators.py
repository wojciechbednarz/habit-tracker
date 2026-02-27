"""Decorator utility methods"""

import time
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

from src.core.cache import RedisKeys
from src.core.schemas import HabitResponse
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def cache_habits_response(
    ttl: int = 3600,
) -> Callable[
    [Callable[..., Awaitable[list[HabitResponse]]]],
    Callable[..., Awaitable[list[HabitResponse]]],
]:
    """
    Decorator to cache habits list response using Redis.
    Specifically for endpoints that return list[HabitResponse].

    :ttl: Time to live for the cache in seconds (default: 3600 seconds or 1 hour)
    :return: Decorator function
    """

    def decorator(
        func: Callable[..., Awaitable[list[HabitResponse]]],
    ) -> Callable[..., Awaitable[list[HabitResponse]]]:
        """Decorator function to wrap the method"""

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> list[HabitResponse] | Any:
            """
            Wrapper function to handle caching logic - getting and
            setting the objects in the cache memory.
            """
            redis_cache = kwargs.get("redis_cache")
            current_user = kwargs.get("current_user")
            if not redis_cache or not current_user:
                logger.warning("Proceeding without caching data...")
                return await func(*args, **kwargs)
            key = RedisKeys.user_habits_cache_key(current_user.user_id)
            cached_data = await redis_cache.service.get_object(key)
            if cached_data:
                logger.info(f"Cache hit for key: {key}")
                return cached_data
            logger.info(f"Cache miss for key: {key}")
            result = await func(*args, **kwargs)
            cached_data = [
                {
                    **item.model_dump(),
                    "id": str(item.id),
                    "user_id": str(item.user_id),
                    "created_at": str(item.created_at),
                }
                for item in result
            ]
            await redis_cache.service.set_object(key, cached_data, ttl)
            return result

        return wrapper

    return decorator


def delete_habit_cache(
    func: Callable[..., Awaitable[Any]],
) -> Callable[..., Awaitable[Any]]:
    """
    Deletes habit from the Redis cache memory.
    Specifically for endpoints that deletes and updates habits.
    """

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        """
        Wrapper function to handle caching logic - deleting object from the
        cache memory.
        """
        redis_cache = kwargs.get("redis_cache")
        current_user = kwargs.get("current_user")
        if not redis_cache or not current_user:
            logger.warning("Proceeding without caching data...")
            return await func(*args, **kwargs)
        result = await func(*args, **kwargs)
        list_key = RedisKeys.user_habits_cache_key(current_user.user_id)
        await redis_cache.service.delete_object(list_key)
        return result

    return wrapper


def timer(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator method to measure the function execution time.

    :func: Function to be wrapped
    :return: Wrapped function
    """

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        """Wrapper function for time measure"""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        calc_time = end_time - start_time
        logger.info(f"Elapsed time for the function {func.__name__} is: {calc_time:.4f}s")
        return result

    return wrapper


def cache_result(ttl: int, prefix: str) -> Callable[..., Any]:
    """
    Decorator to cache the result of a function in Redis with a specified TTL and key prefix.

    :ttl: Time to live for the cache in seconds
    :prefix: Prefix for the cache key to avoid collisions
    :return: Decorator function
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator function to wrap the method"""

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            """
            Wrapper function to handle caching logic -
            getting and setting the objects in the cache memory.
            """
            redis_cache = kwargs.get("redis_cache")
            current_user = kwargs.get("current_user")
            if not redis_cache:
                logger.warning("No Redis cache provided, skipping caching...")
                return await func(*args, **kwargs)
            if not current_user or not current_user.user_id:
                logger.warning("No user found in kwargs, skipping cache...")
                return await func(*args, **kwargs)
            redis_key = f"{prefix}:{current_user.user_id}"
            cached_data = await redis_cache.service.get_object(redis_key)
            if cached_data:
                logger.info(f"Cache hit for key: {redis_key}")
                return cached_data
            logger.info(f"Cache miss for key: {redis_key}")
            result = await func(*args, **kwargs)
            await redis_cache.service.set_object(redis_key, result, ttl)
            return result

        return wrapper

    return decorator
