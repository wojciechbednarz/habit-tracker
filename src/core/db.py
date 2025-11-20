"""Database interaction module."""

import uuid
from datetime import datetime, timezone
import sqlite3
from sqlite3 import Connection, Cursor
from typing import AsyncGenerator, Generator, List, Optional, Tuple, Any
from sqlalchemy import Column, String, Text, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import create_engine, text, select
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker, Session
from src.utils.logger import setup_logger

DATABASE_ASYNC_URL = "sqlite+aiosqlite:///./habits.db"
DATABASE_SYNC_URL = "sqlite:///./habits.db"
logger = setup_logger(__name__)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models"""

    pass


class HabitBase(Base):
    """Declarative class model for POST request"""

    __tablename__ = "habits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    frequency = Column(Text, nullable=False)
    mark_done = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    def __repr__(self):
        return f"Habit(id={self.id}, name={self.name}, description={self.description}, \
        frequency={self.frequency}, mark_done={self.mark_done}, created_at={self.created_at})"

class AsyncDatabase:
    """Asynchronous database interaction class."""

    async_engine = create_async_engine(DATABASE_ASYNC_URL)
    async_session_maker = async_sessionmaker(async_engine, expire_on_commit=False)

    async def init_db_async(self):
        """Starts SQLAlchemy database engine and create table for Post class"""
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Gets a session which allows accessing the database and read/write asynchronously"""
        async with self.async_session_maker() as session:
            yield session


class SyncDatabase:
    """Synchronous database interaction class."""

    sync_engine = create_engine(DATABASE_SYNC_URL)
    sync_session_maker = sessionmaker(sync_engine, expire_on_commit=False)

    def init_db_sync(self):
        """Starts SQLAlchemy database engine and create table for Post class"""
        with self.sync_engine.begin() as conn:
            Base.metadata.create_all(bind=conn)

    def execute_query(self, query: str, params: Optional[Tuple[Any, ...]] = None):
        """Execute a SQL query with optional parameters."""
        with self.sync_engine.begin() as conn:
            return conn.execute(text(query), params)


class HabitDatabase(SyncDatabase):
    """Handle habit-related database operations."""

    def fetch_all_habit_results(self) -> List[HabitBase]:
        """Fetches all results from the database."""
        logger.info("Fetching all habits from the database...")
        try:
            with self.sync_session_maker() as session:
                stmt = select(HabitBase)
                result = session.execute(stmt)
                habits = result.scalars().all()
                logger.info(f"Fetched habits: {habits}")
                return habits
        except Exception as e:
            session.rollback()
            logger.error(f"Error while fetching habits: {e}")
            raise

    def check_if_habit_exists_in_db(self, habit_name):
        """Check if habit already exists in the database."""
        logger.info("Checking if habit exists in the database...")
        result = self.fetch_all_habit_results()
        for row in result:
            return True if row.name == habit_name else False

    def add_habit_to_db(
        self, name: str, description: str, frequency: str, mark_done: bool = False
    ) -> HabitBase:
        logger.info(f"Adding habit: {name} to database...")
        try:
            with self.sync_session_maker() as session:
                new_habit = HabitBase(
                    id=uuid.uuid4(),
                    name=name,
                    description=description,
                    frequency=frequency,
                    mark_done=mark_done,
                )
                session.add(new_habit)
                session.commit()
                session.refresh(new_habit)  # Get the saved object with all fields
                logger.info(f"Habit {name} added successfully with ID: {new_habit.id}")
                return new_habit
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding habit: {e}")
            raise
