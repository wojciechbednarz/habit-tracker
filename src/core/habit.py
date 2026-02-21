"""
DEPRECATED: Synchronous habit management classes.

This module contains synchronous implementations kept for backward compatibility
with CLI commands. New code should use:
- AsyncHabitService from habit_async.py (with repository pattern)
- AsyncHabitManager from habit_async.py
- AsyncUserService from habit_async.py
- AsyncUserManager from habit_async.py

Main usage: Legacy CLI click commands only.
"""

from typing import Any, cast
from uuid import UUID
from warnings import warn

from src.core.db import HabitBase, HabitDatabase, UserBase
from src.core.schemas import HabitCreate, HabitUpdate
from src.utils.helpers import normalize_habit_name
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

DATABASE_NAME = "habit_tracker.db"


class HabitService:
    """Service layer for habit operations - handles business logic.
    DEPRECATED: Use AsyncHabitService from habit_async.py instead.
    """

    def __init__(self, db_path: str | None = None) -> None:
        """Initialize habit service with database connection."""
        warn(
            "HabitService is deprecated. Use AsyncHabitService from habit_async.py",
            DeprecationWarning,
            stacklevel=2,
        )
        self.db = HabitDatabase(db_url=db_path) if db_path else HabitDatabase()

    def create_habit(self, habit_data: HabitCreate, email: str) -> HabitBase:
        """
        Create a new habit.
        Args:
            habit_data: Validated habit creation data
            email: User's email address
        Returns:
            Created habit object
        Raises:
            ValueError: If habit already exists
        """
        logger.info(f"Creating habit: {habit_data.name} to database.")
        if self.db.check_if_habit_exists_in_db(habit_data.name, email):
            logger.warning(f"Habit: '{habit_data.name}' already exists.")
            raise ValueError(f"Habit: '{habit_data.name}' already exists.")
        habit = self.db.add_habit_to_db(
            name=habit_data.name,
            description=habit_data.description,
            frequency=habit_data.frequency,
            email=email,
            mark_done=habit_data.mark_done,
        )
        logger.info(f"Habit: {habit_data.name} added successfully.")
        return habit

    def get_all_habits(self, email: str) -> list[HabitBase]:
        """
        Get all habits from database.
        Returns:
            List of habit objects
        """
        logger.info("Fetching all habits")
        user = self.db.fetch_user_by_email(email)
        user_id = cast(UUID, user.user_id)
        habits = self.db.fetch_all_habit_results(user_id)
        logger.debug(f"Found {len(habits)} habits")
        return habits

    def update_habit(self, habit_name: str, updates: HabitUpdate, email: str) -> bool:
        """
        Update an existing habit.
        Args:
            habit_name: Name of habit to update
            updates: Fields to update
        Raises:
            ValueError: If habit not found
        """
        logger.info(f"Updating habit: {habit_name}")
        if not self.db.check_if_habit_exists_in_db(habit_name, email):
            raise ValueError(f"Habit with name: '{habit_name}' not found.")
        update_data = updates.model_dump(exclude_none=True)
        if not update_data:
            logger.warning("No fields to update.")
            return False
        update = self.db.update_habit(habit_name, update_data, email)
        logger.info(f"Habit '{habit_name}' updated successfully")
        return update

    def mark_habit_done(self, habit_name: str, email: str) -> None:
        """
        Mark a habit as completed.
        Args:
            habit_name: Name of habit to mark as done
            email: User's email address
        Raises:
            ValueError: If habit not found
        """
        logger.info(f"Marking habit '{habit_name}' as done")
        if not self.db.check_if_habit_exists_in_db(habit_name, email):
            raise ValueError(f"Habit '{habit_name}' not found")
        self.db.mark_habit_as_done(habit_name, email)
        logger.info(f"Habit '{habit_name}' marked as done")

    def delete_habits_for_all_users(self) -> None:
        """Delete all habits from the database."""
        logger.warning("Deleting all habits")
        self.db.execute_query("DELETE FROM habits")
        logger.info("All habits deleted")


class HabitFormatter:
    """Formatter for habit display - handles presentation logic."""

    @staticmethod
    def format_as_string(habits: list[HabitBase]) -> str:
        """
        Format habits as human-readable string.
        Args:
            habits: List of habit objects
        Returns:
            Formatted string representation
        """
        if not habits:
            return "No habits found."
        logger.debug(f"Formatting {len(habits)} habits as string")
        habits_display = []
        for habit in habits:
            status = "✓ Done" if habit.mark_done else "○ Pending"
            habit_info = f"• {habit.name} ({habit.frequency}) - {status}\n  {habit.description}"
            habits_display.append(habit_info)
        return "\n\n".join(habits_display)

    @staticmethod
    def format_as_dict_list(habits: list[HabitBase]) -> list[dict[str, Any]]:
        """
        Format habits as list of dictionaries.
        Args:
            habits: List of habit objects
        Returns:
            List of habit dictionaries
        """
        logger.debug(f"Formatting {len(habits)} habits as dict list")
        return [
            {
                "id": str(habit.id),
                "name": habit.name,
                "description": habit.description,
                "frequency": habit.frequency,
                "mark_done": habit.mark_done,
                "created_at": habit.created_at.isoformat() if habit.created_at else None,
            }
            for habit in habits
        ]

    @staticmethod
    def format_as_table(habits: list[HabitBase]) -> str:
        """
        Format habits as ASCII table.
        Args:
            habits: List of habit objects
        Returns:
            Table string representation
        """
        if not habits:
            return "No habits found."
        header = f"{'Name':<20} {'Frequency':<10} {'Status':<10}"
        separator = "-" * 40
        rows = [header, separator]
        for habit in habits:
            status = "Done" if habit.mark_done else "Pending"
            row = f"{habit.name:<20} {habit.frequency:<10} {status:<10}"
            rows.append(row)
        return "\n".join(rows)


class HabitManager:
    """
    High-level interface for habit management.
    Combines service and formatter for easy use.
    DEPRECATED: Use AsyncHabitManager from habit_async.py instead.
    """

    def __init__(self, db_path: str | None = None) -> None:
        """Initialize habit manager."""
        warn(
            "HabitManager is deprecated. Use AsyncHabitManager from habit_async.py",
            DeprecationWarning,
            stacklevel=2,
        )
        self.service = HabitService(db_path=db_path)
        self.formatter = HabitFormatter()
        self.running = True

    def add_habit(
        self,
        habit_name: str,
        description: str,
        frequency: str,
        email: str,
        mark_done: bool = False,
    ) -> HabitBase | str:
        """Add a new habit."""
        normalized_habit_name = normalize_habit_name(habit_name)
        habit_data = HabitCreate(
            name=normalized_habit_name,
            description=description,
            frequency=frequency,
            mark_done=mark_done,
        )
        try:
            habit = self.service.create_habit(habit_data, email)
            logger.info(f"Habit '{habit.name}' added successfully!")
            return habit
        except ValueError as e:
            return f"Error: {e}"
        except Exception as e:
            logger.error(f"Failed to add habit: {e}")
            return f"Failed to add habit: {e}"

    def update_habit(self, habit_name: str, updates: dict[str, Any], email: str) -> bool:
        """Updates specific value relate to the habit"""
        normalized_habit_name = normalize_habit_name(habit_name)
        update_model = HabitUpdate(**updates)
        return self.service.update_habit(normalized_habit_name, update_model, email)

    def complete_habit(self, habit_name: str, email: str) -> str:
        """Mark a habit as completed."""
        normalized_habit_name = normalize_habit_name(habit_name)
        try:
            self.service.mark_habit_done(normalized_habit_name, email)
            return f"Habit '{normalized_habit_name}' marked as complete!"
        except ValueError as e:
            return f"Error: {e}"
        except Exception as e:
            logger.error(f"Failed to complete habit: {e}")
            return f"Failed to complete habit: {e}"

    def clear_all_habits(self) -> None:
        """Delete all habits."""
        self.service.delete_habits_for_all_users()

    def get_habits_by_user_email(self, email: str) -> str:
        """Get all habits for a specific user based on email"""
        habits = self.service.get_all_habits(email)
        return self.formatter.format_as_string(habits)


class UserService:
    """Service layer for user operations - handles business logic.
    DEPRECATED: Use AsyncUserService from habit_async.py instead.
    """

    def __init__(self, db_path: str | None = None) -> None:
        """Initialize user service with database connection."""
        warn(
            "UserService is deprecated. Use AsyncUserService from habit_async.py",
            DeprecationWarning,
            stacklevel=2,
        )
        self.db = HabitDatabase(db_url=db_path) if db_path else HabitDatabase()
        self.formatter = HabitFormatter()

    def create_user(self, username: str, email: str, nickname: str, password: str) -> UserBase:
        """Create a new user."""
        logger.info(f"Creating user: {username} to database.")
        user = self.db.create_new_user(username, email, nickname, password)
        logger.info(f"User: {username} added successfully.")
        return user

    def get_user_by_email_address(self, email: str) -> UserBase:
        """Get user by email address."""
        logger.info(f"Fetching user by email address: {email}")
        user = self.db.fetch_user_by_email(email)
        logger.debug(f"Found user: {user}")
        return user


class UserManager:
    """High-level interface for user management.
    DEPRECATED: Use AsyncUserManager from habit_async.py instead.
    """

    def __init__(self, db_path: str | None = None) -> None:
        """Initialize user manager."""
        warn(
            "UserManager is deprecated. Use AsyncUserManager from habit_async.py",
            DeprecationWarning,
            stacklevel=2,
        )
        self.user_service = UserService(db_path=db_path)

    def create_user(self, username: str, email: str, nickname: str, password: str) -> UserBase:
        """Creates a user"""
        return self.user_service.create_user(username, email, nickname, password)

    def get_user_by_email_address(self, email: str) -> UserBase:
        """Get user by email address."""
        return self.user_service.get_user_by_email_address(email)


if __name__ == "__main__":
    manager = HabitManager()
    user_manager = UserManager()
    email = "j.kowalski@example.com"
    password = "password123"
    user = user_manager.create_user(username="jkowal", email=email, nickname="JohhnyKowalski", password=password)

    try:
        manager.add_habit(
            habit_name="Exercise",
            description="Morning workout",
            frequency="daily",
            email=email,
        )
        manager.update_habit(habit_name="Exercise", updates={"frequency": "weekly"}, email=email)
    except ValueError as e:
        print(f"Error: {e}")

    manager.clear_all_habits()
    habits = manager.get_habits_by_user_email(email)

    print(f"List of habits: {habits}, type: {type(habits)}")
