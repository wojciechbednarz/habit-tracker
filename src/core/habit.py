# core/habit.py
import os
import sys
from sqlite3 import Error as SQLiteError
from core.db.crud import get_db_connection, execute_query, create_table, fetch_all_results

# Add the project root to Python path to allow imports from src
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.logger import setup_logger


logger = setup_logger(__name__)

DATABASE_NAME = "habit_tracker.db"

class HabitHandler:
    """Handle habit-related operations."""

    def __init__(self, temp_dict_storage: dict):
        self.temp_dict_storage = temp_dict_storage
        self.db_con = get_db_connection(DATABASE_NAME)

    def check_if_habit_exists_in_db(self) -> bool:
        """Check if habit already exists in the database."""
        logger.info(f"Checking if habit: {self.temp_dict_storage['name']} exists in the database.")
        try:
            # select_habit_count = execute_query(self.db_con, "SELECT COUNT(*) FROM habits WHERE name = ?",
            #               (self.temp_dict_storage["name"],))
            fetched_results = fetch_all_results(self.db_con, "SELECT COUNT(*) FROM habits WHERE name = ?", (self.temp_dict_storage["name"],))
            habit_exists = fetched_results[0][0] > 0
        except SQLiteError as e:
            logger.error(f"An error occurred while checking habit existence: {e}")
            habit_exists = False
        return habit_exists

    def modify_habit(self, updated_habit: dict, value_to_update: str) -> None:
        """Modify an existing habit in the database."""
        logger.info(f"Modifying habit: {value_to_update} in the database.")
        try:
            execute_query(self.db_con, "UPDATE habits SET name = ?, description = ?, frequency = ?, done = ? WHERE name = ?",
                          (updated_habit["name"], updated_habit["description"], updated_habit["frequency"], int(updated_habit.get("done", False)), value_to_update))
        except SQLiteError as e:
            logger.error(f"An error occurred while modifying habit: {value_to_update}, error: {e}")
    
    def clear_database(self) -> None:
        """Clear the habit database."""
        logger.info("Clearing the habit database.")
        execute_query(self.db_con, "DELETE FROM habits")
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
        self.db_con = get_db_connection(DATABASE_NAME)


    def initialize_database(self) -> None:
        """Initialize the habit database if it does not exist."""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            frequency TEXT NOT NULL,
            done INTEGER NOT NULL
        );
        """
        create_table(self.db_con, create_table_query)

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
        execute_query(self.db_con, "INSERT INTO habits (name, description, frequency, done) VALUES (?, ?, ?, ?)",
                      (self.name, self.description, self.frequency, int(self.done)))
        logger.info(f"Habit: {self.name} added successfully.")

    def list_habits(self):
        """List all habits in the database."""
        logger.info("Listing all habits in the database.")
        # habits = execute_query(self.db_con, "SELECT name, description, frequency, done FROM habits")
        habits = fetch_all_results(self.db_con, "SELECT name, description, frequency, done FROM habits")
        habits_list = []
        if habits:
            for habit_row in habits:
                logger.info(f"Habit: {habit_row['name']}, Description: {habit_row['description']}, Frequency: {habit_row['frequency']}")
                habits_list.append(habit_row)
        else:
            logger.info("Habits list is empty, nothing to be displayed.")
        return habits_list

    def modify_habit(self, updated_habit: dict, value_to_update: str) -> None:
        """Modify an existing habit in the database."""
        self.habit_handler.modify_habit(updated_habit, value_to_update)

    def mark_done(self, habit_name: str) -> None:
        """Mark a habit as done."""
        logger.info(f"Marking habit: {habit_name} as done.")
        habits = execute_query(self.db_con, "SELECT name, description, frequency, done FROM habits")
        if habits:
            for habit in habits:
                if habit["name"] == habit_name:
                    habit["done"] = True
                    execute_query(self.db_con, "UPDATE habits SET done = ? WHERE name = ?",
                                  (1, habit_name))
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
    habit.initialize_database()
    habit.list_habits()
    # habit.add_habit(name="Playing chess daily", description="I want to play chess daily to reach 1000 ELO", frequency="Daily")
    # habit.add_habit(name="Reading books", description="Read at least one book per month", frequency="Monthly")
    # habit.add_habit(name="Morning Exercise", description="Do a 30-minute workout every morning", frequency="Daily")
    # habit.add_habit(name="Meditation", description="Meditate for 10 minutes every day", frequency="Daily")
    # habit.modify_habit(
    #     updated_habit={
    #         "name": "Playing chess weekly",
    #         "description": "I want to play chess weekly to reach 1000 ELO",
    #         "frequency": "Weekly"
    #     },
    #     value_to_update="Playing chess daily"
    # )
    # habit.list_habits()
    # habit.mark_done("Morning Exercise")
