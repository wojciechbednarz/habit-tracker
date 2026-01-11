"""Asynchronous service and manager for user operations related to manipulation
with API endpoints.
"""

import asyncio
from uuid import UUID

from src.core.db import AsyncDatabase
from src.core.exceptions import HabitNotFoundException, UserNotFoundException
from src.core.habit import HabitFormatter
from src.core.models import HabitBase, UserBase
from src.core.schemas import HabitCreate, HabitResponse, HabitUpdate, UserUpdate
from src.core.security import get_password_hash
from src.repository.habit_repository import HabitRepository
from src.repository.user_repository import UserRepository
from src.utils.helpers import normalize_habit_name
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class AsyncUserService:
    """Service layer for user operations - handles business logic."""

    def __init__(self, db_path: str | None = None) -> None:
        """Initialize user service with database connection."""
        self.async_database = AsyncDatabase(db_path) if db_path else AsyncDatabase()
        async_session_maker = self.async_database.async_session_maker
        self.user_repo = UserRepository(async_session_maker)
        self.formatter = HabitFormatter()

    async def create_user(
        self, username: str, email: str, nickname: str, password: str
    ) -> UserBase:
        """Create a new user."""
        logger.info(f"Creating user: {username} to database.")
        user_base = UserBase(
            username=username,
            email=email,
            nickname=nickname,
            hashed_password=get_password_hash(password),
        )
        user = await self.user_repo.add(user_base)
        logger.info(f"User: {username} added successfully.")
        return user

    async def get_user_by_email_address(self, email: str) -> UserBase:
        """Get user by email address."""
        logger.info(f"Fetching user by email address: {email}")
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise UserNotFoundException(f"User with email '{email}' not found.")
        logger.info(f"Found user: {user}")
        return user

    async def get_user_by_username(self, username: str) -> UserBase:
        """Get user by username."""
        logger.info(f"Fetching user by username: {username}")
        user = await self.user_repo.get_by_username(username)
        if not user:
            raise UserNotFoundException(f"User with username '{username}' not found.")
        logger.info(f"Found user: {user}")
        return user

    async def delete_user(self, user_id: UUID) -> bool:
        """Delete user by user ID."""
        logger.info(f"Deleting user using user ID: {user_id}")
        deleted = await self.user_repo.delete(user_id)
        if not deleted:
            raise UserNotFoundException(f"User with user ID: '{user_id}' not found.")
        logger.info(f"User with user ID: {user_id} successfully deleted.")
        return deleted

    async def update_user(self, user_id: UUID, updates: UserUpdate) -> bool:
        """Update an existing user."""
        logger.info(f"Updating user with user ID: {user_id}")
        if not await self.user_repo.get_by_id(user_id):
            raise UserNotFoundException(f"User with user ID: '{user_id}' not found.")
        update_data = updates.model_dump(exclude_none=True)
        if not update_data:
            logger.warning("No fields to update.")
            return False
        update = await self.user_repo.update(user_id, update_data)
        logger.info(f"User with user ID '{user_id}' updated successfully")
        return update

    async def get_all_users(self) -> list[UserBase]:
        """Returns a list"""
        logger.info("Fetching all users from the database...")
        users = await self.user_repo.get_all()
        logger.info(f"Fetched users: {users}")
        return users


class AsyncUserManager:
    """High-level interface for user management."""

    def __init__(self, db_path: str | None = None) -> None:
        """Initialize user manager."""
        self.user_service = AsyncUserService(db_path=db_path)

    async def create_user(
        self, username: str, email: str, nickname: str, password: str
    ) -> UserBase:
        """Creates a user"""
        return await self.user_service.create_user(username, email, nickname, password)

    async def update_user(self, user_id: UUID, updates: UserUpdate) -> bool:
        """Updates specific value relate to the user"""
        logger.info(f"Updating user with ID: {user_id}")
        update = await self.user_service.update_user(user_id, updates)
        logger.info(f"User with ID: {user_id} updated successfully")
        return update

    async def delete_user(self, user_id: UUID) -> bool:
        """Creates a user"""
        logger.info(f"Deleting user with ID: {user_id}")
        deleted = await self.user_service.delete_user(user_id)
        logger.info(f"User with ID: {user_id} deleted successfully")
        return deleted

    async def get_user_by_email_address(self, email: str) -> UserBase:
        """Get user by email address."""
        return await self.user_service.get_user_by_email_address(email)

    async def get_user_by_username(self, username: str) -> UserBase:
        """Get user by username"""
        return await self.user_service.get_user_by_username(username)

    async def read_all_users(self) -> list[UserBase]:
        """Returns a list"""
        users = await self.user_service.get_all_users()
        return users


class AsyncHabitService:
    """Service layer for habit operations - handles business logic."""

    def __init__(
        self,
        user_repo: UserRepository,
        habit_repo: HabitRepository,
        async_db: AsyncDatabase,
    ) -> None:
        self.user_repo = user_repo
        self.habit_repo = habit_repo
        self.async_db = async_db
        self.async_session_maker = async_db.async_session_maker
        self.async_engine = async_db.async_engine

    async def create_habit(self, habit_data: HabitCreate, user_id: UUID) -> HabitBase:
        """
        Create a new habit.
        Args:
            habit_data: Validated habit creation data
        Returns:
            Created habit object
        Raises:
            HabitNotFoundException: If habit already exists
        """
        logger.info(f"Creating habit: {habit_data.name}.")
        habit_base = HabitBase(
            user_id=user_id,
            name=habit_data.name,
            description=habit_data.description,
            frequency=habit_data.frequency,
            mark_done=habit_data.mark_done,
        )
        habit = await self.habit_repo.add(habit_base)
        logger.info(f"Habit: {habit_data.name} added successfully.")
        return habit

    async def get_all_habits_for_all_users(self) -> list[HabitResponse]:
        """
        Get all habits from database.
        Returns:
            List of habit objects
        """
        logger.info("Fetching all habits from database.")
        habits = await self.habit_repo.get_all()
        logger.info(f"Retrieved {len(habits)} habits from database.")
        return [HabitResponse.model_validate(habit) for habit in habits]

    async def get_all_habits_for_user(self, user_id: UUID) -> list[HabitResponse]:
        """Get all habits for a specific user based on user ID"""
        logger.info(f"Fetching habits for user with ID: {user_id}")
        habits = await self.habit_repo.get_all_habits_for_user(user_id)
        logger.info(f"Retrieved {len(habits)} habits for user ID: {user_id}")
        return [HabitResponse.model_validate(habit) for habit in habits]

    async def get_specific_habit(self, habit_id: UUID) -> HabitResponse:
        """Get a specific habit for a user based on habit id."""
        logger.info(f"Fetching habit with ID: {habit_id}")
        habit = await self.habit_repo.get_specific_habit_for_user(habit_id)
        logger.info(f"Retrieved habit: {habit}")
        return HabitResponse.model_validate(habit)

    async def update_habit(self, updates: HabitUpdate, habit_id: UUID) -> bool:
        """
        Update an existing habit.
        Args:
            habit_id: Unique ID of specific habit
            updates: Fields to update
        Raises:
            ValueError: If habit not found
        """
        habit = await self.habit_repo.get_specific_habit_for_user(habit_id)
        if not habit:
            raise HabitNotFoundException(f"Habit with ID '{habit_id}' not found")
        normalized_habit_name = normalize_habit_name(str(habit.name))
        logger.info(f"Updating habit: {normalized_habit_name}")
        update_data = updates.model_dump(exclude_none=True)
        if not update_data:
            logger.warning("No fields to update.")
            return False
        update = await self.habit_repo.update(habit_id, update_data)
        logger.info(f"Habit '{normalized_habit_name}' updated successfully")
        return update

    async def mark_habit_done(self, habit_id: UUID, mark_done: bool = True) -> None:
        """
        Mark a habit as completed.
        Args:
            habit_name: Name of habit to mark as done
            habit_id: Unique ID of specific habit
        Raises:
            HabitNotFoundException: If habit not found
        """
        logger.info(f"Marking habit with ID '{habit_id}' as done")
        habit = await self.habit_repo.get_specific_habit_for_user(habit_id)
        if not habit:
            raise HabitNotFoundException(f"Habit with ID '{habit_id}' not found")
        params = {"mark_done": mark_done}
        await self.habit_repo.update(habit_id, params)
        logger.info(f"Habit '{habit.name}' marked as done")

    async def delete_habits_for_all_users(self) -> None:
        """Delete all habits from the database."""
        await self.habit_repo.execute_query("DELETE FROM habits")

    async def delete_habits_for_specific_user(self, user_id: UUID) -> int:
        """Delete all habits for a specific user."""
        logger.info(f"Deleting habits for user with ID: {user_id}")
        deleted_count = await self.habit_repo.delete_all(user_id)
        logger.info(f"Deleted {deleted_count} habits for user '{user_id}'.")
        return deleted_count

    async def delete_habit_for_specific_user(self, habit_id: UUID) -> bool:
        """Delete habit for a specific user."""
        logger.info(f"Deleting habit with ID {habit_id}.")
        deleted = await self.habit_repo.delete(habit_id)
        if deleted:
            logger.info(f"Habit {habit_id} deleted successfully.")
        else:
            logger.warning(f"Habit with ID {habit_id} was not found.")
            raise HabitNotFoundException(f"Habit with ID {habit_id} not found")
        return deleted


class AsyncHabitManager:
    """High-level interface for habit management."""

    def __init__(
        self, db_path: str | None = None, service: AsyncHabitService | None = None
    ) -> None:
        """Initialize habit manager."""
        self.async_db = AsyncDatabase(db_path) if db_path else AsyncDatabase()
        self.formatter = HabitFormatter()
        self.running = True
        if service:
            self.service = service
        else:
            user_repo = UserRepository(self.async_db.async_session_maker)
            habit_repo = HabitRepository(
                self.async_db.async_session_maker, self.async_db.async_engine
            )
            self.service = AsyncHabitService(
                user_repo=user_repo, habit_repo=habit_repo, async_db=self.async_db
            )

    async def add_habit(
        self,
        user_id: UUID,
        habit_name: str,
        description: str,
        frequency: str,
        mark_done: bool = False,
    ) -> HabitBase:
        """Add a new habit."""
        normalized_habit_name = normalize_habit_name(habit_name)
        habit_data = HabitCreate(
            name=normalized_habit_name,
            description=description,
            frequency=frequency,
            mark_done=mark_done,
        )
        return await self.service.create_habit(habit_data, user_id)

    async def update_habit(self, updates: HabitUpdate, habit_id: UUID) -> bool:
        """Updates specific value relate to the habit"""
        return await self.service.update_habit(updates, habit_id)

    async def complete_habit(self, habit_id: UUID, mark_done: bool = True) -> None:
        """Mark a habit as completed."""
        await self.service.mark_habit_done(habit_id, mark_done)

    async def clear_all_habits(self) -> None:
        """Delete all habits for all users."""
        await self.service.delete_habits_for_all_users()

    async def delete_habits(self, user_id: UUID) -> int:
        """Delete all habits for specific user and gets the number of deleted habits."""
        return await self.service.delete_habits_for_specific_user(user_id)

    async def delete_habit(self, habit_id: UUID) -> bool:
        """Delete habit for specific user."""
        return await self.service.delete_habit_for_specific_user(habit_id)

    async def get_all_habits_for_user(self, user_id: UUID) -> list[HabitResponse]:
        """Get all habits for a specific user based on user ID"""
        return await self.service.get_all_habits_for_user(user_id)

    async def get_specific_habit(self, habit_id: UUID) -> HabitResponse:
        """Get a specific habit for a user based on habit id."""
        habit = await self.service.get_specific_habit(habit_id)
        return habit


if __name__ == "__main__":

    async def main() -> None:
        """Main function to test AsyncHabitManager functionality."""
        manager = AsyncHabitManager()
        user_id = UUID("12345678-1234-1234-1234-123456789012")
        try:
            await manager.add_habit(
                user_id=user_id,
                habit_name="Read a book",
                description="Read 20 pages of a book",
                frequency="daily",
                mark_done=False,
            )
            await manager.update_habit(
                updates=HabitUpdate(
                    name="Read a book", description="Read a book", frequency="daily"
                ),
                habit_id=UUID("put-a-valid-uuid-here"),
            )
        except ValueError as e:
            print(f"Error: {e}")

        await manager.clear_all_habits()
        habits = await manager.get_all_habits_for_user(UUID("put-a-valid-uuid-here"))

        print(f"List of habits: {habits}, type: {type(habits)}")

    asyncio.run(main())
