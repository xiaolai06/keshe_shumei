"""
Database — SQLite initialization and connection management
"""
import sqlite3
import logging
from pathlib import Path
from contextlib import contextmanager

import config

logger = logging.getLogger("SmartHome.db")

_db_path = config.DATA_DIR / "pet.db"


def init_db() -> None:
    """Initialize database: create tables from schema.sql"""
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    schema_path = Path(__file__).parent / "schema.sql"

    with open(schema_path, encoding="utf-8") as f:
        schema_sql = f.read()

    with get_conn() as conn:
        conn.executescript(schema_sql)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
    logger.info("Database initialized: %s", _db_path)


@contextmanager
def get_conn():
    """Context manager for a SQLite connection"""
    conn = sqlite3.connect(str(_db_path), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=5000")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
