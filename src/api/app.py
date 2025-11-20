"""API application for habit-tracker."""

from fastapi import FastAPI
from src.core.habit import HabitCore, HabitData
from src.core.db import Post, create_db_and_tables, get_async_session

app = FastAPI()


@app.get("/api/habits")
def get_all_habits(user: str = "default"):
    """Gets all habits list by sending a GET request"""
    core = HabitCore()
    habits = core.list_habits()
    return {"user": user, "habits": habits}


@app.post("/api/habits")
def create_habit(habit: HabitData, user: str = "default"):
    """Creates a habit by sending a POST request"""
    core = HabitCore(user_data=user)
    core.add_habit(name="", description="", frequency="", done=False)
    return {"message: ": "Habit created", "habit": habit.name}
