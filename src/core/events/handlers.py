"""Handler class for events"""

import functools
import typing
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from config import settings
from src.core.events.events import AchievementUnlockedEvent, HabitCompletedEvent
from src.core.models import HabitCompletion
from src.infrastructure.aws.dynamodb_client import DynamoDBClient
from src.infrastructure.aws.email_client import SESClient
from src.repository.habit_repository import HabitRepository
from src.repository.user_repository import UserRepository
from src.utils.decorators import timer
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

event_registry = defaultdict(list)


BASE_POINTS_COMPLETION: dict[str, Any] = {
    "base_points": 10,
    "streak_multiplier": {
        7: 2.0,  # double points for 7-day streak
        30: 5.0,  # quintuple points for 30-day streak
        100: 10.0,  # tenfold points for 100-day streak
    },
}


@dataclass
class Context:
    """Context dataclass for injecting the instances"""

    user_repo: UserRepository
    habit_repo: HabitRepository
    ses_client: SESClient
    dynamo_db: DynamoDBClient


def subscribe(event_type: type) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Subscribes to a given type of event.

    :func: Function to be added to the events registry
    :return: Wrapped function
    """

    def wrapper(func: Callable[..., Any]) -> Callable[..., Any]:
        event_registry[event_type].append(func)
        logger.debug(f"Registered handler {func.__name__} for {event_type.__name__}")

        @functools.wraps(func)
        async def inner_wrapper(*args: Any, **kwargs: Any) -> Any:
            return await func(*args, **kwargs)

        return inner_wrapper

    return wrapper


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


def _check_milestone(streak: int) -> str:
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


@subscribe(HabitCompletedEvent)
async def check_streaks(event: HabitCompletedEvent, context: Context) -> None:
    """
    Checks the habit streaks and dispatches an achievement event if a milestone
    is reached.

    :event: The HabitCompletedEvent containing details about the completed habit
    :context: The Context object containing repositories and clients for handling
    the event
    :return: None
    """
    # Local import to avoid circular import
    from src.core.events.dispatcher import dispatch

    completed_descending_habits = await context.habit_repo.get_completions_by_habit(event.habit_id)
    streak = check_habit_consecutive_days(completed_descending_habits)
    if streak > event.streak_count:
        await context.dynamo_db.put_streak(event.user_id, event.habit_id, streak)
    milestone = _check_milestone(streak)
    if milestone:
        achievement_event = AchievementUnlockedEvent(
            user_id=event.user_id,
            achievement_type=milestone,
            timestamp=datetime.now(),
            event_id=uuid4(),
        )
        await dispatch(achievement_event, context)


@subscribe(HabitCompletedEvent)
async def award_points(event: HabitCompletedEvent, context: Context) -> None:
    """
    Awards points to the user based on the habit completion and current streak.

    :event: The HabitCompletedEvent containing details about the completed habit
    :context: The Context object containing repositories and clients for handling
    the event
    :return: None
    """

    streaks = event.streak_count
    count = 0
    if streaks >= 100:
        count = BASE_POINTS_COMPLETION["base_points"] * BASE_POINTS_COMPLETION["streak_multiplier"][100]
    elif streaks >= 30:
        count = BASE_POINTS_COMPLETION["base_points"] * BASE_POINTS_COMPLETION["streak_multiplier"][30]
    elif streaks >= 7:
        count = BASE_POINTS_COMPLETION["base_points"] * BASE_POINTS_COMPLETION["streak_multiplier"][7]
    else:
        count = BASE_POINTS_COMPLETION["base_points"]
    await context.dynamo_db.update_points(event.user_id, count)


@timer
@subscribe(AchievementUnlockedEvent)
async def send_notification(event: AchievementUnlockedEvent, context: Context) -> None:
    """
    Sends a congratulation email to the user when they unlock an achievement.

    :event: The AchievementUnlockedEvent containing details about the unlocked achievement
    :context: The Context object containing repositories and clients for handling
    the event
    :return: None
    """
    user_data = await context.user_repo.get_by_id(event.user_id)
    if not user_data:
        logger.error(f"User {event.user_id} not found for notification")
        return
    await context.ses_client.send_congratulation_email(
        achievement_type=event.achievement_type,
        recipient=typing.cast(str, user_data.email),
        sender=settings.AWS_SES_SENDER_EMAIL,
    )
