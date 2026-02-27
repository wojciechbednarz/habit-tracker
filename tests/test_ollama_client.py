"""Integration tests for the OllamaClient class in the habit-tracker application."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from src.core.schemas import HabitAdvice
from src.infrastructure.ai.ai_client import OllamaClient


# Check Ollama availability once at import time
def _check_ollama() -> bool:
    """Synchronously check if Ollama is available."""
    try:
        response = httpx.get("http://localhost:11434/api/tags", timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False


OLLAMA_AVAILABLE = _check_ollama()


@pytest.mark.parametrize(
    ("habit_name, streak, days_missed"),
    [
        ("Exercise", 5, 2),
        ("Meditation", 10, 0),
        ("Reading", 3, 5),
    ],
)
@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(not OLLAMA_AVAILABLE, reason="Ollama is not available")
async def test_get_habit_advice(ollama_client: OllamaClient, habit_name: str, streak: int, days_missed: int) -> None:
    """
    Test the get_habit_advice method of the OllamaClient class.
    Uses the actual Ollama API to get habit advice based on a given habit name, streak,
    and days missed. Asserts that the response is a valid HabitAdvice object with the
    expected fields.
    """

    advice = await ollama_client.get_habit_advice(habit_name, streak, days_missed)

    assert isinstance(advice, HabitAdvice)
    assert advice.habit_name == habit_name
    assert advice.reasoning != ""
    assert advice.advice_tip != ""
    assert isinstance(advice.priority, str)


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(not OLLAMA_AVAILABLE, reason="Ollama is not available")
async def test_get_general_coaching(ollama_client: OllamaClient, user_context: dict) -> None:
    """
    Test the get_general_coaching method of the OllamaClient class.
    Uses the actual Ollama API to get habit advice based on a given habit name, streak,
    and days missed. Asserts that the response is a valid HabitAdvice object with the
    expected fields.
    """

    advice = await ollama_client.get_general_coaching(user_context)
    assert isinstance(advice, HabitAdvice)
    assert advice.habit_name == user_context["habits"][0]["name"]
    assert advice.reasoning != ""
    assert advice.advice_tip != ""
    assert isinstance(advice.priority, str)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_habit_advice_mocked(ollama_client: OllamaClient, mock_ai_model_response_content: dict) -> None:
    """
    Test the get_habit_advice method with a mocked API response.
    """
    habit_name = "Exercise"
    streak = 5
    days_missed = 2

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = AsyncMock(
            status_code=200, json=lambda: mock_ai_model_response_content, raise_for_status=lambda: None
        )

        advice = await ollama_client.get_habit_advice(habit_name, streak, days_missed)

        assert isinstance(advice, HabitAdvice)
        assert advice.habit_name == habit_name
        assert advice.reasoning == "Keep going!"
        assert advice.advice_tip == "Try morning workouts."
        assert advice.priority == "High"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_general_coaching_mocked(
    ollama_client: OllamaClient, mock_ai_model_response_content: dict, user_context: dict
) -> None:
    """
    Test the get_general_coaching method with a mocked API response.
    """
    habit_name = "Exercise"

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = AsyncMock(
            status_code=200, json=lambda: mock_ai_model_response_content, raise_for_status=lambda: None
        )

        advice = await ollama_client.get_general_coaching(user_context)

        assert isinstance(advice, HabitAdvice)
        assert advice.habit_name == habit_name
        assert advice.reasoning == "Keep going!"
        assert advice.advice_tip == "Try morning workouts."
        assert advice.priority == "High"
