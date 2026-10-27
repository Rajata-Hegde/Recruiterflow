import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "data"
DB_DIR.mkdir(exist_ok=True)

# Default SQLite Database Path
DB_PATH = os.getenv("DATABASE_PATH", str(DB_DIR / "recruiterflow.db"))

DDL_FILE_PATH = BASE_DIR / "app" / "ddl.sql"
SEED_FILE_PATH = BASE_DIR / "app" / "seed.sql"
STATIC_DIR = BASE_DIR / "app" / "static"
