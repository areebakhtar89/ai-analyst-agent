"""Database management module for the AI Analyst Agent.

Handles MySQL connection and query execution for the Olist dataset.
Replaces the original DuckDB implementation — interface is identical
so all other files (sql_tool.py, agents, etc.) work without changes.
"""

import os
import time
import pandas as pd
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
from .logging_config import setup_logger, log_query_execution

load_dotenv()
logger = setup_logger(__name__)

# MySQL connection config — read from .env
DB_CONFIG = {
    "host":     os.getenv("MYSQL_HOST", "localhost"),
    "port":     int(os.getenv("MYSQL_PORT", 3306)),
    "user":     os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "olist_db"),
    "charset":  "utf8mb4",
}


def get_connection():
    """Return a live MySQL connection using .env credentials."""
    return mysql.connector.connect(**DB_CONFIG)


def run_query(sql: str) -> pd.DataFrame:
    """Execute a SQL query and return results as a DataFrame.

    Drop-in replacement for the old DuckDB run_query — same signature,
    same return type, so sql_tool.py and all agents need no changes.

    Args:
        sql: SQL query string to execute

    Returns:
        pandas.DataFrame: Query results
    """
    logger.debug(f"Executing SQL query: {sql}")
    start_time = time.time()

    conn   = None
    cursor = None
    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql)
        rows   = cursor.fetchall()

        # Build DataFrame — same shape as DuckDB's fetchdf()
        result = pd.DataFrame(rows)

        # Convert MySQL-specific types that are not JSON serializable:
        # - decimal.Decimal → float  (MySQL DECIMAL/NUMERIC columns)
        # - datetime.timedelta → str (MySQL TIME columns)
        import decimal, datetime
        for col in result.columns:
            if result.empty:
                break
            sample = result[col].dropna()
            if sample.empty:
                continue
            first = sample.iloc[0]
            if isinstance(first, decimal.Decimal):
                result[col] = result[col].apply(
                    lambda x: float(x) if isinstance(x, decimal.Decimal) else x
                )
            elif isinstance(first, datetime.timedelta):
                result[col] = result[col].astype(str)

        # Replace NaN with None — NaN is not JSON serializable, None becomes null
        result = result.where(result.notna(), other=None)

        execution_time = time.time() - start_time

        log_query_execution(logger, sql, execution_time, len(result))
        return result

    except Error as e:
        execution_time = time.time() - start_time
        log_query_execution(logger, sql, execution_time, 0, str(e))
        logger.error(f"Query execution failed: {e}")
        raise

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def init_db():
    """Verify MySQL connection and log table row counts.

    The old DuckDB init_db() loaded CSVs into the DB.
    With MySQL, data is loaded once via setup_mysql.py —
    this function just confirms the connection is healthy.
    """
    logger.info("Verifying MySQL connection...")
    try:
        conn   = get_connection()
        cursor = conn.cursor()

        tables = [
            "orders", "order_items", "customers", "products",
            "sellers", "order_payments", "order_reviews",
            "geolocation", "product_category_translation"
        ]

        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            logger.info(f"  {table}: {count:,} rows")

        cursor.close()
        conn.close()
        logger.info("MySQL connection verified successfully.")

    except Error as e:
        logger.error(f"MySQL connection failed: {e}")
        raise