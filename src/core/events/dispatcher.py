"""Dispatcher module for events look up"""

from src.core.events.events import BaseEvent
from src.core.events.handlers import Context, event_registry
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# event_registry = {
#     HabitCompletedEvent: [],
#     AchievementUnlockedEvent: []
# }


async def dispatch(event: BaseEvent, context: Context) -> None:
    """Performs look up for events"""

    # 1. Check if event_registry contains some data \n    # e.g. HabitCompletedEvent: [check_streaks]
    # 2. If there is handler in the list, call the handler with (event, context)
    logger.info("Event dispatcher start")
    event_type = type(event)
    handlers = event_registry.get(event_type, [])
    if not handlers:
        logger.debug(f"No handlers registered for {event_type.__name__}")
        return
    logger.info(f"Dispatching {event_type.__name__} to {len(handlers)} handlers")
    for handler in handlers:
        try:
            await handler(event, context)
        except Exception as e:
            logger.error(
                f"Handler {handler.__name__} failed for {event_type.__name__}. Error: {e}",
                exc_info=True,
            )
            continue
    logger.info(f"Finished dispatching {event_type.__name__}")
