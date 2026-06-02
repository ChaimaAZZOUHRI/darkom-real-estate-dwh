import logging
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import text


# ============================================================
# Project paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.append(str(SCRIPTS_DIR))

from utils.db_connection import get_engine  # noqa: E402


# ============================================================
# Logger
# ============================================================

LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)


def get_logger():
    """
    Create a specific logger for the warehouse loading step.
    Logs are saved in logs/load_warehouse.log.
    """

    logger = logging.getLogger("load_warehouse")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        log_file = LOG_DIR / "load_warehouse.log"

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s"
        )

        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


logger = get_logger()


def log_step(step_number, title):
    """
    Write a clear step title in the log file.
    """

    logger.info("")
    logger.info("=" * 90)
    logger.info("STEP %s - %s", step_number, title)
    logger.info("=" * 90)


# ============================================================
# Create warehouse tables
# ============================================================

def create_warehouse_tables(engine):
    """
    Create the BI schema and all warehouse tables.

    The model is a star schema:
    - dim_date
    - dim_location
    - dim_property
    - dim_transaction
    - fact_annonces
    """

    create_sql = """
    CREATE SCHEMA IF NOT EXISTS bi_schema;

    DROP TABLE IF EXISTS bi_schema.fact_annonces;
    DROP TABLE IF EXISTS bi_schema.dim_date;
    DROP TABLE IF EXISTS bi_schema.dim_location;
    DROP TABLE IF EXISTS bi_schema.dim_property;
    DROP TABLE IF EXISTS bi_schema.dim_transaction;

    CREATE TABLE bi_schema.dim_date (
        date_id SERIAL PRIMARY KEY,
        date_publication DATE UNIQUE,
        annee_publication INTEGER,
        mois_publication INTEGER,
        trimestre_publication INTEGER
    );

    CREATE TABLE bi_schema.dim_location (
        location_id SERIAL PRIMARY KEY,
        ville TEXT,
        quartier TEXT,
        UNIQUE (ville, quartier)
    );

    CREATE TABLE bi_schema.dim_property (
        property_id SERIAL PRIMARY KEY,
        type_bien TEXT,
        categorie_surface TEXT,
        surface_bin TEXT,
        UNIQUE (type_bien, categorie_surface, surface_bin)
    );

    CREATE TABLE bi_schema.dim_transaction (
        transaction_id SERIAL PRIMARY KEY,
        transaction TEXT UNIQUE
    );

    CREATE TABLE bi_schema.fact_annonces (
        fact_id SERIAL PRIMARY KEY,
        annonce_id TEXT UNIQUE,

        date_id INTEGER REFERENCES bi_schema.dim_date(date_id),
        location_id INTEGER REFERENCES bi_schema.dim_location(location_id),
        property_id INTEGER REFERENCES bi_schema.dim_property(property_id),
        transaction_id INTEGER REFERENCES bi_schema.dim_transaction(transaction_id),

        prix NUMERIC,
        prix_capped NUMERIC,

        surface NUMERIC,
        surface_capped NUMERIC,

        prix_m2 NUMERIC,
        prix_m2_capped NUMERIC,

        nb_chambres INTEGER,
        nb_salles_bain INTEGER,
        etage INTEGER,
        annee_construction INTEGER,
        age_bien INTEGER,

        categorie_prix TEXT,

        is_outlier BOOLEAN,
        prix_is_outlier BOOLEAN,
        surface_is_outlier BOOLEAN,
        prix_m2_is_outlier BOOLEAN,

        date_publication_imputed BOOLEAN,
        quartier_imputed BOOLEAN,
        type_bien_imputed BOOLEAN,
        transaction_imputed BOOLEAN,
        nb_chambres_imputed BOOLEAN,
        nb_salles_bain_imputed BOOLEAN,
        etage_imputed BOOLEAN,
        annee_construction_imputed BOOLEAN
    );

    CREATE INDEX idx_fact_annonces_date_id
    ON bi_schema.fact_annonces(date_id);

    CREATE INDEX idx_fact_annonces_location_id
    ON bi_schema.fact_annonces(location_id);

    CREATE INDEX idx_fact_annonces_property_id
    ON bi_schema.fact_annonces(property_id);

    CREATE INDEX idx_fact_annonces_transaction_id
    ON bi_schema.fact_annonces(transaction_id);

    CREATE INDEX idx_fact_annonces_prix
    ON bi_schema.fact_annonces(prix);

    CREATE INDEX idx_fact_annonces_surface
    ON bi_schema.fact_annonces(surface);

    CREATE INDEX idx_fact_annonces_prix_m2
    ON bi_schema.fact_annonces(prix_m2);
    """

    with engine.begin() as conn:
        conn.execute(text(create_sql))

    logger.info("BI schema and warehouse tables created successfully.")


# ============================================================
# Main warehouse loading function
# ============================================================

def load_warehouse():
    """
    Load clean data into the warehouse star schema.
    Source: clean.darkom_annonces_clean
    Target: bi_schema dimensions and fact table
    """

    try:
        logger.info("")
        logger.info("#" * 90)
        logger.info("STARTING WAREHOUSE LOADING")
        logger.info("#" * 90)

        engine = get_engine()

        # ------------------------------------------------------------
        # Step 1 - Read clean data
        # ------------------------------------------------------------

        log_step(1, "READ CLEAN DATA")

        df = pd.read_sql_query(
            "SELECT * FROM clean.darkom_annonces_clean;",
            engine,
        )

        logger.info("Rows loaded from clean layer: %s", df.shape[0])
        logger.info("Columns loaded from clean layer: %s", df.shape[1])
        logger.info("Columns: %s", list(df.columns))

        if df.empty:
            raise ValueError("The clean table is empty. Run the cleaning script first.")

        # ------------------------------------------------------------
        # Step 2 - Create BI schema and tables
        # ------------------------------------------------------------

        log_step(2, "CREATE BI SCHEMA AND TABLES")

        create_warehouse_tables(engine)

        # ------------------------------------------------------------
        # Step 3 - Load dim_date
        # ------------------------------------------------------------

        log_step(3, "LOAD DIM_DATE")

        dim_date = (
            df[
                [
                    "date_publication",
                    "annee_publication",
                    "mois_publication",
                    "trimestre_publication",
                ]
            ]
            .drop_duplicates()
            .copy()
        )

        dim_date.to_sql(
            name="dim_date",
            con=engine,
            schema="bi_schema",
            if_exists="append",
            index=False,
            method="multi",
        )

        logger.info("Rows inserted into dim_date: %s", len(dim_date))

        # ------------------------------------------------------------
        # Step 4 - Load dim_location
        # ------------------------------------------------------------

        log_step(4, "LOAD DIM_LOCATION")

        dim_location = (
            df[["ville", "quartier"]]
            .drop_duplicates()
            .copy()
        )

        dim_location.to_sql(
            name="dim_location",
            con=engine,
            schema="bi_schema",
            if_exists="append",
            index=False,
            method="multi",
        )

        logger.info("Rows inserted into dim_location: %s", len(dim_location))

        # ------------------------------------------------------------
        # Step 5 - Load dim_property
        # ------------------------------------------------------------

        log_step(5, "LOAD DIM_PROPERTY")

        dim_property = (
            df[["type_bien", "categorie_surface", "surface_bin"]]
            .drop_duplicates()
            .copy()
        )

        dim_property.to_sql(
            name="dim_property",
            con=engine,
            schema="bi_schema",
            if_exists="append",
            index=False,
            method="multi",
        )

        logger.info("Rows inserted into dim_property: %s", len(dim_property))

        # ------------------------------------------------------------
        # Step 6 - Load dim_transaction
        # ------------------------------------------------------------

        log_step(6, "LOAD DIM_TRANSACTION")

        dim_transaction = (
            df[["transaction"]]
            .drop_duplicates()
            .copy()
        )

        dim_transaction.to_sql(
            name="dim_transaction",
            con=engine,
            schema="bi_schema",
            if_exists="append",
            index=False,
            method="multi",
        )

        logger.info("Rows inserted into dim_transaction: %s", len(dim_transaction))

        # ------------------------------------------------------------
        # Step 7 - Read dimension tables with generated IDs
        # ------------------------------------------------------------

        log_step(7, "READ DIMENSION IDS")

        dim_date_db = pd.read_sql_query(
            "SELECT * FROM bi_schema.dim_date;",
            engine,
        )

        dim_location_db = pd.read_sql_query(
            "SELECT * FROM bi_schema.dim_location;",
            engine,
        )

        dim_property_db = pd.read_sql_query(
            "SELECT * FROM bi_schema.dim_property;",
            engine,
        )

        dim_transaction_db = pd.read_sql_query(
            "SELECT * FROM bi_schema.dim_transaction;",
            engine,
        )

        logger.info("dim_date rows: %s", len(dim_date_db))
        logger.info("dim_location rows: %s", len(dim_location_db))
        logger.info("dim_property rows: %s", len(dim_property_db))
        logger.info("dim_transaction rows: %s", len(dim_transaction_db))

        # ------------------------------------------------------------
        # Step 8 - Build fact table with foreign keys
        # ------------------------------------------------------------

        log_step(8, "BUILD FACT TABLE")

        fact_df = df.copy()

        fact_df = fact_df.merge(
            dim_date_db,
            on=[
                "date_publication",
                "annee_publication",
                "mois_publication",
                "trimestre_publication",
            ],
            how="left",
        )

        fact_df = fact_df.merge(
            dim_location_db,
            on=["ville", "quartier"],
            how="left",
        )

        fact_df = fact_df.merge(
            dim_property_db,
            on=["type_bien", "categorie_surface", "surface_bin"],
            how="left",
        )

        fact_df = fact_df.merge(
            dim_transaction_db,
            on=["transaction"],
            how="left",
        )

        missing_fk = fact_df[
            ["date_id", "location_id", "property_id", "transaction_id"]
        ].isna().sum()

        logger.info("Missing foreign keys before loading:")
        logger.info("\n%s", missing_fk.to_string())

        fact_columns = [
            "annonce_id",
            "date_id",
            "location_id",
            "property_id",
            "transaction_id",

            "prix",
            "prix_capped",

            "surface",
            "surface_capped",

            "prix_m2",
            "prix_m2_capped",

            "nb_chambres",
            "nb_salles_bain",
            "etage",
            "annee_construction",
            "age_bien",

            "categorie_prix",

            "is_outlier",
            "prix_is_outlier",
            "surface_is_outlier",
            "prix_m2_is_outlier",

            "date_publication_imputed",
            "quartier_imputed",
            "type_bien_imputed",
            "transaction_imputed",
            "nb_chambres_imputed",
            "nb_salles_bain_imputed",
            "etage_imputed",
            "annee_construction_imputed",
        ]

        fact_df = fact_df[fact_columns]

        logger.info("Fact dataframe rows: %s", fact_df.shape[0])
        logger.info("Fact dataframe columns: %s", fact_df.shape[1])

        # ------------------------------------------------------------
        # Step 9 - Load fact_annonces
        # ------------------------------------------------------------

        log_step(9, "LOAD FACT_ANNONCES")

        fact_df = fact_df.astype(object).where(pd.notna(fact_df), None)

        fact_df.to_sql(
            name="fact_annonces",
            con=engine,
            schema="bi_schema",
            if_exists="append",
            index=False,
            method="multi",
        )

        logger.info("Rows inserted into fact_annonces: %s", len(fact_df))

        # ------------------------------------------------------------
        # Step 10 - Final validation
        # ------------------------------------------------------------

        log_step(10, "FINAL WAREHOUSE VALIDATION")

        with engine.connect() as conn:
            clean_count = conn.execute(
                text("SELECT COUNT(*) FROM clean.darkom_annonces_clean;")
            ).scalar()

            fact_count = conn.execute(
                text("SELECT COUNT(*) FROM bi_schema.fact_annonces;")
            ).scalar()

            dim_date_count = conn.execute(
                text("SELECT COUNT(*) FROM bi_schema.dim_date;")
            ).scalar()

            dim_location_count = conn.execute(
                text("SELECT COUNT(*) FROM bi_schema.dim_location;")
            ).scalar()

            dim_property_count = conn.execute(
                text("SELECT COUNT(*) FROM bi_schema.dim_property;")
            ).scalar()

            dim_transaction_count = conn.execute(
                text("SELECT COUNT(*) FROM bi_schema.dim_transaction;")
            ).scalar()

            missing_fk_result = conn.execute(
                text(
                    """
                    SELECT
                        COUNT(*) FILTER (WHERE date_id IS NULL) AS missing_date_id,
                        COUNT(*) FILTER (WHERE location_id IS NULL) AS missing_location_id,
                        COUNT(*) FILTER (WHERE property_id IS NULL) AS missing_property_id,
                        COUNT(*) FILTER (WHERE transaction_id IS NULL) AS missing_transaction_id
                    FROM bi_schema.fact_annonces;
                    """
                )
            ).mappings().first()

        logger.info("Rows in clean table: %s", clean_count)
        logger.info("Rows in fact_annonces: %s", fact_count)
        logger.info("Rows in dim_date: %s", dim_date_count)
        logger.info("Rows in dim_location: %s", dim_location_count)
        logger.info("Rows in dim_property: %s", dim_property_count)
        logger.info("Rows in dim_transaction: %s", dim_transaction_count)

        logger.info("Missing date_id: %s", missing_fk_result["missing_date_id"])
        logger.info("Missing location_id: %s", missing_fk_result["missing_location_id"])
        logger.info("Missing property_id: %s", missing_fk_result["missing_property_id"])
        logger.info("Missing transaction_id: %s", missing_fk_result["missing_transaction_id"])

        if clean_count == fact_count:
            logger.info("Validation status: SUCCESS. Clean and fact row counts match.")
        else:
            logger.warning("Validation status: WARNING. Clean and fact row counts do not match.")

        if all(value == 0 for value in missing_fk_result.values()):
            logger.info("Foreign key validation: SUCCESS. No missing foreign keys.")
        else:
            logger.warning("Foreign key validation: WARNING. Some foreign keys are missing.")

        logger.info("")
        logger.info("#" * 90)
        logger.info("WAREHOUSE LOADING FINISHED SUCCESSFULLY")
        logger.info("#" * 90)

    except Exception as error:
        logger.exception("Warehouse loading failed: %s", error)
        raise


if __name__ == "__main__":
    load_warehouse()