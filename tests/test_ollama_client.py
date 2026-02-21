"""Integration tests for the OllamaClient class in the habit-tracker application."""

import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from src.core.schemas import HabitAdvice
from src.infrastructure.ai.ollama_client import OllamaClient


# Check Ollama availability once at import time
def _check_ollama() -> bool:
    """Synchronously check if Ollama is available."""
    try:
        response = httpx.get("http://localhost:11434/api/tags", timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False


OLLAMA_AVAILABLE = _check_ollama()


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(not OLLAMA_AVAILABLE, reason="Ollama is not available")
async def test_get_habit_advice() -> None:
    """
    Test the get_habit_advice method of the OllamaClient class.
    Uses the actual Ollama API to get habit advice based on a given habit name, streak,
    and days missed. Asserts that the response is a valid HabitAdvice object with the
    expected fields.
    """
    ollama_url = "http://localhost:11434"
    client = OllamaClient()
    client.base_url = ollama_url
    client.chat_url = f"{ollama_url}/api/chat"
    habit_name = "Exercise"
    streak = 5
    days_missed = 2

    advice = await client.get_habit_advice(habit_name, streak, days_missed)

    assert isinstance(advice, HabitAdvice)
    assert advice.habit_name == habit_name
    assert advice.reasoning != ""
    assert advice.advice_tip != ""
    assert isinstance(advice.priority, str)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_habit_advice_mocked() -> None:
    """
    Test the get_habit_advice method with a mocked API response.
    """
    client = OllamaClient()
    habit_name = "Exercise"
    streak = 5
    days_missed = 2

    mock_response_content = {
        "message": {
            "content": json.dumps(
                {
                    "habit_name": habit_name,
                    "reasoning": "Keep going!",
                    "advice_tip": "Try morning workouts.",
                    "priority": "High",
                }
            )
        }
    }

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = AsyncMock(
            status_code=200, json=lambda: mock_response_content, raise_for_status=lambda: None
        )

        advice = await client.get_habit_advice(habit_name, streak, days_missed)

        assert isinstance(advice, HabitAdvice)
        assert advice.habit_name == habit_name
        assert advice.reasoning == "Keep going!"
        assert advice.advice_tip == "Try morning workouts."
        assert advice.priority == "High"
