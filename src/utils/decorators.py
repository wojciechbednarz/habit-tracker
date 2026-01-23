"""Decorator utility methods"""

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

    Args:
        ttl: Time to live in seconds. Defaults to 3600.
    """

    def decorator(
        func: Callable[..., Awaitable[list[HabitResponse]]],
    ) -> Callable[..., Awaitable[list[HabitResponse]]]:
        """Decorator function to wrap the method"""

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> list[HabitResponse] | Any:
            """Wrapper function to handle caching logic."""
            redis_manager = kwargs.get("redis_cache")
            current_user = kwargs.get("current_user")
            if not redis_manager or not current_user:
                logger.warning("Proceeding without caching data...")
                return await func(*args, **kwargs)
            key = RedisKeys.user_habits_cache_key(current_user.user_id)
            cached_data = await redis_manager.service.get_object(key)
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
            await redis_manager.service.set_object(key, cached_data, ttl)
            return result

        return wrapper

    return decorator
