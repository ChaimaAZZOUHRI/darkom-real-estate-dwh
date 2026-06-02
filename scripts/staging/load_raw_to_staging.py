import logging
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import text


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.append(str(SCRIPTS_DIR))

from utils.db_connection import get_engine  # noqa: E402


RAW_FILE = PROJECT_ROOT / "data" / "raw" / "darkom-annonces_raw.csv"
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)


EXPECTED_COLUMNS = [
    "annonce_id",
    "date_publication",
    "titre",
    "ville",
    "quartier",
    "type_bien",
    "transaction",
    "prix",
    "surface",
    "nb_chambres",
    "nb_salles_bain",
    "etage",
    "annee_construction",
]


def get_logger():
    logger = logging.getLogger("load_raw_to_staging")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        log_file = LOG_DIR / "load_raw_to_staging.log"

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s"
        )

        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


logger = get_logger()


def create_staging_table_if_not_exists():
    create_sql = """
    CREATE SCHEMA IF NOT EXISTS staging;

    CREATE TABLE IF NOT EXISTS staging.darkom_annonces_raw (
        annonce_id TEXT,
        date_publication TEXT,
        titre TEXT,
        ville TEXT,
        quartier TEXT,
        type_bien TEXT,
        transaction TEXT,
        prix TEXT,
        surface TEXT,
        nb_chambres TEXT,
        nb_salles_bain TEXT,
        etage TEXT,
        annee_construction TEXT
    );
    """

    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(text(create_sql))

    logger.info("Staging schema and table checked successfully.")


def load_raw_to_staging():
    try:
        logger.info("Starting raw data loading process.")

        if not RAW_FILE.exists():
            raise FileNotFoundError(f"CSV file not found: {RAW_FILE}")

        logger.info("Input file found: %s", RAW_FILE)

        df = pd.read_csv(RAW_FILE, encoding="utf-8-sig")

        logger.info(
            "CSV loaded successfully with %s rows and %s columns.",
            df.shape[0],
            df.shape[1],
        )

        df.columns = [str(col).strip() for col in df.columns]

        missing_columns = [
            col for col in EXPECTED_COLUMNS if col not in df.columns
        ]

        if missing_columns:
            raise ValueError(f"Missing columns in CSV file: {missing_columns}")

        df = df[EXPECTED_COLUMNS]

        df = df.astype("string")
        df = df.where(pd.notna(df), None)

        create_staging_table_if_not_exists()

        engine = get_engine()

        with engine.begin() as conn:
            conn.execute(text("TRUNCATE TABLE staging.darkom_annonces_raw;"))

            df.to_sql(
                name="darkom_annonces_raw",
                con=conn,
                schema="staging",
                if_exists="append",
                index=False,
                method="multi",
            )

            total_rows = conn.execute(
                text("SELECT COUNT(*) FROM staging.darkom_annonces_raw;")
            ).scalar()

        logger.info("Raw data loaded successfully into staging.darkom_annonces_raw.")
        logger.info("Total rows inserted: %s", total_rows)
        logger.info("Raw data loading process finished successfully.")

    except Exception as error:
        logger.exception("Raw data loading failed: %s", error)
        raise


if __name__ == "__main__":
    load_raw_to_staging()