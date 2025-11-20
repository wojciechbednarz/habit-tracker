"""Testing API endpoints related to habit-tracker app"""

from src.api.app import get_habits, send_habit


def test_getting_the_user_data():
    """Check the response from GET request"""
    expected_user = "default"
    expected_message = "Root habit-tracker endpoint"

    habits = get_habits()

    assert habits["user"] == expected_user


def test_sending_the_habit_data():
    """Checks the habit data being sent via POST request"""
    expected_message = "Success"

    habit = send_habit()

    assert expected_message in habit
