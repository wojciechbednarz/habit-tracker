"""Habit Repository Module."""

from abc import abstractmethod
from typing import Any, TypeVar
from uuid import UUID

from sqlalchemy import delete, select, text, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from src.core.exceptions import (
    DatabaseException,
    HabitAlreadyExistsException,
    HabitNotFoundException,
)
from src.core.models import HabitBase
from src.repository.base import BaseRepository
from src.utils.logger import setup_logger

logger = setup_logger(__name__)
T = TypeVar("T")


class IHabitRepository(BaseRepository[HabitBase]):
    """Interface extension for habit related repository methods"""

    @abstractmethod
    async def delete_all(self, entity_id: UUID) -> int | None:
        """Deletes all habit entities for specific user"""
        pass

    @abstractmethod
    async def get_specific_habit_for_user(self, entity_id: UUID) -> HabitBase | None:
        """Gets habit entity based on its ID"""
        pass

    @abstractmethod
    async def get_all_habits_for_user(self, entity_id: UUID) -> list[HabitBase]:
        """Gets all habit entities for a specific user."""
        pass

    @abstractmethod
    async def exists_by_id(self, entity_id: UUID) -> bool:
        """Checks if habit entity exists using its ID"""
        pass

    @abstractmethod
    async def execute_query(
        self, query: str, params: tuple[Any, ...] | None
    ) -> T | None:
        """Executes SQL query"""
        pass


class HabitRepository(IHabitRepository):
    """Defines habit related repository methods"""

    def __init__(
        self,
        async_session_maker: async_sessionmaker[AsyncSession],
        async_engine: AsyncEngine,
    ) -> None:
        """Initializes the HabitRepository with an async session maker."""
        self.async_session_maker = async_session_maker
        self.async_engine = async_engine

    async def add(self, entity: HabitBase) -> HabitBase:
        """Persists a habit entity to the database."""
        try:
            async with self.async_session_maker() as session:
                session.add(entity)
                await session.commit()
                await session.refresh(entity)
                return entity
        except IntegrityError as e:
            logger.error(f"Habit '{entity.name}' already exists: {e}")
            raise HabitAlreadyExistsException(
                f"Habit with name '{entity.name}' already exists"
            ) from e
        except SQLAlchemyError as e:
            logger.error(f"Database error while adding habit '{entity.name}': {e}")
            raise DatabaseException(
                f"Failed to add habit '{entity.name}': {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error while adding habit '{entity.name}': {e}")
            raise DatabaseException(
                f"Unexpected error while adding habit: {str(e)}"
            ) from e

    async def delete(self, entity_id: UUID) -> bool:
        """Performs delete of the specific habit entity from the database."""
        async with self.async_session_maker() as session:
            try:
                query = delete(HabitBase).where(HabitBase.id == entity_id)
                result = await session.execute(query)
                await session.commit()
                deleted: bool = bool(result.rowcount) if result.rowcount else False  # type: ignore[attr-defined]
                return deleted
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(
                    f"Database error while deleting habit with ID '{entity_id}': {e}"
                )
                raise DatabaseException(
                    f"Failed to delete habit with ID '{entity_id}': {str(e)}"
                ) from e
            except HabitNotFoundException:
                raise
            except Exception as e:
                await session.rollback()
                logger.error(
                    f"Unexpected error while deleting habit with ID '{entity_id}': {e}"
                )
                raise DatabaseException(
                    f"Unexpected error while deleting habit: {str(e)}"
                ) from e

    async def delete_all(self, entity_id: UUID) -> int:
        """Deletes all habit entities for specific user."""
        async with self.async_session_maker() as session:
            try:
                query = delete(HabitBase).where(HabitBase.user_id == entity_id)
                result = await session.execute(query)
                await session.commit()
                deleted_count: int = result.rowcount or 0  # type: ignore[attr-defined]
                return deleted_count
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(
                    f"Database error while deleting habits for a user "
                    f"with ID '{entity_id}': {e}"
                )
                raise DatabaseException(
                    f"Failed to delete habits for a user with ID "
                    f"'{entity_id}': {str(e)}"
                ) from e
            except Exception as e:
                await session.rollback()
                logger.error(
                    f"Unexpected error while deleting habits for a user "
                    f"with ID '{entity_id}': {e}"
                )
                raise DatabaseException(
                    f"Unexpected error while deleting habits: {str(e)}"
                ) from e

    async def update(self, entity_id: UUID, params: dict[str, Any]) -> bool:
        """Updates habit entities in the database"""
        async with self.async_session_maker() as session:
            try:
                query = (
                    update(HabitBase).where(HabitBase.id == entity_id).values(**params)
                )
                result = await session.execute(query)
                await session.commit()
                updated: bool = bool(result.rowcount) if result.rowcount else False  # type: ignore[attr-defined]
                if not updated:
                    logger.warning(f"Habit with ID '{entity_id}' was not found.")
                    raise HabitNotFoundException(
                        f"Habit with ID '{entity_id}' not found"
                    )
                else:
                    logger.info(f"Habit with ID '{entity_id}' updated successfully.")
                return updated
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(
                    f"Database error while updating habit with ID '{entity_id}': {e}"
                )
                raise DatabaseException(f"Failed to update habit: {str(e)}") from e
            except HabitNotFoundException:
                raise
            except Exception as e:
                await session.rollback()
                logger.error(
                    f"Unexpected error while updating habit with ID '{entity_id}': {e}"
                )
                raise DatabaseException(
                    f"Unexpected error while updating habit "
                    f"with ID '{entity_id}': {str(e)}"
                ) from e

    async def get_specific_habit_for_user(self, entity_id: UUID) -> HabitBase | None:
        """Gets the habit entity from the database using habit ID."""
        try:
            async with self.async_session_maker() as session:
                query = select(HabitBase).where(HabitBase.id == entity_id)
                result = await session.execute(query)
                habit = result.scalar_one_or_none()
                if habit:
                    logger.info(f"Fetched habit: {habit}")
                else:
                    logger.warning(f"Habit with provided ID {entity_id} not found.")
                    raise HabitNotFoundException(f"Habit with ID {entity_id} not found")
                return habit
        except SQLAlchemyError as e:
            logger.error(
                f"Database error while fetching habit with ID {entity_id}: {e}"
            )
            raise DatabaseException(
                f"Failed to fetch habit by ID {entity_id}: {str(e)}"
            ) from e
        except HabitNotFoundException:
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error while fetching habit by ID {entity_id}: {e}"
            )
            raise DatabaseException(
                f"Unexpected error while fetching habit by ID {entity_id}: {str(e)}"
            ) from e

    async def get_all_habits_for_user(self, entity_id: UUID) -> list[HabitBase]:
        """Gets all habit entities for a specific user."""
        try:
            async with self.async_session_maker() as session:
                query = select(HabitBase).where(HabitBase.user_id == entity_id)
                result = await session.execute(query)
                habits = result.scalars().all()
                return list(habits)
        except SQLAlchemyError as e:
            logger.error(
                f"Database error while fetching habits for user {entity_id}: {e}"
            )
            raise DatabaseException(f"Failed to fetch habits: {str(e)}") from e

    async def get_all(self) -> list[HabitBase]:
        """Fetches all the habit entities from the database. Admin usage only."""
        logger.info("Fetching all habits from the database...")
        async with self.async_session_maker() as session:
            try:
                query = select(HabitBase)
                result = await session.execute(query)
                all_habits = result.scalars().all()
                logger.debug(f"Fetched habits: {all_habits}")
                return list(all_habits)
            except SQLAlchemyError as e:
                logger.error(f"Database error while fetching all habits: {e}")
                raise DatabaseException(f"Failed to fetch all habits: {str(e)}") from e
            except Exception as e:
                logger.error(f"Unexpected error while fetching all habits: {e}")
                raise DatabaseException(
                    f"Unexpected error while fetching all habits: {str(e)}"
                ) from e

    async def exists_by_id(self, entity_id: UUID) -> bool:
        """Check if habit entity exists by email."""
        habit = await self.get_specific_habit_for_user(entity_id)
        return habit is not None

    async def execute_query(
        self, query: str, params: tuple[Any, ...] | None = None
    ) -> Any:
        """Executes SQL query"""
        logger.warning("Deleting all habits")
        async with self.async_engine.begin() as conn:
            if isinstance(params, tuple):
                return await conn.exec_driver_sql(query, params)
            else:
                return await conn.execute(text(query), params)
        logger.info("All habits deleted")
