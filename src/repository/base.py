"""Base for repository design pattern"""

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID


class BaseRepository[T](ABC):
    """Base class for repository design pattern"""

    @abstractmethod
    async def add(self, entity: T) -> T:
        """Adds a new entity"""
        pass

    @abstractmethod
    async def get_all(self) -> list[T]:
        """Gets all entities"""
        pass

    @abstractmethod
    async def delete(self, entity_id: UUID) -> bool:
        """Deletes entity"""
        pass

    @abstractmethod
    async def update(self, entity_id: UUID, params: dict[str, Any]) -> bool:
        """Updates entity"""
