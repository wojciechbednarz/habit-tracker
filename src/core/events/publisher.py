from collections import defaultdict
from typing import Any

from src.core.events.events import BaseEvent


class HabitEventPublisher:
    """Publisher class for habit events"""

    def __init__(self) -> None:
        """Initializes the HabitEventPublisher with an empty registry."""
        self.registry: defaultdict[type[BaseEvent], list[Any]] = defaultdict(list)

    def register(self, handler: Any) -> None:
        """
        Registers a handler for a specific event type.

        :handler: An instance of a handler that has an event_type attribute
        :return: None
        """
        self.registry[handler.event_type].append(handler)

    def publish(self, event: BaseEvent) -> None:
        """
        Publishes an event to all registered handlers for the event's type.

        :event: An instance of an event to be published
        :return: None
        """
        for event_reg, handler in self.registry.items():
            if isinstance(event, event_reg):
                for h in handler:
                    h.handle(event)
