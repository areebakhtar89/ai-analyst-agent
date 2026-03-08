"""
app/core/database.py

Routes all SQL queries through the active connection.

Priority:
1. If a connection config is passed explicitly → use it
2. If FastAPI request context has an active connection → use it
3. Fall back to .env MySQL config (Task 1 default)

All agents call run_query(sql) — they never need to know which DB is active.
"""

import os
import time
import pandas as pd
from dotenv import load_dotenv
from app.core.logging_config import setup_logger, log_query_execution

load_dotenv()
logger = setup_logger(__name__)

# ── Default .env config (Task 1 / fallback) ───────────────────────────────────
_DEFAULT_CONFIG = {
    "type":     "mysql",
    "host":     os.getenv("MYSQL_HOST", "localhost"),
    "port":     int(os.getenv("MYSQL_PORT", 3306)),
    "user":     os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "olist_db"),
}

# Active connection config — set by /connect API endpoint
# When None, falls back to _DEFAULT_CONFIG
_active_config: dict | None = None


def set_active_connection(config: dict):
    """Called by the /connect endpoint when user connects a new DB."""
    global _active_config
    _active_config = config
    logger.info(
        f"[DB] ✓ Active connection CHANGED to: "
        f"{config.get('type','?').upper()} / "
        f"{config.get('database') or config.get('file','?')} "
        f"@ {config.get('host', 'local')}"
    )


def get_active_config() -> dict:
    """Return the currently active connection config."""
    if _active_config is not None:
        logger.debug(
            f"[DB] Using USER-connected DB: "
            f"{_active_config.get('type').upper()} / "
            f"{_active_config.get('database') or _active_config.get('file')}"
        )
        return _active_config
    else:
        logger.debug(
            f"[DB] Using FALLBACK .env DB: "
            f"{_DEFAULT_CONFIG.get('type').upper()} / "
            f"{_DEFAULT_CONFIG.get('database')}"
        )
        return _DEFAULT_CONFIG


def run_query(sql: str, config: dict = None) -> pd.DataFrame:
    """Execute SQL and return a DataFrame.

    Args:
        sql:    SQL query to execute
        config: Optional explicit config. Uses active connection if None.

    Returns:
        pd.DataFrame
    """
    from app.core.connectors import run_query as _connector_query

    active = config or get_active_config()
    source = "USER-CONNECTED" if _active_config is not None else "FALLBACK-.ENV"
    logger.info(
        f"[DB] Executing query on {source} "
        f"({active.get('type','?').upper()} / "
        f"{active.get('database') or active.get('file','?')})"
    )
    start  = time.time()

    try:
        result         = _connector_query(active, sql)
        execution_time = time.time() - start
        log_query_execution(logger, sql, execution_time, len(result))
        return result

    except Exception as e:
        execution_time = time.time() - start
        log_query_execution(logger, sql, execution_time, 0, str(e))
        logger.error(f"Query failed: {e}")
        raise


def init_db():
    """Verify the active connection is healthy and log table counts."""
    from app.core.connectors import get_schema
    logger.info("Verifying database connection...")
    try:
        config = get_active_config()
        schema = get_schema(config)
        for t in schema:
            logger.info(f"  {t['table']:<35} {t['row_count']:>10,} rows")
        logger.info("Connection verified.")
    except Exception as e:
        logger.error(f"Connection verification failed: {e}")
        raise


def get_connection():
    """Return a raw DB connection (used by legacy code paths)."""
    config = get_active_config()
    db_type = config.get("type", "mysql")
    if db_type == "mysql":
        import mysql.connector
        return mysql.connector.connect(
            host=config["host"], port=int(config.get("port", 3306)),
            user=config["user"], password=config["password"],
            database=config["database"], charset="utf8mb4"
        )
    elif db_type == "postgresql":
        import psycopg2
        return psycopg2.connect(
            host=config["host"], port=int(config.get("port", 5432)),
            user=config["user"], password=config["password"],
            dbname=config["database"]
        )
    elif db_type == "sqlite":
        import sqlite3
        return sqlite3.connect(config["file"])
    elif db_type == "duckdb":
        import duckdb
        return duckdb.connect(config.get("file", ":memory:"))
    else:
        raise ValueError(f"Unsupported DB type: {db_type}")
