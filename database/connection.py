# database/connection.py

import mysql.connector
from config.db_config import (HOST, USER, PASSWORD, DATABASE)


class DatabaseConnectionError(Exception):
    """Raised when the application cannot connect to the database."""
    pass


def create_connection():

    try:
        connection = mysql.connector.connect(
            host=HOST,
            user=USER,
            password=PASSWORD,
            database=DATABASE
        )

        return connection

    except mysql.connector.Error as e:
        # Fail loudly and clearly instead of returning None, which used to
        # crash every caller downstream with a confusing
        # "NoneType has no attribute 'cursor'" error.
        raise DatabaseConnectionError(
            f"Could not connect to the database: {e}"
        ) from e