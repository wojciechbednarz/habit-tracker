"""Handler class for events"""

import functools
import typing
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import uuid4

from config import settings
from src.core.events.events import AchievementUnlockedEvent, HabitCompletedEvent, HabitUpdatedEvent
from src.core.streak_service import check_habit_consecutive_days, check_milestone
from src.infrastructure.aws.email_client import SESClient
from src.repository.habit_repository import HabitRepository
from src.repository.user_repository import UserRepository
from src.utils.decorators import timer
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

event_registry = defaultdict(list)


@dataclass
class Context:
    """Context dataclass for injecting the instances"""

    user_repo: UserRepository
    habit_repo: HabitRepository
    ses_client: SESClient


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
    milestone = check_milestone(streak)
    if milestone:
        achievement_event = AchievementUnlockedEvent(
            user_id=event.user_id,
            achievement_type=milestone,
            timestamp=datetime.now(),
            event_id=uuid4(),
        )
        await dispatch(achievement_event, context)


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


class AuditLogHandler:
    """Handler for logging events to an audit log"""

    def __init__(self) -> None:
        """Initializes the AuditLogHandler with the specified event type."""
        self.event_type = HabitUpdatedEvent

    def handle(self, event: HabitUpdatedEvent) -> None:
        """Handles the event by logging it to the audit log."""
        logger.info(f"Audit Log - Event: {event.event_id}, User: {event.user_id}, Habit: {event.habit_id}. Updates:")
        for habit_field, (old_value, new_value) in event.updates.items():
            logger.info(f"{habit_field}: {old_value} -> {new_value}")
