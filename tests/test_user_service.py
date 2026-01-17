"""Unit tests for AsyncUserService - uses mocks, no real database."""

import pytest


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_user_with_default_habit_session_operations(
    mocked_user_service, fake_user_data
):
    """Unit test: verify session.add is called twice (user + habit)."""
    username, email, nickname, password = fake_user_data
    await mocked_user_service.create_user_with_default_habit(
        username, email, nickname, password
    )
    assert mocked_user_service._mock_session.add.call_count == 2
    mocked_user_service._mock_session.flush.assert_called_once()
