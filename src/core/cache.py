"""Caching using Redis"""

from uuid import UUID

from redis.asyncio import Redis  # type: ignore[import-untyped]
from redis.exceptions import RedisError  # type: ignore[import-untyped]

from config import settings
from src.utils.logger import setup_logger

DEFAULT_KEY_PREFIX = "habit"

logger = setup_logger(__name__)


class Keys:
    """Method to generate key names for Redis data structures."""

    def __init__(self, prefix: str = DEFAULT_KEY_PREFIX) -> None:
        """Initializes values for Keys class"""
        self.prefix = prefix

    def habit_session(self, habit_id: UUID) -> str:
        """Creates key name for establsihing user session"""
        return f"habit:{habit_id}:session"

    def user_session(self, user_id: UUID) -> str:
        """Creates key name for establsihing user session"""
        return f"user:{user_id}:session"

    USER_SESSION = "user:{user_id}: session"
    RATE_LIMIT = "rate_limit:{ip}"
    CACHE_USER = "cache:user:{user_id}"


class CacheManager:
    """Handled caching using Redis functionalities"""

    def __init__(self) -> None:
        self.redis: Redis | None = None
        self.keys = Keys()

    async def initialize_redis(self) -> None:
        """Intializes redis"""
        try:
            logger.info("Initializing Redis...")
            self.redis = await Redis.from_url(
                settings.REDIS_URL, decode_responses=True, encoding="utf-8"
            )
            await self.redis.ping()
            logger.info("Redis initialized and connected successfully.")
        except RedisError as e:
            logger.error(f"Failed to initialize Redis: {e}")
            raise
