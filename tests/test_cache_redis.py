"""Integration tests related to testing Redis functionalities"""

import pytest

from src.core.cache import CacheManager


@pytest.mark.integration
@pytest.mark.asyncio
async def test_redis_connection(redis_client: str) -> None:
    """Checks if connection to redis server can be established"""
    cache = CacheManager()
    cache.redis = redis_client
    ping = await cache.redis.ping()
    assert ping is True
