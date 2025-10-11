import json
import os
import sys

# Add the project root to Python path to allow imports from src
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.logger import setup_logger
from src.utils.helpers import (
    check_if_key_exists_in_json, 
    initialize_json_file, 
    read_json_file, 
    write_json_file,
    modify_json_file
)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HABIT_STORAGE_JSON_PATH = os.path.join(ROOT_DIR, "core", "habit_storage.json")

logger = setup_logger(__name__)



class HabitHandler:
    """Handle habit-related operations."""

    def __init__(self, temp_dict_storage):
        self.temp_dict_storage = temp_dict_storage

    def check_if_habit_exists_in_db(self) -> bool:
        """Check if habit already exists in the database."""
        habit_exists = check_if_key_exists_in_json(
            file_name=HABIT_STORAGE_JSON_PATH, value_related_to_habit=self.temp_dict_storage["name"])
        return habit_exists

    def modify_habit(self, updated_habit: dict, value_to_update: str) -> None:
        """Modify an existing habit in the database."""
        logger.info(f"Modifying habit: {value_to_update} in the database.")
        try:
            modify_json_file(HABIT_STORAGE_JSON_PATH, updated_habit, value_to_update)
        except Exception as e:
            logger.error(f"An error occurred while modifying habit: {value_to_update}, error: {e}")
    
    def clear_database(self) -> None:
        """Clear the habit database."""
        logger.info("Clearing the habit database.")
        write_json_file(HABIT_STORAGE_JSON_PATH, [])
        logger.info("Habit database cleared successfully.")


class HabitCore:
    """Core functionality for managing habits."""
    def __init__(self):
        self.name = ""
        self.description = ""
        self.frequency = ""
        self.done = False
        self.temp_dict_storage = {}
        self.habit_handler = HabitHandler(self.temp_dict_storage)
        initialize_json_file(HABIT_STORAGE_JSON_PATH)


    def create_temp_dict_storage(self) -> None:
        """Create a temporary dictionary to store habit details."""
        self.temp_dict_storage["name"] = self.name
        self.temp_dict_storage["description"] = self.description
        self.temp_dict_storage["frequency"] = self.frequency
        self.temp_dict_storage["done"] = self.done
        logger.debug(f"Temporary dictionary storage created: {self.temp_dict_storage}")

    def add_habit(
            self, name: str, description: str, frequency: str, done: bool = False) -> None:
        """Add a new habit to the database."""
        self.name = name
        self.description = description
        self.frequency = frequency
        self.done = done
        logger.info(f"Adding habit: {self.name} to database.")
        self.create_temp_dict_storage()
        if self.habit_handler.check_if_habit_exists_in_db():
            logger.warning(f"Habit: {self.name} already exists in the database.")
            return
        habits = read_json_file(HABIT_STORAGE_JSON_PATH)
        if habits is None:
            habits = []
        habits.append(self.temp_dict_storage)
        write_json_file(HABIT_STORAGE_JSON_PATH, habits)
        logger.info(f"Habit: {self.name} added successfully.")

    def list_habits(self):
        """List all habits in the database."""
        logger.info("Listing all habits in the database.")
        habits = read_json_file(HABIT_STORAGE_JSON_PATH)
        habits_list = []
        if habits:
            for habit in habits:
                logger.info(f"Habit: {habit['name']}, Description: {habit['description']}, Frequency: {habit['frequency']}")
                habits_list.append(habit)
        return habits_list

    def modify_habit(self, updated_habit: dict, value_to_update: str) -> None:
        """Modify an existing habit in the database."""
        self.habit_handler.modify_habit(updated_habit, value_to_update)

    def mark_done(self, habit_name: str) -> None:
        """Mark a habit as done."""
        logger.info(f"Marking habit: {habit_name} as done.")
        habits = read_json_file(HABIT_STORAGE_JSON_PATH)
        if habits:
            for habit in habits:
                if habit["name"] == habit_name:
                    habit["done"] = True
                    write_json_file(HABIT_STORAGE_JSON_PATH, habits)
                    logger.info(f"Habit: {habit_name} marked as done.")
                    return
            logger.warning(f"Habit: {habit_name} not found in the database.")
        else:
            logger.warning("No habits found in the database.")
    
    def clear_habits(self) -> None:
        """Clear all habits from the database."""
        self.habit_handler.clear_database()

if __name__ == "__main__":
    habit = HabitCore()
    habit.add_habit(name="Playing chess daily", description="I want to play chess daily to reach 1000 ELO", frequency="Daily")
    habit.add_habit(name="Reading books", description="Read at least one book per month", frequency="Monthly")
    habit.add_habit(name="Morning Exercise", description="Do a 30-minute workout every morning", frequency="Daily")
    habit.add_habit(name="Meditation", description="Meditate for 10 minutes every day", frequency="Daily")
    habit.modify_habit(
        updated_habit={
            "name": "Playing chess weekly",
            "description": "I want to play chess weekly to reach 1000 ELO",
            "frequency": "Weekly"
        },
        value_to_update="Playing chess daily"
    )
    habit.list_habits()
    # habit.mark_done("Morning Exercise")
