"""
Integration tests testing API endpoints related to habit-tracker app using temporary
SQlite database and redis with testcontainers.
"""

from collections.abc import AsyncGenerator
from typing import Any, cast
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from src.core.models import HabitBase, UserBase
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


USER_TEST_DATA = [
    ("john_doe", "john@example.com", "Johnny", "password123"),
    ("jane_smith", "jane@example.com", "Janey", "mypassword"),
    ("bob_jones", "bob@example.com", "Bobby", "securepass"),
]

HABIT_TEST_DATA = [
    ("Read a book", "Read at least 30 pages", "daily"),
    ("Play chess", "Playing chess conpetively", "daily"),
    ("Meditation", "Meditate to feel better", "weekly"),
]


@pytest.mark.integration
@pytest.mark.parametrize("name, description, frequency", HABIT_TEST_DATA, ids=["book", "chess", "meditation"])
def test_get_all_habits(
    name: str, description: str, frequency: str, authenticated_as_user_api_client: TestClient
) -> None:
    """Check the response from GET request"""
    json_content = {
        "name": name,
        "description": description,
        "frequency": frequency,
    }
    response1 = authenticated_as_user_api_client.post(url="api/habits", json=json_content)
    assert response1.status_code == 200
    response2 = authenticated_as_user_api_client.get(url="api/habits")
    assert response2.status_code == 200


@pytest.mark.integration
@pytest.mark.parametrize("username, email, nickname, password", USER_TEST_DATA)
def test_create_user_positive(username, email, nickname, password, api_client: TestClient) -> None:
    """Creates the user via POST request"""
    user_content = {
        "username": username,
        "email": email,
        "nickname": nickname,
        "password": password,
    }
    response = api_client.post(url="/api/users", json=user_content)
    response_json = response.json()
    logger.info(response_json)
    expected_response = {
        "message": "User successfully created",
        "user_id": cast(UUID, response_json["user_id"]),
    }
    assert response.status_code == 200
    assert response.json() == expected_response


@pytest.mark.integration
@pytest.mark.parametrize("name, description, frequency", HABIT_TEST_DATA)
def test_create_habit_positive(
    name: str,
    description: str,
    frequency: str,
    async_test_user_sqlite: dict[str, Any],
    authenticated_as_user_api_client: TestClient,
) -> None:
    """Checks the habit data being sent via POST request"""
    json_content = {
        "email": async_test_user_sqlite["user"].email,
        "name": name,
        "description": description,
        "frequency": frequency,
    }
    response = authenticated_as_user_api_client.post(url="/api/habits", json=json_content)
    response_json = response.json()
    expected_response = {"message": "Habit created", "id": str(response_json["id"])}
    assert response.status_code == 200
    assert response.json() == expected_response


@pytest.mark.integration
def test_delete_user_positive(
    async_test_user_sqlite: dict[str, Any],
    authenticated_as_user_api_client: TestClient,
) -> None:
    """Deletes the user via DELETE request"""
    response = authenticated_as_user_api_client.delete(
        url="/api/users/me", params={"email": async_test_user_sqlite["user"].email}
    )
    assert response.status_code == 204


@pytest.mark.integration
def test_delete_habit_positive(
    async_test_habit: HabitBase,
    authenticated_as_user_api_client: TestClient,
) -> None:
    """Deletes the habit via DELETE request"""
    response = authenticated_as_user_api_client.delete(
        url=f"/api/habits/{async_test_habit.id}",
        params={"id": async_test_habit.id},
    )
    assert response.status_code == 204


@pytest.mark.integration
def test_delete_habits_positive(
    async_test_user_sqlite: dict[str, Any],
    authenticated_as_user_api_client: TestClient,
) -> None:
    """Deletes all habits for a user via DELETE request"""
    response = authenticated_as_user_api_client.delete(
        url="/api/habits/", params={"user_id": async_test_user_sqlite["user"].user_id}
    )
    assert response.status_code == 204


@pytest.mark.integration
def test_login_for_access_token_positive(
    api_client: TestClient, async_test_user_sqlite: AsyncGenerator[UserBase]
) -> None:
    """Performs positive test of user login API endpoint"""
    response = api_client.post(
        url="/token",
        data={
            "username": async_test_user_sqlite["user"].username,
            "password": async_test_user_sqlite["password"],
        },
    )
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.integration
def test_login_for_access_token_negative(
    api_client: TestClient, async_test_user_sqlite: AsyncGenerator[UserBase]
) -> None:
    """Performs negative test of user login API endpoint"""
    wrong_password = "wrongpassword"
    response = api_client.post(
        url="/token",
        data={
            "username": async_test_user_sqlite["user"].username,
            "password": wrong_password,
        },
    )
    assert response.status_code == 401


@pytest.mark.integration
def test_read_all_users_with_admin_privileges(
    authenticated_as_admin_api_client: TestClient,
) -> None:
    """Verifies if all users are read correctly for user with admin privileges"""
    response = authenticated_as_admin_api_client.get(url="/admin/users")
    assert response.status_code == 200
    assert "Reading all users successful" in response.text


@pytest.mark.integration
def test_read_all_users_without_admin_privileges(
    authenticated_as_user_api_client: TestClient,
) -> None:
    """Verifies if all users are read correctly for user without admin privileges"""
    response = authenticated_as_user_api_client.get(url="/admin/users")
    assert response.status_code == 403
    assert "Admin privileges required" in response.text


@pytest.mark.integration
def test_update_user_role_with_admin_privileges(
    async_test_user_sqlite: dict[str, Any], authenticated_as_admin_api_client: TestClient
) -> None:
    """Verifies if user role is updated correctly for user with admin privileges"""
    response = authenticated_as_admin_api_client.patch(
        url=f"admin/users/{async_test_user_sqlite['user'].user_id}/role",
        params={"new_role": "admin"},
    )
    assert response.status_code == 200
    assert "User role updated to admin" in response.text


@pytest.mark.integration
def test_update_user_role_without_admin_privileges(
    async_test_user_sqlite: dict[str, Any], authenticated_as_user_api_client: TestClient
) -> None:
    """Verifies if user role is updated correctly for user with admin privileges"""
    response = authenticated_as_user_api_client.patch(
        url=f"admin/users/{async_test_user_sqlite['user'].user_id}/role",
        params={"new_role": "admin"},
    )
    assert response.status_code == 403
    assert "Admin privileges required" in response.text


@pytest.mark.integration
def test_read_user_without_admin_privileges(
    authenticated_as_user_api_client: TestClient, async_test_user_sqlite: dict[str, Any]
) -> None:
    """Verifies if users is read correctly for user without admin privileges"""
    response = authenticated_as_user_api_client.get(url=f"/admin/users/{async_test_user_sqlite['user'].user_id}")
    assert response.status_code == 403
    assert "Admin privileges required" in response.text


@pytest.mark.integration
def test_read_user_with_admin_privileges(
    authenticated_as_admin_api_client: TestClient, async_test_user_sqlite: dict[str, Any]
) -> None:
    """Verifies if user is read for user with admin privileges"""
    response = authenticated_as_admin_api_client.get(url=f"/admin/users/{async_test_user_sqlite['user'].user_id}")
    assert response.status_code == 200
    assert f"Reading a user with ID {async_test_user_sqlite['user'].user_id} successful" in response.text


@pytest.mark.integration
@pytest.mark.parametrize("name, description, frequency", HABIT_TEST_DATA)
def test_update_habit_returns_fresh_data(
    async_test_user_sqlite: dict[str, Any],
    authenticated_as_user_api_client: TestClient,
    name: str,
    description: str,
    frequency: str,
) -> None:
    """
    Test that updating a habit returns fresh data on subsequent requests.

    This verifies the cache invalidation works correctly by checking that:
    1. After creating a habit, GET returns it
    2. After updating the habit, GET returns the updated version (not stale cache)

    This is a behavioral test - we don't check Redis internals, we verify
    the system works correctly end-to-end.
    """
    user = async_test_user_sqlite["user"]

    json_content = {
        "email": user.email,
        "name": name,
        "description": description,
        "frequency": frequency,
    }
    response_post = authenticated_as_user_api_client.post(url="/api/habits", json=json_content)
    assert response_post.status_code == 200
    habit_id = response_post.json()["id"]

    response_get = authenticated_as_user_api_client.get("/api/habits")
    assert response_get.status_code == 200
    habits = response_get.json()
    assert any(h["id"] == habit_id and h["frequency"] == frequency for h in habits)

    new_frequency = "daily"
    response_patch = authenticated_as_user_api_client.patch(
        url=f"/api/habits/{habit_id}",
        json={"frequency": new_frequency},
    )
    assert response_patch.status_code == 200

    response_get_after = authenticated_as_user_api_client.get("/api/habits")
    assert response_get_after.status_code == 200
    habits_after = response_get_after.json()

    updated_habit = next((h for h in habits_after if h["id"] == habit_id), None)
    assert updated_habit is not None, "Habit should still exist after update"
    assert updated_habit["frequency"] == new_frequency, (
        f"Should return updated frequency '{new_frequency}', not cached '{frequency}'"
    )
