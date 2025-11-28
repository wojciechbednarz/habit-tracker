"""API application for habit-tracker."""

from fastapi import FastAPI

app = FastAPI()


@app.get("/api/habits")
def get_all_habits(user: str = "default") -> dict[str, list[dict[str, str]]]:
    """Gets all habits list by sending a GET request"""
    pass


@app.post("/api/habits")
def create_habit(user: str = "default") -> dict[str, str]:
    """Creates a habit by sending a POST request"""
    pass
