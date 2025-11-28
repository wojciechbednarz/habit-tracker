"""
This class handles all of the actions related to habits like: adding habit,
modifying it, displaying habits etc.
"""

from collections.abc import Sequence
from typing import Any, overload
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.core.db import HabitBase, HabitDatabase, UserBase
from src.utils.helpers import normalize_habit_name
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

DATABASE_NAME = "habit_tracker.db"


class HabitHistory(Sequence[HabitBase]):
    """To be used in future to store habit history e.g. how many completions
    it was for given habit and in which days.
    """

    def __init__(self, *habits: HabitBase) -> None:
        self._habits = list(habits)

    def __len__(self) -> int:
        return len(self._habits)

    @overload
    def __getitem__(self, item: int) -> HabitBase: ...
    @overload
    def __getitem__(self, item: slice) -> Sequence[HabitBase]: ...
    def __getitem__(self, item: int | slice) -> HabitBase | Sequence[HabitBase]:
        return self._habits[item]


class HabitCreate(BaseModel):
    """Schema for creating a new habit"""

    name: str = Field(..., min_length=1, max_length=30)
    description: str = Field(..., max_length=255)
    frequency: str = Field(
        ..., min_length=1, max_length=20, pattern="^(daily|weekly|monthly)$"
    )
    mark_done: bool = Field(default=False)
    user_id: UUID = Field(...)

    @field_validator("name", "description")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Remove leading/trailing whitespace."""
        return v.strip()


class HabitUpdate(BaseModel):
    """Pydantic class describing types of the habit data"""

    name: str | None = Field(None, min_length=1, max_length=30)
    description: str | None = Field(None, max_length=255)
    frequency: str | None = Field(
        None, min_length=1, max_length=20, pattern="^(daily|weekly|monthly)$"
    )
    mark_done: bool | None = None

    @field_validator("name", "description")
    @classmethod
    def strip_whitespace(cls, v: str) -> str | None:
        """Remove leading/trailing whitespace."""
        if v is not None:
            return v.strip()
        return v


class HabitResponse(BaseModel):
    """Schema for habit response."""

    id: str
    name: str
    description: str
    frequency: str
    mark_done: bool
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class HabitService:
    """Service layer for habit operations - handles business logic."""

    def __init__(self, db_path: str | None = None) -> None:
        """Initialize habit service with database connection."""
        self.db = HabitDatabase(db_url=db_path) if db_path else HabitDatabase()
        self.db.init_db_sync()

    def create_habit(self, habit_data: HabitCreate) -> HabitBase:
        """
        Create a new habit.
        Args:
            habit_data: Validated habit creation data
        Returns:
            Created habit object
        Raises:
            ValueError: If habit already exists
        """
        logger.info(f"Creating habit: {habit_data.name} to database.")
        if self.db.check_if_habit_exists_in_db(habit_data.name, habit_data.user_id):
            logger.warning(f"Habit: {habit_data.name} already exists.")
            raise ValueError(f"Habit: {habit_data.name} already exists.")
        habit = self.db.add_habit_to_db(
            name=habit_data.name,
            description=habit_data.description,
            frequency=habit_data.frequency,
            mark_done=habit_data.mark_done,
            user_id=habit_data.user_id,
        )
        logger.info(f"Habit: {habit_data.name} added successfully.")
        return habit

    def get_all_habits(self, user_id: UUID) -> list[HabitBase]:
        """
        Get all habits from database.
        Returns:
            List of habit objects
        """
        logger.info("Fetching all habits")
        habits = self.db.fetch_all_habit_results(user_id)
        logger.debug(f"Found {len(habits)} habits")
        return habits

    def update_habit(
        self, habit_name: str, updates: HabitUpdate, user_id: UUID
    ) -> None:
        """
        Update an existing habit.
        Args:
            habit_name: Name of habit to update
            updates: Fields to update
        Raises:
            ValueError: If habit not found
        """
        logger.info(f"Updating habit: {habit_name}")
        if not self.db.check_if_habit_exists_in_db(habit_name, user_id):
            raise ValueError(f"Habit with name: '{habit_name}' not found.")
        update_data = updates.model_dump(exclude_none=True)
        if not update_data:
            logger.warning("No fields to update.")
            return
        self.db.update_habit(habit_name, update_data, user_id)
        logger.info(f"Habit '{habit_name}' updated successfully")

    def mark_habit_done(self, habit_name: str, user_id: UUID) -> None:
        """
        Mark a habit as completed.
        Args:
            habit_name: Name of habit to mark as done
        Raises:
            ValueError: If habit not found
        """
        logger.info(f"Marking habit '{habit_name}' as done")
        if not self.db.check_if_habit_exists_in_db(habit_name, user_id):
            raise ValueError(f"Habit '{habit_name}' not found")
        self.db.mark_habit_as_done(habit_name, user_id)
        logger.info(f"Habit '{habit_name}' marked as done")

    def delete_all_habits(self) -> None:
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
            habit_info = (
                f"• {habit.name} ({habit.frequency}) - {status}\n  {habit.description}"
            )
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
                "created_at": habit.created_at.isoformat()
                if habit.created_at
                else None,
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
    """

    def __init__(self, db_path: str | None = None) -> None:
        """Initialize habit manager."""
        self.service = HabitService(db_path=db_path)
        self.formatter = HabitFormatter()
        self.running = True

    def add_habit(
        self,
        habit_name: str,
        description: str,
        frequency: str,
        user_id: UUID,
        mark_done: bool = False,
    ) -> HabitBase:
        """Add a new habit."""
        normalized_habit_name = normalize_habit_name(habit_name)
        habit_data = HabitCreate(
            name=normalized_habit_name,
            description=description,
            frequency=frequency,
            mark_done=mark_done,
            user_id=user_id,
        )
        return self.service.create_habit(habit_data)

    def update_habit(
        self, habit_name: str, updates: dict[str, Any], user_id: UUID
    ) -> None:
        """Updates specific value relate to the habit"""
        normalized_habit_name = normalize_habit_name(habit_name)
        update_model = HabitUpdate(**updates)
        self.service.update_habit(normalized_habit_name, update_model, user_id)

    def complete_habit(self, habit_name: str, user_id: UUID) -> None:
        """Mark a habit as completed."""
        normalized_habit_name = normalize_habit_name(habit_name)
        self.service.mark_habit_done(normalized_habit_name, user_id)

    def clear_all_habits(self) -> None:
        """Delete all habits."""
        self.service.delete_all_habits()

    def list_habits(self, user_id: UUID) -> str:
        """Get all habits for a specific user based on username"""
        habits = self.service.get_all_habits(user_id)
        return self.formatter.format_as_string(habits)


class UserService:
    """Service layer for user operations - handles business logic."""

    def __init__(self, db_path: str | None = None) -> None:
        """Initialize user service with database connection."""
        self.db = HabitDatabase(db_url=db_path) if db_path else HabitDatabase()
        self.formatter = HabitFormatter()
        self.db.init_db_sync()

    def add_user(self, user_name: str, email_address: str, nickname: str) -> UserBase:
        """Create a new user."""
        logger.info(f"Creating user: {user_name} to database.")
        user = self.db.create_new_user(user_name, email_address, nickname)
        logger.info(f"User: {user_name} added successfully.")
        return user


class UserManager:
    """High-level interface for user management."""

    def __init__(self, db_path: str | None = None) -> None:
        """Initialize user manager."""
        self.user_service = UserService(db_path=db_path)

    def create_user(
        self, user_name: str, email_address: str, nickname: str
    ) -> UserBase:
        """Creates a user"""
        return self.user_service.add_user(user_name, email_address, nickname)


if __name__ == "__main__":
    manager = HabitManager()
    user_manager = UserManager()

    user = user_manager.create_user(
        user_name="wojslaw", email_address="wojslaw@example.com", nickname="woj"
    )
    user_id = user.user_id

    try:
        manager.add_habit(
            habit_name="Exercise",
            description="Morning workout",
            frequency="daily",
            user_id=user_id,
        )
        manager.update_habit(
            habit_name="Exercise", updates={"frequency": "weekly"}, user_id=user_id
        )
    except ValueError as e:
        print(f"Error: {e}")

    manager.clear_all_habits()
    habits = manager.list_habits(user_id)

    print(f"List of habits: {habits}, type: {type(habits)}")
