import sys
import time
from pathlib import Path

from sqlalchemy import text


# ============================================================
# Allow Python to import shared scripts
# ============================================================

SCRIPTS_DIR = Path(__file__).resolve().parent

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))


# ============================================================
# Shared utilities
# ============================================================

from utils.db_connection import get_engine  # noqa: E402
from utils.logging_config import get_logger, log_step  # noqa: E402


# ============================================================
# Pipeline steps
# ============================================================

from staging.load_raw_to_staging import load_raw_to_staging  # noqa: E402
from clean.transform_clean_data import transform_clean_data  # noqa: E402
from warehouse.load_warehouse import load_warehouse  # noqa: E402


# ============================================================
# Logger for the full pipeline
# ============================================================

logger = get_logger(
    logger_name="run_pipeline",
    log_filename="run_pipeline.log",
)


# ============================================================
# Helper functions
# ============================================================

def test_database_connection():
    """
    Test the PostgreSQL connection before running the pipeline.
    """

    engine = get_engine()

    with engine.connect() as conn:
        database_name = conn.execute(
            text("SELECT current_database();")
        ).scalar()

    logger.info("Database connection successful.")
    logger.info("Connected database: %s", database_name)


def run_pipeline_step(step_number, step_name, step_function):
    """
    Run one pipeline step and log execution time.
    """

    log_step(logger, step_number, step_name)

    start_time = time.time()

    try:
        logger.info("Starting step: %s", step_name)

        step_function()

        elapsed_time = round(time.time() - start_time, 2)

        logger.info("Step completed successfully: %s", step_name)
        logger.info("Execution time: %s seconds", elapsed_time)

    except Exception as error:
        elapsed_time = round(time.time() - start_time, 2)

        logger.exception("Step failed: %s", step_name)
        logger.exception("Error: %s", error)
        logger.info("Execution time before failure: %s seconds", elapsed_time)

        raise


def validate_final_pipeline():
    """
    Validate final row counts after warehouse loading.
    """

    engine = get_engine()

    with engine.connect() as conn:
        staging_count = conn.execute(
            text("SELECT COUNT(*) FROM staging.darkom_annonces_raw;")
        ).scalar()

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

        missing_fk = conn.execute(
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

    log_step(logger, 4, "FINAL PIPELINE VALIDATION")

    logger.info("Rows in staging.darkom_annonces_raw: %s", staging_count)
    logger.info("Rows in clean.darkom_annonces_clean: %s", clean_count)
    logger.info("Rows in bi_schema.fact_annonces: %s", fact_count)
    logger.info("Rows in bi_schema.dim_date: %s", dim_date_count)
    logger.info("Rows in bi_schema.dim_location: %s", dim_location_count)
    logger.info("Rows in bi_schema.dim_property: %s", dim_property_count)
    logger.info("Rows in bi_schema.dim_transaction: %s", dim_transaction_count)

    logger.info("Missing date_id: %s", missing_fk["missing_date_id"])
    logger.info("Missing location_id: %s", missing_fk["missing_location_id"])
    logger.info("Missing property_id: %s", missing_fk["missing_property_id"])
    logger.info("Missing transaction_id: %s", missing_fk["missing_transaction_id"])

    if clean_count == fact_count:
        logger.info("Row count validation: SUCCESS. Clean and fact rows match.")
    else:
        logger.warning("Row count validation: WARNING. Clean and fact rows do not match.")

    if all(value == 0 for value in missing_fk.values()):
        logger.info("Foreign key validation: SUCCESS. No missing foreign keys.")
    else:
        logger.warning("Foreign key validation: WARNING. Missing foreign keys detected.")


# ============================================================
# Main pipeline
# ============================================================

def main():
    """
    Run the full Darkom data pipeline.

    Pipeline:
    Raw CSV -> Staging -> Clean -> Warehouse / BI schema
    """

    pipeline_start_time = time.time()

    try:
        logger.info("")
        logger.info("#" * 90)
        logger.info("STARTING FULL DARKOM DATA PIPELINE")
        logger.info("#" * 90)

        test_database_connection()

        run_pipeline_step(
            step_number=1,
            step_name="Load raw CSV to staging",
            step_function=load_raw_to_staging,
        )

        run_pipeline_step(
            step_number=2,
            step_name="Clean and transform data",
            step_function=transform_clean_data,
        )

        run_pipeline_step(
            step_number=3,
            step_name="Load warehouse / BI schema",
            step_function=load_warehouse,
        )

        validate_final_pipeline()

        total_time = round(time.time() - pipeline_start_time, 2)

        logger.info("")
        logger.info("#" * 90)
        logger.info("FULL DARKOM DATA PIPELINE FINISHED SUCCESSFULLY")
        logger.info("Total execution time: %s seconds", total_time)
        logger.info("#" * 90)

    except Exception as error:
        total_time = round(time.time() - pipeline_start_time, 2)

        logger.exception("FULL DARKOM DATA PIPELINE FAILED.")
        logger.exception("Error: %s", error)
        logger.info("Total execution time before failure: %s seconds", total_time)

        raise


if __name__ == "__main__":
    main()