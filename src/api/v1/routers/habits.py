"""Habit-related API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.v1.routers.dependencies import (
    get_current_active_user,
    get_habit_manager,
)
from src.core.habit_async import AsyncHabitManager
from src.core.schemas import HabitCreate, HabitResponse, HabitUpdate, User

router = APIRouter(prefix="/api/habits", tags=["habits"])


@router.get("/")
async def get_all_habits(
    habit_manager: Annotated[AsyncHabitManager, Depends(get_habit_manager)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> list[HabitResponse]:
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


@router.delete("/{habit_id}", status_code=204)
async def delete_habit(
    habit_id: UUID,
    habit_manager: Annotated[AsyncHabitManager, Depends(get_habit_manager)],
    current_user: Annotated[User, Depends(get_current_active_user)],
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
async def delete_habits(
    habit_manager: Annotated[AsyncHabitManager, Depends(get_habit_manager)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> None:
    """Deletes all habits for a user by sending a DELETE request"""
    await habit_manager.delete_habits(current_user.user_id)


@router.put("/{habit_id}")
async def update_habit(
    habit_id: UUID,
    updates: HabitUpdate,
    habit_manager: Annotated[AsyncHabitManager, Depends(get_habit_manager)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict[str, str]:
    """Updates a habit by sending a PUT request"""
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
async def create_habit(
    habit: HabitCreate,
    habit_manager: Annotated[AsyncHabitManager, Depends(get_habit_manager)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict[str, str]:
    """Creates a habit by sending a POST request"""
    new_habit = await habit_manager.add_habit(
        user_id=current_user.user_id,
        habit_name=habit.name,
        description=habit.description,
        frequency=habit.frequency,
    )
    return {"message": "Habit created", "id": f"{new_habit.id}"}
