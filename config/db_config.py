# config/db_config.py

import os

HOST = os.getenv("DB_HOST", "127.0.0.1")
USER = os.getenv("DB_USER", "bankapp")
PASSWORD = os.getenv("DB_PASSWORD", "")
DATABASE = os.getenv("DB_NAME", "banking_system")
