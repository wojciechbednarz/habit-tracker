from datetime import timedelta
from typing import Any

from src.core.models import HabitCompletion

BASE_POINTS_COMPLETION: dict[str, Any] = {
    "base_points": 10,
    "streak_multiplier": {
        7: 2.0,  # double points for 7-day streak
        30: 5.0,  # quintuple points for 30-day streak
        100: 10.0,  # tenfold points for 100-day streak
    },
}


def check_milestone(streak: int) -> str:
    """
    Helper function to check if the streak hits a milestone
    and return the milestone name.

    :streak: Current streak count
    :return: Milestone name if hit, else empty string
    """
    milestones = {
        1: "TEST STREAK",
        7: "1 Week Streak",
        30: "1 Month Streak",
        100: "100 Days Streak",
    }
    return milestones.get(streak, "")


def check_habit_consecutive_days(completions: list[HabitCompletion]) -> int:
    """
    Helper function to check how many consecutive days there are in the
    list of completions.
    The list is expected to be ordered by date descending (most recent first).

    :completions: List of completion dates for a habit, ordered by date descending
    :return: Number of consecutive days
    """
    streak = 1
    for i in range(len(completions) - 1):
        diff = completions[i].completed_at.date() - completions[i + 1].completed_at.date()
        if diff == timedelta(days=1):
            streak += 1
        elif diff == timedelta(days=0):
            continue
        else:
            break
    return streak


def compute_completion_points(streak_count: int) -> int:
    """Computes the points to award for a habit completion based on the current streak count.
    :streak_count: The current streak count for the habit completion
    :return: The number of points to award
    """
    count = 0
    if streak_count >= 100:
        count = BASE_POINTS_COMPLETION["base_points"] * BASE_POINTS_COMPLETION["streak_multiplier"][100]
    elif streak_count >= 30:
        count = BASE_POINTS_COMPLETION["base_points"] * BASE_POINTS_COMPLETION["streak_multiplier"][30]
    elif streak_count >= 7:
        count = BASE_POINTS_COMPLETION["base_points"] * BASE_POINTS_COMPLETION["streak_multiplier"][7]
    else:
        count = BASE_POINTS_COMPLETION["base_points"]
    return int(count)
