import os
import logging
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Load .env
load_dotenv(PROJECT_ROOT / ".env")

# Logs folder
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)


def get_db_logger():
    """
    Create a dedicated logger only for database connection.
    It writes only to logs/db_connection.log.
    """

    logger = logging.getLogger("db_connection")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        log_file = LOG_DIR / "db_connection.log"

        file_handler = logging.FileHandler(log_file, encoding="utf-8")

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s"
        )

        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_engine():
    """
    Create and return a SQLAlchemy engine for PostgreSQL.
    This function is reused by staging, clean, and warehouse scripts.
    """

    url = URL.create(
        drivername="postgresql+psycopg2",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME"),
    )

    return create_engine(url)


def test_connection():
    """
    Test the database connection and write the result to db_connection.log.
    """

    logger = get_db_logger()

    try:
        logger.info("Starting database connection test.")

        engine = get_engine()

        with engine.connect() as conn:
            database_name = conn.execute(
                text("SELECT current_database();")
            ).scalar()

        logger.info("Connected successfully to database: %s", database_name)
        logger.info("Database connection test finished successfully.")

    except Exception as error:
        logger.exception("Database connection failed: %s", error)
        raise


if __name__ == "__main__":
    test_connection()