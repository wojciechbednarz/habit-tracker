"""Unit test for AIService modules using property-based testing"""

from collections.abc import Callable

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from src.core.ai_service import AIService
from src.core.models import HabitBase, UserBase


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    habits=st.lists(st.builds(HabitBase), min_size=0, max_size=50),
    user_entity=st.builds(UserBase),
)
@pytest.mark.asyncio
async def test_get_user_context_pb(
    ai_service_factory: Callable[[], AIService], user_entity: UserBase, habits: list[HabitBase]
) -> None:
    """
    Test get_user_context with property-based testing to ensure it
    handles various user IDs correctly.

    :ai_service: The AIService instance to test.
    :user_id: A randomly generated UUID to use as the user ID for testing.
    :return: None
    """
    ai_service = ai_service_factory()
    ai_service.user_repo.get_by_id.return_value = user_entity
    ai_service.habit_repo.get_all_habits_for_user.return_value = habits

    result = await ai_service.get_user_context(user_entity.user_id)
    assert "user_profile" in result
    assert result["user_profile"]["user_id"] == user_entity.user_id
