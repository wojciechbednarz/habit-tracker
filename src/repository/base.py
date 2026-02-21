"""Base for repository design pattern"""

from typing import Any, Protocol
from uuid import UUID


class HasID(Protocol):
    id: UUID


class BaseRepository[T](Protocol):
    """Base class for repository design pattern"""

    async def add(self, entity: T) -> T:
        """Adds a new entity"""
        pass

    async def delete(self, entity_id: UUID) -> bool:
        """Deletes entity"""
        pass

    async def update(self, entity_id: UUID, params: dict[str, Any]) -> bool:
        """Updates entity"""
        pass


class FakeHabitRepository[T: HasID]:
    """Fake repository class for tests purposes"""

    def __init__(self) -> None:
        """Initialies FakeHabitRepository instance and in-memory 'database'"""
        self._items: dict[Any, T] = {}

    async def add(self, habit: T) -> T:
        """Adds a new entity"""
        habit = self._items[habit.id] = habit
        return habit

    async def get_all(self) -> list[T]:
        """Gets all habit entities"""
        return list(self._items.values())

    async def delete(self, habit_id: Any) -> bool:
        """Deletes habit from the dictionary"""
        self._items.pop(habit_id, None)
        return True

    async def update(self, habit_id: Any, params: dict[str, Any]) -> None:
        """Updates entity"""
        habit = self._items[habit_id]
        for key, value in params.items():
            setattr(habit, key, value)
