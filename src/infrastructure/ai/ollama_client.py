"""Ollama client for handling interactions with the Ollama API."""

import json
import typing
from typing import Any

import httpx

from config import settings
from src.core.schemas import HabitAdvice
from src.utils.logger import setup_logger

logger = setup_logger(__name__)
POST_REQUEST_TIMEOUT = 30


class OllamaClient:
    """Ollama client for handling interactions with the Ollama API."""

    def __init__(self, model: str = "llama3.1:latest"):
        self.model = model
        self.base_url = settings.OLLAMA_URL if settings.OLLAMA_URL else "http://localhost:11434"
        self.chat_url = f"{self.base_url}/api/chat"

    def get_payload(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """
        Gets the header needed for a POST request to the AI model.
        'stream' is set to False to get the full response in one go, and
        'format' is set to 'json' to ensure the response is in JSON format for
        easier parsing.

        :system_prompt: The system prompt to guide the AI's response
        :user_prompt: The user prompt containing the specific question or request \n        for the AI
        :return: A dictionary containing the model and messages for the AI request
        """
        return {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "format": "json",
        }

    async def get_habit_advice(self, habit_name: str, streak: int, days_missed: int) -> HabitAdvice | None:
        """
        Creates the habit advice based on response from the AI model

        :habit_name: The name of the habit for which advice is being sought
        :streak: The current streak of the user for the habit
        :days_missed: The number of days the user has missed maintaining the habit
        :return: HabitAdvice or None
        """
        system_prompt = (
            "You are a Senior Behavioral Coach. Provide a specific, actionable tip "
            "for a user who is struggling to maintain their habit streak. "
            "Return the response ONLY as a JSON object with keys: "
            "'habit_name', 'reasoning', 'advice_tip', and 'priority'."
        )
        user_prompt = (
            f"The user is struggling to maintain their habit: {habit_name}. "
            f"Their current streak is {streak} and they have missed {days_missed} days."
        )
        logger.info(f"Getting habit advice from Ollama API at {self.chat_url}")
        try:
            async with httpx.AsyncClient(timeout=POST_REQUEST_TIMEOUT) as client:
                response = await client.post(url=self.chat_url, json=self.get_payload(system_prompt, user_prompt))
                response.raise_for_status()
                raw_content = response.json()["message"]["content"]
                logger.info(f"Received response from Ollama API: {raw_content}")
                return HabitAdvice.model_validate_json(raw_content)
        except httpx.HTTPStatusError as err:
            logger.error(f"HTTP error {err.response.status_code}: {err.response.text}")
        except httpx.RequestError as err:
            logger.error(f"Error during execution of request: {err}")
        return None

    async def generate_tags(self, habit_name: str, habit_description: str) -> str:
        """
        Genereate the tags based on user input for given habit name with description

        :habit_name: The name of the habit for which tags are being generated
        :habit_description: The description of the habit for which \n        tags are being generated
        :return: A string of comma-separated tags
        """
        system_prompt = (
            "You are a productivity expert. Analyze the habit and return 3-5 relevant "
            "tags as a JSON object with a single key 'tags' containing a \n            comma-separated string. "
            "Example: {'tags': 'health, fitness, morning'}"
        )
        user_prompt = f"Habit: {habit_name}. Description: {habit_description}."
        logger.info(f"Getting habit tags from Ollama API at {self.chat_url}")
        try:
            async with httpx.AsyncClient(timeout=POST_REQUEST_TIMEOUT) as client:
                response = await client.post(url=self.chat_url, json=self.get_payload(system_prompt, user_prompt))
                response.raise_for_status()
                raw_content = response.json()["message"]["content"]
                logger.info(f"Received response from Ollama API: {raw_content}")
                tags_dict = json.loads(raw_content)
                return typing.cast(str, tags_dict.get("tags", ""))
        except httpx.HTTPStatusError as err:
            logger.error(f"HTTP error {err.response.status_code}: {err.response.text}")
        except httpx.RequestError as err:
            logger.error(f"Error during execution of request: {err}")
        return ""
