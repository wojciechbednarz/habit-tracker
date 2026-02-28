"""AI-related endpoints for the Habit Tracker API. This module defines routes that
interact with the AI service to provide insights and advice on user habits, such as
identifying at-risk habits and generating personalized coaching advice based on
user data and habit performance."""

import asyncio
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from src.api.v1.routers.dependencies import (
    get_ai_service,
    get_current_active_user,
    get_habit_manager,
    get_ollama_client,
    get_redis_manager,
)
from src.core.ai_service import AIService
from src.core.cache import RedisManager
from src.core.habit_async import AsyncHabitManager
from src.core.schemas import HabitAdvice, HabitResponse, User
from src.infrastructure.ai.ai_client import OllamaClient
from src.utils.decorators import cache_result, timer

router = APIRouter(prefix="/api/v1/ai", tags=["habits"])


@router.get("/advice")
@timer
@cache_result(ttl=3600, prefix="ai_general_advice")
async def get_ai_advice(
    current_user: Annotated[User, Depends(get_current_active_user)],
    ai_service: Annotated[AIService, Depends(get_ai_service)],
    ollama_client: Annotated[OllamaClient, Depends(get_ollama_client)],
    redis_cache: Annotated[RedisManager, Depends(get_redis_manager)],
) -> HabitAdvice:
    user_context = await ai_service.get_user_context(current_user.user_id)
    general_advice = await ollama_client.get_general_coaching(user_context)
    if not general_advice:
        raise HTTPException(status_code=503, detail="AI service unavailable")
    return general_advice


@router.get("/at-risk")
@timer
@cache_result(ttl=3600, prefix="ai_at_risk_coaching")
async def get_at_risk_habits_ai_coach(
    current_user: Annotated[User, Depends(get_current_active_user)],
    habit_manager: Annotated[AsyncHabitManager, Depends(get_habit_manager)],
    ollama_client: Annotated[OllamaClient, Depends(get_ollama_client)],
    redis_cache: Annotated[RedisManager, Depends(get_redis_manager)],
) -> list[dict[str, Any]]:
    """
    Gets all 'at risk' habits list with AI-generated advice by sending a GET request.

    :current_user: The currently authenticated user for whom to fetch at-risk habits and advice
    :habit_manager: The habit manager dependency to interact with habit data
    :ollama_client: The Ollama client dependency to fetch AI-generated advice
    :redis_cache: The Redis manager dependency for caching results
    :return: A list of dictionaries containing at-risk habits and corresponding AI advice
    """
    at_risk_habits = await habit_manager.get_at_risk_habits(current_user.user_id)

    async def get_habit_data(habit: HabitResponse) -> dict[str, Any]:
        habit_analytics = await habit_manager.get_habit_analytics(habit.id)
        advice = await ollama_client.get_habit_advice(
            habit_name=str(habit.name), streak=habit_analytics["streak"], days_missed=habit_analytics["days_missed"]
        )
        return {"habit": habit.model_dump(), "ai_coach": advice}

    return await asyncio.gather(*[get_habit_data(h) for h in at_risk_habits])
