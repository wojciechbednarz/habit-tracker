"""Database interaction module."""

from typing import Any, cast
from uuid import UUID, uuid4

from sqlalchemy import create_engine, select, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

from config import settings
from src.core.models import Base, HabitBase, UserBase
from src.core.security import get_password_hash
from src.utils.logger import setup_logger

DATABASE_ASYNC_URL = str(settings.DATABASE_URL)
DATABASE_SYNC_URL = DATABASE_ASYNC_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://").replace(
    "sqlite+aiosqlite://", "sqlite://"
)
logger = setup_logger(__name__)

__all__ = ["AsyncDatabase", "SyncDatabase", "HabitDatabase", "HabitBase", "UserBase"]


def get_async_engine() -> AsyncEngine:
    """
    Creates and returns asynchronous database engine.

    :return: Asynchronous database engine
    """
    return create_async_engine(DATABASE_ASYNC_URL, echo=False)


def get_session_maker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """
    Creates and returns asynchronous session maker.

    :param engine: Asynchronous database engine
    :return: Asynchronous session maker
    """
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class AsyncDatabase:
    """Asynchronous database interaction class."""

    def __init__(self, db_url: str = DATABASE_ASYNC_URL):
        self.async_engine = create_async_engine(db_url, echo=False)
        self.async_session_maker = async_sessionmaker(self.async_engine, expire_on_commit=False)
        self.db_url = db_url

    async def init_db_async(self) -> None:
        """Starts SQLAlchemy database engine and create table for Post class.
        Creates tables directly without migrations.
        Testing purpose only.
        """
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)


class SyncDatabase:
    """Synchronous database interaction class."""

    def __init__(self, db_url: str = DATABASE_SYNC_URL):
        """Initialize synchronous database connection."""
        self.sync_engine = create_engine(db_url)
        self.sync_session_maker = sessionmaker(self.sync_engine, expire_on_commit=False)

    def init_db_sync(self) -> None:
        """FOR TESTING ONLY - Creates tables directly without migrations."""
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


class HabitDatabase(SyncDatabase):
    """Handle habit-related database operations.
    DEPRECATED: This synchronous database class is kept for backward compatibility.
    New code should use AsyncHabitService with repository pattern instead.
    """

    def __init__(self, db_url: str = DATABASE_SYNC_URL):
        super().__init__(db_url=db_url)

    def _get_user_id(self, email: str) -> UUID:
        user = self.fetch_user_by_email(email)
        user_id = cast(UUID, user.user_id)
        return user_id

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

    def check_if_habit_exists_in_db(self, habit_name: str, email: str) -> bool:
        """Check if habit already exists in the database."""
        logger.info("Checking if habit exists in the database...")
        user = self.fetch_user_by_email(email)
        user_id = cast(UUID, user.user_id)
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
        email: str,
        mark_done: bool = False,
    ) -> HabitBase:
        """Adds habit to the database"""
        logger.debug(f"Adding habit: {name} to database...")
        try:
            with self.sync_session_maker() as session:
                user = self.fetch_user_by_email(email)
                user_id = cast(UUID, user.user_id)
                new_habit = HabitBase(
                    id=uuid4(),
                    name=name,
                    description=description,
                    frequency=frequency,
                    mark_done=mark_done,
                    user_id=user_id,
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

    def update_habit(self, name: str, params: dict[str, Any], email: str) -> bool:
        """Updates habit in the database using ORM"""
        logger.info(f"Updating habit: {name} with parameters: {params}")
        try:
            with self.sync_session_maker() as session:
                user = self.fetch_user_by_email(email)
                user_id = cast(UUID, user.user_id)
                habit = session.query(HabitBase).filter(HabitBase.user_id == user_id, HabitBase.name == name).first()
                if not habit:
                    logger.warning(f"Provided habit name: {name} was not found in the database.")
                    return False
                for key, value in params.items():
                    setattr(habit, key, value)
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Error during updating habit: {name}. Error: {e}")
            return False

    def mark_habit_as_done(self, name: str, email: str) -> bool:
        """Marks habit as done in the database"""
        logger.info(f"Marking habit: {name} as done in the database.")
        try:
            user_id: UUID = self._get_user_id(email)
            with self.sync_session_maker() as session:
                habit = session.query(HabitBase).filter_by(name=name, user_id=user_id).first()
                if not habit:
                    logger.warning(
                        f"Provided habit name: {name} for user {user_id} \
                        was not found in the database."
                    )
                    return False
                habit.mark_done = True  # type: ignore[assignment]
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Marking habit {name} as done failed: {e}")
            return False

    def create_new_user(self, username: str, email: str, nickname: str, password: str) -> UserBase:
        """Creates a new user in the database"""
        logger.info(f"Creating a new user with username: {username}.")
        try:
            with self.sync_session_maker() as session:
                user = session.query(UserBase).filter_by(email=email).first()
                if user:
                    logger.warning(
                        f"User with provided e-mail address {email} \
                                   already exists in the database."
                    )
                    return user
                new_user = UserBase(
                    username=username,
                    email=email,
                    nickname=nickname,
                    hashed_password=get_password_hash(password),
                )
                session.add(new_user)
                session.commit()
                session.refresh(new_user)
                logger.debug(
                    f"User with e-mail address {email} successfully \
                      added to the database."
                )
                return new_user
        except Exception as e:
            logger.error(f"Creating new user with username {username} failed: {e}")
            raise Exception("User creation failed") from e

    def fetch_user_by_email(self, email: str) -> UserBase:
        """Fetch user by email address."""
        logger.info("Fetching user by email address from the database...")
        try:
            with self.sync_session_maker() as session:
                query = select(UserBase).where(UserBase.email == email)
                result = session.execute(query)
                user = result.scalar_one_or_none()
                if user:
                    logger.info(f"Fetched user: {user}")
                    return user
                else:
                    logger.warning(
                        f"User with provided e-mail address {email} \
                        was not found in the database."
                    )
                    raise Exception("User not found")
        except Exception as e:
            logger.error(f"Getting user by e-mail address {email} failed: {e}")
            raise Exception("Getting user failed") from e
