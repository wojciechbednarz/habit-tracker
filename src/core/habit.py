""" This class handles all of the actions related to habits like: adding habit, modifying it, displaying habits etc. """
from pydantic import BaseModel, Field
from sqlite3 import Error as SQLiteError
from typing import Optional, List
from src.core.db import HabitDatabase
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

DATABASE_NAME = "habit_tracker.db"


class HabitData(BaseModel):
    """Pydantic class describing types of the habit data"""

    habit_name: str = Field(min_length=1, max_length=30, default="Default Habit Name")
    habit_description: str = Field(max_length=255, default="Default Habit Description")
    habit_frequency: str = Field(min_length=1, max_length=20, default="daily")
    habit_done: bool = Field(default=False)


class HabitHandler:
    """Handle habit-related operations."""

    def __init__(self, habit_data: dict):
        self.habit_data = habit_data
        self.db = HabitDatabase()

    def check_if_habit_exists_in_db(self) -> bool:
        """Check if habit already exists in the database."""
        logger.info(
            f"Checking if habit: {self.habit_data['name']} exists in the database."
        )
        try:
            habit_check = self.db.check_if_habit_exists_in_db(self.habit_data["name"])
        except SQLiteError as e:
            logger.error(f"An error occurred while checking habit existence: {e}")
            habit_check = False
        return habit_check

    def modify_habit(self, updated_habit: dict, value_to_update: str) -> None:
        """Modify an existing habit in the database."""
        logger.info(f"Modifying habit: {value_to_update} in the database.")
        try:
            self.db.execute_query(
                "UPDATE habits SET name = ?, description = ?, frequency = ?, done = ? WHERE name = ?",
                (
                    updated_habit["name"],
                    updated_habit["description"],
                    updated_habit["frequency"],
                    int(updated_habit.get("done", False)),
                    value_to_update,
                ),
            )
        except SQLiteError as e:
            logger.error(
                f"An error occurred while modifying habit: {value_to_update}, error: {e}"
            )

    def clear_database(self) -> None:
        """Clear the habit database."""
        logger.info("Clearing the habit database.")
        self.db.execute_query("DELETE FROM habits")
        logger.info("Habit database cleared successfully.")

    def format_habits_to_str(self, habits) -> str:
        """
        Changes habits from SQL-like objects to human readable string format.
        """
        logger.debug("Formatting habits to human readable format.")
        try:
            habits_display = []
            for habit_row in habits:
                status = "✓ Done" if habit_row.mark_done else "○ Pending"
                habit_info = f"• {habit_row.name} ({habit_row.frequency}) - {status}\n  {habit_row.description}"
                habits_display.append(habit_info)
            return "\n".join(habits_display)
        except AttributeError as err:
            logger.error(
                f"Error accessing habit attributes. "
                f"Expected HabitBase object with attributes (name, mark_done, frequency, description). "
                f"Error: {err}",
                exc_info=True
            )
        except TypeError as err:
            logger.error(
                f"Error processing habit data. "
                f"Expected iterable of HabitBase objects. "
                f"Error: {err}",
                exc_info=True
            )

    def format_habits_to_dict(self, habits) -> List[dict]:
        """
        Changes habits from SQL-like objects to dictionary format.
        """
        logger.debug("Formatting habits to dictionary format.")
        list_with_habits = []
        for habit in habits:
            habit_formatted_to_dict = {
                "name": habit.name, "description": habit.description, "frequency": habit.frequency, "mark_done": habit.mark_done}
            list_with_habits.append(habit_formatted_to_dict)
        return list_with_habits


class HabitCore:
    """Core functionality for managing habits."""

    def __init__(self, user_data: Optional[str] = None):
        self.name = ""
        self.description = ""
        self.frequency = ""
        self.habit_done = False
        self.habit_data: HabitData = {}
        self.user_data = user_data
        self.habit_handler = HabitHandler(self.habit_data)
        self.db = HabitDatabase()
        self.db.init_db_sync()
        self.running = True

    def _prepare_habit_data(self) -> None:
        """Create a temporary dictionary to store habit details."""
        self.habit_data["name"] = self.name
        self.habit_data["description"] = self.description
        self.habit_data["frequency"] = self.frequency
        self.habit_data["done"] = self.mark_done
        logger.debug(f"Created habit data: {self.habit_data}")

    def add_habit(
        self, name: str, description: str, frequency: str, done: bool = False
    ) -> None:
        """Add a new habit to the database Example: add_habit("Exercise", "30 minutes of exercise", "daily").
        Args:
            name (str): Name of the habit.
            description (str): Description of the habit.
            frequency (str): Frequency of the habit.
            done (bool): Whether the habit is done or not. Defaults to False.
        Returns:
            None
        """
        self.name = name
        self.description = description
        self.frequency = frequency
        self.habit_done = done
        logger.debug(f"Adding habit: {self.name} to database.")
        self._prepare_habit_data()
        if self.habit_handler.check_if_habit_exists_in_db():
            logger.warning(f"Habit: {self.name} already exists in the database.")
            return
        self.db.add_habit_to_db(
            self.name, self.description, self.frequency, self.habit_done
        )
        logger.info(f"Habit: {self.name} added successfully.")

    def list_habits_as_string(self) -> str:
        """List all habits in the database. Example: list_habits_as_string().
        Returns:
            str: Formatted string of all habits.
        """
        logger.info("Listing all habits in the form of string from the database.")
        habits = self.db.fetch_all_habit_results()
        if habits:
            habits_formatted_to_string = self.habit_handler.format_habits_to_str(habits)
            return habits_formatted_to_string
        else:
            logger.debug("Habits list is empty, nothing to be displayed.")

    def list_habits_as_dict(self) -> dict:
        """List all habits in the database. Example: list_habits_as_dict().
        Returns:
            dict: Formatted string of all habits.
        """
        logger.info("Listing all habits in the form of dictionary from the database")
        habits = self.db.fetch_all_habit_results()
        logger.info(f"\nDEBUG\nAll habits: {habits}, \ntype: {type(habits)}")
        if habits:
            habit_list_with_habits_as_dicts = self.habit_handler.format_habits_to_dict(habits)
            return habit_list_with_habits_as_dicts
        else:
            logger.debug("Habits list is empty, nothing to be displayed.")

    def modify_habit(self, updated_habit: dict, value_to_update: str) -> None:
        """Modify an existing habit in the database.
        Example: modify_habit({"name": "Exercise", "description": "45 minutes of exercise", "frequency": "daily"},
        value_to_update="Exercise").
        Args:
            updated_habit (dict): Dictionary containing updated habit details.
            value_to_update (str): Name of the habit to be updated.
        Returns:
            None
        """
        logger.debug(
            f"Modifying habit: {value_to_update} with new data: {updated_habit}."
        )
        self.habit_handler.modify_habit(updated_habit, value_to_update)

    def mark_done(self, habit_name: str) -> None:
        """Mark a habit as done. Example: mark_done("Exercise").
        Args:
            habit_name (str): Name of the habit to be marked as done.
        Returns:
            None
        """
        logger.info(f"Marking habit: {habit_name} as done.")
        habits = self.db.fetch_all_habit_results()
        if habits:
            for habit in habits:
                if habit["name"] == habit_name:
                    self.db.execute_query(
                        "UPDATE habits SET done = ? WHERE name = ?", (1, habit_name)
                    )
                    logger.info(f"Habit: {habit_name} marked as done.")
                    return
            logger.warning(f"Habit: {habit_name} not found in the database.")
        else:
            logger.warning("No habits found in the database.")

    def clear_habits(self) -> None:
        """Clear all habits from the database."""
        self.habit_handler.clear_database()

    def display_data(self):
        """Displays user data from database.
        Returns:
            str: Formatted string of user data.
        """
        return f"User data: {self.user_data}"


if __name__ == "__main__":
    habit_core = HabitCore()
    habits_as_dict = habit_core.list_habits_as_dict()
    print(habits_as_dict)
    # habit_core.db.fetch_all_results()
