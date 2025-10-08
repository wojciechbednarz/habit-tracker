"""Helper functions for habit tracking application."""
import json
from src.utils.logger import setup_logger


logger = setup_logger(__name__)


def check_if_key_exists_in_json(file_name: str, value_related_to_habit: str) -> bool:
    """Check if a specific key exists in a JSON file."""
    logger.debug(f"Checking if value exists in the file: {file_name}")
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            loaded_json = json.load(f)
        if loaded_json is None:
            return False
        for list_value in loaded_json:
            if isinstance(list_value, dict):
                for _, loaded_value in list_value.items():
                    if loaded_value == value_related_to_habit:
                        logger.debug(f"Loaded key: {loaded_value} is the same as provided one: {value_related_to_habit}")
                        return True
        return False
    except ValueError as e:
        logger.error(f"There was an error during loading json file {file_name}, error: {e}")
        return False
    except FileNotFoundError as e:
        logger.error(f"File {file_name} not found, error: {e}")
        return False

def read_json_file(file_name: str):
    """Read and return the contents of a JSON file."""
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"Successfully read JSON file: {file_name}")
        return data
    except FileNotFoundError as e:
        logger.error(f"File {file_name} not found, error: {e}")
        return None
    except ValueError as e:
        logger.error(f"There was an error during loading json file {file_name}, error: {e}")
        return None

def write_json_file(file_name: str, data) -> None:
    """Write data to a JSON file."""
    try:
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        logger.info(f"Successfully wrote to JSON file: {file_name}")
    except Exception as e:
        logger.error(f"An error occurred while writing to JSON file: {file_name}, error: {e}")

def modify_json_file(file_name: str, updated_data: dict, value_to_update: str) -> None:
    """Modify an existing JSON file with updated data."""
    try:
        existing_data = read_json_file(file_name)
        if existing_data is None:
            logger.error(f"Cannot modify JSON file: {file_name} because it could not be read.")
            return
        for i, item in enumerate(existing_data):
            if isinstance(item, dict) and item.get("name") == value_to_update:
                existing_data[i] = updated_data
                break
        write_json_file(file_name, existing_data)
        logger.info(f"Successfully modified JSON file: {file_name}")
    except Exception as e:
        logger.error(f"An error occurred while modifying JSON file: {file_name}, error: {e}")

def initialize_json_file(file_name: str) -> None:
    """Initialize a JSON file with an empty dictionary if it doesn't exist."""
    try:
        if not read_json_file(file_name):
            with open(file_name, "w", encoding="utf-8") as f:
                json.dump([], f)
        else:
            logger.info(f"JSON file: {file_name} already initialized.")
            return
        logger.info(f"Initialized new JSON file: {file_name}")
    except FileExistsError:
        logger.info(f"JSON file: {file_name} already exists. No action taken.")
    except Exception as e:
        logger.error(f"An error occurred while initializing JSON file: {file_name}, error: {e}")
