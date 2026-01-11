"""Testing API endpoints related to habit-tracker app"""

from collections.abc import AsyncGenerator
from typing import cast
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from src.core.habit_async import AsyncUserManager
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


@pytest.mark.parametrize(
    "name, description, frequency", HABIT_TEST_DATA, ids=["book", "chess", "meditation"]
)
def test_get_all_habits(name, description, frequency, authenticated_api_client):
    """Check the response from GET request"""
    json_content = {
        "name": name,
        "description": description,
        "frequency": frequency,
    }
    response1 = authenticated_api_client.post(url="api/habits", json=json_content)
    assert response1.status_code == 200
    response2 = authenticated_api_client.get(url="api/habits")
    assert response2.status_code == 200


@pytest.mark.parametrize("username, email, nickname, password", USER_TEST_DATA)
def test_create_user_positive(
    username, email, nickname, password, api_client: TestClient
) -> None:
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


@pytest.mark.parametrize("name, description, frequency", HABIT_TEST_DATA)
def test_create_habit_positive(
    name: str,
    description: str,
    frequency: str,
    async_test_user: AsyncUserManager,
    authenticated_api_client: TestClient,
):
    """Checks the habit data being sent via POST request"""
    json_content = {
        "email": async_test_user.email,
        "name": name,
        "description": description,
        "frequency": frequency,
    }
    response = authenticated_api_client.post(url="/api/habits", json=json_content)
    response_json = response.json()
    expected_response = {"message": "Habit created", "id": str(response_json["id"])}
    assert response.status_code == 200
    assert response.json() == expected_response


def test_delete_user_positive(
    async_test_user: AsyncUserManager, authenticated_api_client: TestClient
) -> None:
    """Deletes the user via DELETE request"""
    response = authenticated_api_client.delete(
        url="/api/users", params={"email": async_test_user.email}
    )
    assert response.status_code == 204


def test_delete_habit_positive(
    async_test_habit: HabitBase,
    authenticated_api_client: TestClient,
) -> None:
    """Deletes the habit via DELETE request"""
    response = authenticated_api_client.delete(
        url=f"/api/habits/{async_test_habit.id}",
        params={"id": async_test_habit.id},
    )
    assert response.status_code == 204


def test_delete_habits_positive(
    async_test_user: UserBase,
    authenticated_api_client: TestClient,
) -> None:
    """Deletes all habits for a user via DELETE request"""
    response = authenticated_api_client.delete(
        url="/api/habits/", params={"user_id": async_test_user.user_id}
    )
    assert response.status_code == 204


def test_login_for_access_token_positive(
    api_client: TestClient, async_test_user: AsyncGenerator[UserBase]
) -> None:
    """Performs positive test of user login API endpoint"""
    response = api_client.post(
        url="/token",
        data={
            "username": async_test_user.username,
            "password": async_test_user.password,
        },
    )
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_for_access_token_negative(
    api_client: TestClient, async_test_user: AsyncGenerator[UserBase]
) -> None:
    """Performs negative test of user login API endpoint"""
    wrong_password = "wrongpassword"
    response = api_client.post(
        url="/token",
        data={
            "username": async_test_user.username,
            "password": wrong_password,
        },
    )
    assert response.status_code == 401
