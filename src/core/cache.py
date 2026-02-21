"""Caching using Redis"""

import json
from typing import Any
from uuid import UUID

from redis.asyncio import Redis
from redis.exceptions import RedisError

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class RedisKeys:
    """Method to generate key names for Redis data structures."""

    @staticmethod
    def user_habits_cache_key(user_id: UUID) -> str:
        """Returns key name for user habits cache."""
        return f"user:{user_id}:habits"

    @staticmethod
    def user_profile_key(user_id: UUID) -> str:
        """Returns key name for user profile."""
        return f"user:{user_id}:profile"


class RedisService:
    """Service layer of Redis memory caching"""

    def __init__(self, redis: Redis | None) -> None:  # type: ignore[type-arg]
        """Initializes redis instance and its keys"""
        self.keys = RedisKeys()
        self.redis = redis
        self.default_ttl = 3600

    async def set_object(self, key: str, data: Any, ttl: int | None = None) -> None:
        """Sets key and value pair in redis server"""
        if self.redis is None:
            raise RuntimeError("Redis instance is not initialized")
        logger.info(f"Setting cache for key: {key}")
        await self.redis.set(key, json.dumps(data), ex=self.default_ttl if not ttl else ttl)

    async def get_object(self, key: str) -> Any | None:
        """Gets value for a key from redis server"""
        if self.redis is None:
            raise RuntimeError("Redis instance is not initialized")
        logger.info(f"Getting cache for key: {key}")
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None

    async def delete_object(self, key: str) -> None:
        """Deletes a key from redis server"""
        if self.redis is None:
            raise RuntimeError("Redis instance is not initialized")
        logger.info(f"Deleting cache for key: {key}")
        await self.redis.delete(key)

    async def ping(self) -> bool:
        """Pings the redis server to check connectivity"""
        if self.redis is None:
            raise RuntimeError("Redis instance is not initialized")
        return await self.redis.ping()


class RedisManager:
    """
    Management layer of Redis memory caching.
    Currently used only for:
    GET /habits
    POST /habits
    DELETE /habits
    PATCH /habits/{habit_id}
    """

    def __init__(
        self,
        redis: Redis | None = None,  # type: ignore[type-arg]
        service: RedisService | None = None,
    ) -> None:
        """Initializes redis instance"""
        self.redis = redis
        if service:
            self.service = service
        else:
            self.service = RedisService(self.redis)

    async def initialize(self, redis_url: str) -> bool:
        """Intializes redis cache memory."""
        try:
            logger.info("Initializing Redis...")
            self.redis = await Redis.from_url(redis_url, decode_responses=True, encoding="utf-8")
            self.service = RedisService(self.redis)
            ping = await self.redis.ping()
            logger.info("Redis initialized and connected successfully.")
            return ping
        except RedisError as e:
            logger.error(f"Failed to initialize Redis: {e}")
            raise

    async def close(self) -> bool:
        """Closes the redis connection"""
        if self.redis is None:
            raise RuntimeError("Redis instance is not initialized")
        try:
            logger.info("Closing Redis connection")
            await self.redis.aclose()  # type: ignore[attr-defined]
            logger.info("Redis connection closed successfully")
            return True
        except RedisError as e:
            logger.error(f"Failed to close Redis connection: {e}")
            raise
