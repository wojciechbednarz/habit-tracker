"""Habit Repository Module."""

from abc import abstractmethod
from datetime import datetime, timedelta
from typing import Any, TypeVar
from uuid import UUID

from sqlalchemy import delete, func, select, text, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from src.core.exceptions import (
    DatabaseException,
    HabitAlreadyExistsException,
    HabitNotFoundException,
)
from src.core.models import HabitBase, HabitCompletion
from src.repository.base import BaseRepository
from src.utils.logger import setup_logger

logger = setup_logger(__name__)
T = TypeVar("T")


class IHabitRepository(BaseRepository[HabitBase]):
    """Interface extension for habit related repository methods"""

    @abstractmethod
    async def add_completion(self, entity_id: UUID, completed_date: datetime | None = None) -> HabitCompletion:
        """Add habit completion for given habit entity"""
        pass

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
    async def get_completions_for_period(
        self, entity_id: UUID, *, start_date: datetime, end_date: datetime
    ) -> list[HabitBase]:
        """Gets all completed habit entities for a specific user with date range."""
        pass

    @abstractmethod
    async def get_completions_by_habit(self, entity_id: UUID) -> list[HabitCompletion]:
        """Gets the list of completed habits based on provided habit ID"""
        pass

    @abstractmethod
    async def get_at_risk_habits(self, entity_id: UUID, threshold_days: int = 3) -> list[HabitBase]:
        """Gets the habits which are 'at risk' - meaning the user has not completed the
        habit for at least 3 consecutive days. A habit is considered 'at risk' if
        there is a gap of 3 or more days without completion \n        after the last completion."""
        pass

    @abstractmethod
    async def exists_by_id(self, entity_id: UUID) -> bool:
        """Checks if habit entity exists using its ID"""
        pass

    @abstractmethod
    async def execute_query(self, query: str, params: tuple[Any, ...] | None) -> T | None:
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
        assert async_session_maker is not None, "async_session_maker must be provided"
        assert async_engine is not None, "async_engine must be provided"
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
            raise HabitAlreadyExistsException(f"Habit with name '{entity.name}' already exists") from e
        except SQLAlchemyError as e:
            logger.error(f"Database error while adding habit '{entity.name}': {e}")
            raise DatabaseException(f"Failed to add habit '{entity.name}': {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error while adding habit '{entity.name}': {e}")
            raise DatabaseException(f"Unexpected error while adding habit: {str(e)}") from e

    async def add_completion(self, entity_id: UUID, completed_date: datetime | None = None) -> HabitCompletion:
        """
        Adds habit completion for given habit id

        :entity_id: ID of the habit for which completion is being added
        :completed_date: Optional datetime for when the habit was completed.
        If not provided, current datetime will be used.
        :return: The created HabitCompletion object
        """
        async with self.async_session_maker() as session:
            try:
                if completed_date:
                    completion = HabitCompletion(habit_id=entity_id, completed_at=completed_date)
                else:
                    completion = HabitCompletion(habit_id=entity_id)
                session.add(completion)
                await session.commit()
                return completion
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Database error while completing habit with ID '{entity_id}': {e}")
                raise DatabaseException(f"Failed to complete habit with ID '{entity_id}': {str(e)}") from e
            except HabitNotFoundException:
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Unexpected error while completing habit with ID '{entity_id}': {e}")
                raise DatabaseException(f"Unexpected error while completing habit: {str(e)}") from e

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
                logger.error(f"Database error while deleting habit with ID '{entity_id}': {e}")
                raise DatabaseException(f"Failed to delete habit with ID '{entity_id}': {str(e)}") from e
            except HabitNotFoundException:
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Unexpected error while deleting habit with ID '{entity_id}': {e}")
                raise DatabaseException(f"Unexpected error while deleting habit: {str(e)}") from e

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
                logger.error(f"Database error while deleting habits for a user with ID '{entity_id}': {e}")
                raise DatabaseException(f"Failed to delete habits for a user with ID '{entity_id}': {str(e)}") from e
            except Exception as e:
                await session.rollback()
                logger.error(f"Unexpected error while deleting habits for a user with ID '{entity_id}': {e}")
                raise DatabaseException(f"Unexpected error while deleting habits: {str(e)}") from e

    async def update(self, entity_id: UUID, params: dict[str, Any]) -> bool:
        """Updates habit entities in the database"""
        async with self.async_session_maker() as session:
            try:
                query = update(HabitBase).where(HabitBase.id == entity_id).values(**params)
                result = await session.execute(query)
                await session.commit()
                updated: bool = bool(result.rowcount) if result.rowcount else False  # type: ignore[attr-defined]
                if not updated:
                    logger.warning(f"Habit with ID '{entity_id}' was not found.")
                    raise HabitNotFoundException(f"Habit with ID '{entity_id}' not found")
                else:
                    logger.info(f"Habit with ID '{entity_id}' updated successfully.")
                return updated
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Database error while updating habit with ID '{entity_id}': {e}")
                raise DatabaseException(f"Failed to update habit: {str(e)}") from e
            except HabitNotFoundException:
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Unexpected error while updating habit with ID '{entity_id}': {e}")
                raise DatabaseException(f"Unexpected error while updating habit with ID '{entity_id}': {str(e)}") from e

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
            logger.error(f"Database error while fetching habit with ID {entity_id}: {e}")
            raise DatabaseException(f"Failed to fetch habit by ID {entity_id}: {str(e)}") from e
        except HabitNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error while fetching habit by ID {entity_id}: {e}")
            raise DatabaseException(f"Unexpected error while fetching habit by ID {entity_id}: {str(e)}") from e

    async def get_completions_for_period(
        self, entity_id: UUID, *, start_date: datetime, end_date: datetime
    ) -> list[HabitBase]:
        """
        Gets all the completed habit entities from the database
        for a given date range using user ID.
        """
        try:
            async with self.async_session_maker() as session:
                query = (
                    select(
                        HabitCompletion.habit_id,
                        HabitBase.name,
                        HabitBase.description,
                        HabitBase.frequency,
                        HabitCompletion.completed_at,
                    )
                    .join(HabitCompletion, HabitBase.id == HabitCompletion.habit_id)
                    .where(
                        HabitBase.user_id == entity_id,
                        HabitCompletion.completed_at >= start_date,
                        HabitCompletion.completed_at <= end_date,
                    )
                    .order_by(HabitCompletion.completed_at)
                )
                result = await session.execute(query)
                habits = list(result.scalars().all())
                if habits:
                    logger.info(f"Fetched habits: {habits}")
                else:
                    logger.warning(f"Habits for a user with provided ID {entity_id} not found.")
                    raise HabitNotFoundException(f"Habits for a user with ID {entity_id} not found")
                return habits
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching habits for a user with ID {entity_id}: {e}")
            raise DatabaseException(f"Failed to fetch habits by user ID {entity_id}: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error while fetching habits by user ID {entity_id}: {e}")
            raise DatabaseException(f"Unexpected error while fetching habits by user ID {entity_id}: {str(e)}") from e

    async def get_completions_by_habit(self, entity_id: UUID) -> list[HabitCompletion]:
        """Gets the list of completed habits based on provided habit ID"""
        try:
            async with self.async_session_maker() as session:
                query = (
                    select(HabitCompletion)
                    .where(HabitCompletion.habit_id == entity_id)
                    .order_by(HabitCompletion.completed_at.desc())
                    .limit(90)
                )
                result = await session.execute(query)
                habits = list(result.scalars().all())
                if habits:
                    logger.info(f"Fetched habits: {habits}")
                else:
                    logger.warning(f"Habits for a user with provided ID {entity_id} not found.")
                    raise HabitNotFoundException(f"Habits for a habit with ID {entity_id} not found")
                return habits
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching habits for a habit with ID {entity_id}: {e}")
            raise DatabaseException(f"Failed to fetch habits by habit ID {entity_id}: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error while fetching habits by habit ID {entity_id}: {e}")
            raise DatabaseException(f"Unexpected error while fetching habits by habit ID {entity_id}: {str(e)}") from e

    async def get_all_habits_for_user(self, entity_id: UUID) -> list[HabitBase]:
        """Gets all habit entities for a specific user."""
        try:
            async with self.async_session_maker() as session:
                query = select(HabitBase).where(HabitBase.user_id == entity_id)
                result = await session.execute(query)
                habits = list(result.scalars().all())
                return list(habits)
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching habits for user {entity_id}: {e}")
            raise DatabaseException(f"Failed to fetch habits: {str(e)}") from e

    async def get_all(self) -> list[HabitBase]:
        """Fetches all the habit entities from the database. Admin usage only."""
        logger.info("Fetching all habits from the database...")
        async with self.async_session_maker() as session:
            try:
                query = select(HabitBase)
                result = await session.execute(query)
                all_habits = list(result.scalars().all())
                logger.debug(f"Fetched habits: {all_habits}")
                return list(all_habits)
            except SQLAlchemyError as e:
                logger.error(f"Database error while fetching all habits: {e}")
                raise DatabaseException(f"Failed to fetch all habits: {str(e)}") from e
            except Exception as e:
                logger.error(f"Unexpected error while fetching all habits: {e}")
                raise DatabaseException(f"Unexpected error while fetching all habits: {str(e)}") from e

    async def get_at_risk_habits(self, entity_id: UUID, threshold_days: int = 3) -> list[HabitBase]:
        """
        Gets the habits which are 'at risk' - meaning the user has not completed the
        habit for at least 3 consecutive days. A habit is considered 'at risk' if
        there is a gap of 3 or more days without completion after the last completion.

        :param entity_id: UUID of the user
        :param threshold_days: Number of days without completion to consider a habit
        'at risk' (default: 3)
        :return: List of HabitBase objects which are at risk
        """
        logger.info("Fetching all habits from the database...")
        async with self.async_session_maker() as session:
            try:
                latest_completions = (
                    select(
                        HabitCompletion.habit_id,
                        func.max(HabitCompletion.completed_at).label("last_completed"),
                    )
                    .group_by(HabitCompletion.habit_id)
                    .subquery()
                )
                threshold_date = datetime.now() - timedelta(days=threshold_days)
                query = (
                    select(HabitBase)
                    .outerjoin(
                        latest_completions,
                        HabitBase.id == latest_completions.c.habit_id,
                    )
                    .where(
                        HabitBase.user_id == entity_id,
                        func.coalesce(latest_completions.c.last_completed, HabitBase.created_at) <= threshold_date,
                    )
                )
                result = await session.execute(query)
                habits_at_risk = list(result.scalars().all())
                return habits_at_risk
            except SQLAlchemyError as e:
                logger.error(f"Error fetching at-risk habits: {e}")
                raise DatabaseException(str(e)) from e

    async def exists_by_id(self, entity_id: UUID) -> bool:
        """Check if habit entity exists by email."""
        habit = await self.get_specific_habit_for_user(entity_id)
        return habit is not None

    async def execute_query(self, query: str, params: tuple[Any, ...] | None = None) -> Any:
        """Executes SQL query"""
        logger.warning("Deleting all habits")
        async with self.async_engine.begin() as conn:
            if isinstance(params, tuple):
                return await conn.exec_driver_sql(query, params)
            else:
                return await conn.execute(text(query), params)
        logger.info("All habits deleted")
