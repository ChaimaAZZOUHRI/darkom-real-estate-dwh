import logging

from utils.project_paths import LOG_DIR


def get_logger(logger_name, log_filename):
    """
    Create a dedicated logger for each script.
    Each script writes logs into its own log file.
    """

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        log_file = LOG_DIR / log_filename

        file_handler = logging.FileHandler(log_file, encoding="utf-8")

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s"
        )

        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def log_step(logger, step_number, title):
    """
    Write a clear step title in the log file.
    """

    logger.info("")
    logger.info("=" * 90)
    logger.info("STEP %s - %s", step_number, title)
    logger.info("=" * 90)


def log_missing_values(logger, df, columns, label):
    """
    Log missing values for selected columns.
    """

    logger.info("Missing values summary: %s", label)

    for col in columns:
        if col in df.columns:
            missing_count = int(df[col].isna().sum())
            missing_percent = round(df[col].isna().mean() * 100, 2)

            logger.info(
                "  %-25s | missing: %-5s | percent: %s%%",
                col,
                missing_count,
                missing_percent,
            )