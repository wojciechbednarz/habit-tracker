import sqlite3
from sqlite3 import Connection, Cursor
from typing import Optional, List, Tuple, Any
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def get_db_connection(db_path: str) -> Connection:
    """Establish a connection to the SQLite database."""
    try:
        conn = sqlite3.connect(db_path)
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        raise

def execute_query(conn: Connection, query: str, params: Optional[Tuple[Any, ...]] = None) -> Cursor:
    """Execute a SQL query with optional parameters."""
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        return cursor
    except sqlite3.Error as e:
        print(f"Error executing query: {e}")
        raise