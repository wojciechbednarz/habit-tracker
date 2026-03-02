"""Unit test for AIService modules using property-based testing"""

from uuid import UUID

from hypothesis import given
from hypothesis import strategies as st

from src.core.cache import RedisKeys


@given(user_id=st.uuids())
def test_user_habits_cache_key_properties(user_id: UUID) -> None:
    """
    Test that the cache key properties for user habits are correctly generated.

    :user_id: A randomly generated UUID to use as the user ID for testing.
    :return: None
    """
    key = RedisKeys.user_habits_cache_key(user_id)

    assert key.startswith("user:")
    assert key.endswith(":habits")
    assert str(user_id) in key

    assert key == RedisKeys.user_habits_cache_key(user_id)


@given(user_id_a=st.uuids(), user_id_b=st.uuids())
def test_user_habits_cache_key_uniqueness(user_id_a: UUID, user_id_b: UUID) -> None:
    """
    Test that the cache key for user habits is unique for different user IDs.
    :user_id_a: A randomly generated UUID to use as the first user ID for testing.
    :user_id_b: A randomly generated UUID to use as the second user ID for testing.
    :return: None
    """
    if user_id_a != user_id_b:
        key_a = RedisKeys.user_habits_cache_key(user_id_a)
        key_b = RedisKeys.user_habits_cache_key(user_id_b)

        assert key_a != key_b
