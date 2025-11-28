"""Database interaction module."""

from collections.abc import AsyncGenerator
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    create_engine,
    text,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.core.models import Base, HabitBase, UserBase
from src.utils.logger import setup_logger

DATABASE_ASYNC_URL = "sqlite+aiosqlite:///./habits.db"
DATABASE_SYNC_URL = "sqlite:///./habits.db"
logger = setup_logger(__name__)

__all__ = ["AsyncDatabase", "SyncDatabase", "HabitDatabase", "HabitBase", "UserBase"]


class AsyncDatabase:
    """Asynchronous database interaction class."""

    def __init__(self, db_url: str = DATABASE_ASYNC_URL):
        self.async_engine = create_async_engine(db_url, echo=False)
        self.async_session_maker = async_sessionmaker(
            self.async_engine, expire_on_commit=False
        )

    async def init_db_async(self) -> None:
        """Starts SQLAlchemy database engine and create table for Post class"""
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def get_async_session(self) -> AsyncGenerator[AsyncSession]:
        """
        Gets a session which allows accessing the database and read/write asynchronously
        """
        async with self.async_session_maker() as session:
            yield session


class SyncDatabase:
    """Synchronous database interaction class."""

    def __init__(self, db_url: str = DATABASE_SYNC_URL):
        """Initialize synchronous database connection."""
        self.sync_engine = create_engine(db_url)
        self.sync_session_maker = sessionmaker(self.sync_engine, expire_on_commit=False)

    def init_db_sync(self) -> None:
        """Starts SQLAlchemy database engine and create table for Post class"""
        with self.sync_engine.begin() as conn:
            Base.metadata.create_all(bind=conn)

    def execute_query(self, query: str, params: tuple[Any, ...] | None = None) -> Any:
        """Execute a SQL query with optional parameters.
        Option for positional parameters (?) and for named parameters (:name)
        """
        with self.sync_engine.begin() as conn:
            if isinstance(params, tuple):
                return conn.exec_driver_sql(query, params)
            else:
                return conn.execute(text(query), params)


class AsyncHabitDatabase(AsyncDatabase):
    """Handle habit-related asynchronous database operations."""

    def __init__(self, db_url: str = DATABASE_ASYNC_URL):
        super().__init__(db_url=db_url)
        self.init_db_async()

    async def add_habit_to_db(
        self,
        name: str,
        description: str,
        frequency: str,
        user_id: UUID,
        mark_done: bool = False,
    ) -> HabitBase:
        """Adds habit to the database"""
        logger.debug(f"Adding habit: {name} to database...")
        try:
            async with self.async_session_maker() as session:
                new_habit = HabitBase(
                    id=uuid4(),
                    name=name,
                    description=description,
                    frequency=frequency,
                    mark_done=mark_done,
                    user_id=UUID(user_id) if isinstance(user_id, str) else user_id,
                )
                session.add(new_habit)
                await session.commit()
                await session.refresh(new_habit)
                logger.info(f"Habit {name} added successfully with ID: {new_habit.id}")
                return new_habit
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding habit: {e}")
            raise


class HabitDatabase(SyncDatabase):
    """Handle habit-related database operations."""

    def __init__(self, db_url: str = DATABASE_SYNC_URL):
        super().__init__(db_url=db_url)
        self.init_db_sync()

    def fetch_all_habit_results(self, user_id: UUID) -> list[HabitBase]:
        """Fetches all results from the database."""
        logger.info("Fetching all habits from the database...")
        try:
            with self.sync_session_maker() as session:
                habits = session.query(HabitBase).filter_by(user_id=user_id).all()
                logger.info(f"Fetched habits: {habits}")
                return habits
        except Exception as e:
            session.rollback()
            logger.error(f"Error while fetching habits: {e}")
            raise

    def check_if_habit_exists_in_db(self, habit_name: str, user_id: UUID) -> bool:
        """Check if habit already exists in the database."""
        logger.info("Checking if habit exists in the database...")
        result = self.fetch_all_habit_results(user_id)
        for row in result:
            if row.name == habit_name:
                return True
        return False

    def add_habit_to_db(
        self,
        name: str,
        description: str,
        frequency: str,
        user_id: UUID,
        mark_done: bool = False,
    ) -> HabitBase:
        """Adds habit to the database"""
        logger.debug(f"Adding habit: {name} to database...")
        try:
            with self.sync_session_maker() as session:
                new_habit = HabitBase(
                    id=uuid4(),
                    name=name,
                    description=description,
                    frequency=frequency,
                    mark_done=mark_done,
                    user_id=UUID(user_id) if isinstance(user_id, str) else user_id,
                )
                session.add(new_habit)
                session.commit()
                session.refresh(new_habit)
                logger.info(f"Habit {name} added successfully with ID: {new_habit.id}")
                return new_habit
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding habit: {e}")
            raise

    def update_habit(self, name: str, params: dict, user_id: UUID) -> bool:
        """Updates habit in the database using ORM"""
        logger.info(f"Updating habit: {name} with parameters: {params}")
        try:
            with self.sync_session_maker() as session:
                habit = (
                    session.query(HabitBase)
                    .filter(HabitBase.user_id == user_id, HabitBase.name == name)
                    .first()
                )
                if not habit:
                    logger.warning(
                        f"Provided habit name: {name} was not found in the database."
                    )
                    return False
                for key, value in params.items():
                    setattr(habit, key, value)
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Error during updating habit: {name}. Error: {e}")
            return False

    def mark_habit_as_done(self, name: str, user_id: UUID) -> bool:
        """Marks habit as done in the database"""
        logger.info(f"Marking habit: {name} as done in the database.")
        try:
            if isinstance(user_id, str):
                user_id = UUID(user_id)
            with self.sync_session_maker() as session:
                habit = (
                    session.query(HabitBase)
                    .filter_by(name=name, user_id=user_id)
                    .first()
                )
                if not habit:
                    logger.warning(
                        f"Provided habit name: {name} for user {user_id} \
                        was not found in the database."
                    )
                    return False
                habit.mark_done = True
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Marking habit {name} as done failed: {e}")
            return False

    def create_new_user(
        self, user_name: str, email_address: str, nickname: str
    ) -> UserBase:
        """Creates a new user in the database"""
        logger.info(f"Creating a new user with username: {user_name}.")
        try:
            with self.sync_session_maker() as session:
                user = (
                    session.query(UserBase)
                    .filter_by(email_address=email_address)
                    .first()
                )
                if user:
                    logger.warning(
                        f"User with provided e-mail address {email_address} \
                                   already exists in the database."
                    )
                    return user
                new_user = UserBase(
                    user_name=user_name, email_address=email_address, nickname=nickname
                )
                session.add(new_user)
                session.commit()
                session.refresh(new_user)
                logger.debug(
                    f"User with e-mail address {email_address} successfully \
                             added to the database."
                )
                return new_user
        except Exception as e:
            logger.error(f"Creating new user with username {user_name} failed: {e}")
            raise Exception("User creation failed") from e
