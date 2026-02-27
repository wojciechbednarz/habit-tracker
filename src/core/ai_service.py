"""
Methods related to fetching the data for the AI model. Fetches habit and user data
asynchronously to have a broad context for AI and to speed up the execution.
"""

import asyncio
from typing import Any
from uuid import UUID

from src.repository.habit_repository import HabitRepository
from src.repository.user_repository import UserRepository
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class AIService:
    """Service for fetching data for the AI model."""

    def __init__(self, user_repo: UserRepository, habit_repo: HabitRepository):
        self.user_repo = user_repo
        self.habit_repo = habit_repo

    async def get_user_context(self, user_id: UUID) -> dict[str, Any]:
        """
        Fetches user and habit data for the given user ID asynchronously.

        :user_id: The ID of the user to fetch data for.
        :returns: A dictionary containing user and habit data.
        """
        logger.info(f"Getting user context async for user_id: {user_id}")
        user_data, habit_data = await asyncio.gather(
            self.user_repo.get_by_id(user_id), self.habit_repo.get_all_habits_for_user(user_id)
        )
        if not user_data:
            logger.warning(f"No user found for user_id: {user_id}")
            return {}
        user_dict = user_data.to_dict()
        habit_list = [habit.to_dict() for habit in habit_data]
        user_context = {"user_profile": {**user_dict}, "habits": habit_list}
        return user_context
