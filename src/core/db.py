"""Database interaction module."""
import sqlite3
from sqlite3 import Connection, Cursor
from typing import Optional, Tuple, Any
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def get_db_connection(db_path: str) -> Connection:
    """Establish a connection to the SQLite database."""
    try:
        conn = sqlite3.connect(db_path)
        return conn
    except sqlite3.Error as e:
        logger.error(f"Error connecting to database: {e}")
        raise


def execute_query(
    conn: Connection, query: str, params: Optional[Tuple[Any, ...]] = None
) -> Cursor:
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
        logger.error(f"Error executing query: {e}")
        raise


def set_row_factory_as_dict(conn: Connection, row: sqlite3.Row = sqlite3.Row) -> None:
    """Sets row factory to return dictionary-like object"""
    logger.debug("Setting the row factory to return dictionary-like object.")
    conn.row_factory = row


def fetch_all_results(
    conn: Connection, query: str, params: Optional[Tuple[Any, ...]] = None
) -> dict:
    """Fetches all results from the database."""
    logger.info("Fetching the results from database...")
    try:
        set_row_factory_as_dict(conn=conn)
        cur = execute_query(conn, query, params)
        return cur.fetchall()
    except sqlite3.Error as e:
        logger.error(f"Error while fetching the results: {e}")
        raise

def create_table(conn: Connection, table_creation_query: str) -> None:
    """Create a table in the database."""
    try:
        cursor = conn.cursor()
        cursor.execute(table_creation_query)
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Error creating table: {e}")
        raise


