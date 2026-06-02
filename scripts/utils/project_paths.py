from pathlib import Path


# Root of the project: darkom-real-estate-dwh
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

LOG_DIR = PROJECT_ROOT / "logs"
SQL_DIR = PROJECT_ROOT / "sql"

RAW_FILE = RAW_DIR / "darkom-annonces_raw.csv"

LOG_DIR.mkdir(exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)