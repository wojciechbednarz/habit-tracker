"""Habit-related API endpoints."""

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from src.api.v1.routers.dependencies import (
    get_current_active_user,
    get_events_context,
    get_habit_manager,
    get_habit_repository,
    get_ollama_client,
    get_redis_manager,
)
from src.core.cache import RedisManager
from src.core.events.dispatcher import dispatch
from src.core.events.events import HabitCompletedEvent
from src.core.events.handlers import Context
from src.core.habit_async import AsyncHabitManager
from src.core.schemas import HabitCreate, HabitResponse, HabitUpdate, User
from src.infrastructure.ai.ollama_client import OllamaClient
from src.repository.habit_repository import HabitRepository
from src.utils.decorators import cache_habits_response, delete_habit_cache

router = APIRouter(prefix="/api/habits", tags=["habits"])


@router.get("/")
@cache_habits_response(ttl=3600)
async def get_all_habits(
    habit_manager: Annotated[AsyncHabitManager, Depends(get_habit_manager)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    redis_cache: Annotated[RedisManager, Depends(get_redis_manager)],
) -> list[HabitResponse] | Any:
    """Gets all habits list by sending a GET request"""
    habits = await habit_manager.get_all_habits_for_user(current_user.user_id)
    return habits


@router.get("/{habit_id}")
async def get_habit(
    habit_id: UUID,
    habit_manager: Annotated[AsyncHabitManager, Depends(get_habit_manager)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> HabitResponse:
    """Gets a specific habit by sending a GET request"""
    habit = await habit_manager.get_specific_habit(habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    if habit.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access habits for other users",
        )
    return habit


@router.get("/at-risk")
@cache_habits_response(ttl=3600)
async def get_at_risk_habits_with_advice(
    habit_manager: Annotated[AsyncHabitManager, Depends(get_habit_manager)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    redis_cache: Annotated[RedisManager, Depends(get_redis_manager)],
) -> list[HabitResponse] | Any:
    """
    Gets all 'at risk' habits list by sending a GET request.

    A habit is considered 'at risk' if there is a gap of 3 or more days without
    completion after the last completion.

    :habit_manager: AsyncHabitManager instance for accessing habit-related operations
    :current_user: User object representing the currently authenticated user
    :redis_cache: RedisManager instance for caching the response
    :return: List of at-risk habits as HabitResponse objects or cached response
    """
    habits = await habit_manager.get_at_risk_habits(current_user.user_id)
    return habits


@router.get("/at-risk/ai-coach")
async def get_at_risk_habits_ai_coach(
    user_id: UUID,
    repo: Annotated[HabitRepository, Depends(get_habit_repository)],
    ollama_client: Annotated[OllamaClient, Depends(get_ollama_client)],
) -> list[dict[str, Any]]:
    """
    Gets all 'at risk' habits list with AI-generated advice by sending a GET request.

    TODO: Implement getting of streak and days missed for each habit to pass
    to the AI model instead of hardcoded values.

    :user_id: The ID of the user for whom to retrieve at-risk habits
    :repo: HabitRepository instance for accessing habit-related database operations
    :ollama_client: OllamaClient instance for getting AI-generated advice
    :return: List of at-risk habits with AI advice as a list of dictionaries
    containing habit and advice information
    """
    at_risk_habits = await repo.get_at_risk_habits(user_id)
    results = []

    for habit in at_risk_habits:
        advice = await ollama_client.get_habit_advice(
            habit_name=str(habit.name),
            streak=5,  # Hardcoded placeholder
            days_missed=3,  # Hardcoded placeholder (since threshold is 3)
        )
        results.append({"habit": habit, "ai_coach": advice})
    return results


@router.delete("/{habit_id}", status_code=204)
@delete_habit_cache
async def delete_habit(
    habit_id: UUID,
    habit_manager: Annotated[AsyncHabitManager, Depends(get_habit_manager)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    redis_cache: Annotated[RedisManager, Depends(get_redis_manager)],
) -> None:
    """Delete a specific habit by ID"""
    habit = await habit_manager.get_specific_habit(habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    if habit.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete habits for other users",
        )
    success = await habit_manager.delete_habit(habit_id)
    if not success:
        raise HTTPException(status_code=404, detail="Habit not found")


@router.delete("/", status_code=204)
@delete_habit_cache
async def delete_habits(
    habit_manager: Annotated[AsyncHabitManager, Depends(get_habit_manager)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    redis_cache: Annotated[RedisManager, Depends(get_redis_manager)],
) -> None:
    """Deletes all habits for a user by sending a DELETE request"""
    await habit_manager.delete_habits(current_user.user_id)


@router.patch("/{habit_id}")
@delete_habit_cache
async def update_habit(
    habit_id: UUID,
    updates: HabitUpdate,
    habit_manager: Annotated[AsyncHabitManager, Depends(get_habit_manager)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    redis_cache: Annotated[RedisManager, Depends(get_redis_manager)],
) -> dict[str, str]:
    """Updates a habit by sending a PATCH request"""
    habit = await habit_manager.get_specific_habit(habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    if habit.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update habits for other users",
        )
    success = await habit_manager.update_habit(updates, habit_id)
    if not success:
        raise HTTPException(status_code=404, detail="Habit not found")
    return {"message": "Habit updated successfully"}


@router.post("/")
@delete_habit_cache
async def create_habit(
    habit: HabitCreate,
    habit_manager: Annotated[AsyncHabitManager, Depends(get_habit_manager)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    redis_cache: Annotated[RedisManager, Depends(get_redis_manager)],
) -> dict[str, str]:
    """Creates a habit by sending a POST request"""
    new_habit = await habit_manager.add_habit(
        user_id=current_user.user_id,
        habit_name=str(habit.name),
        description=habit.description,
        frequency=habit.frequency,
        tags=habit.tags,
    )
    return {"message": "Habit created", "id": f"{new_habit.id}"}


@router.post("/{habit_id}/complete", status_code=201)
@delete_habit_cache
async def complete_habit(
    habit_id: UUID,
    habit_manager: Annotated[AsyncHabitManager, Depends(get_habit_manager)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    redis_cache: Annotated[RedisManager, Depends(get_redis_manager)],
    event_context: Annotated[Context, Depends(get_events_context)],
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    """Completes a habit by sending POST request"""
    habit = await habit_manager.get_specific_habit(habit_id)
    if current_user.user_id != habit.user_id:
        raise HTTPException(status_code=403, detail="Not your habit")
    new_streak = await habit_manager.complete_habit(habit_id)
    event = HabitCompletedEvent(
        event_id=uuid4(),
        user_id=current_user.user_id,
        habit_id=habit.id,
        timestamp=datetime.now(),
        completed_date=datetime.now(),
        streak_count=new_streak,
    )
    background_tasks.add_task(dispatch, event, event_context)
    return {"message": "Habit completion logged"}
