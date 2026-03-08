"""SQL execution tool for the AI Analyst Agent.

Provides a safe interface for executing read-only SQL queries
against the MySQL Olist database with proper error handling.
"""

import mysql.connector
from app.core.database import run_query
from app.core.logging_config import setup_logger

logger = setup_logger(__name__)

# Blocked keywords — prevent any destructive operations
BLOCKED = {"DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "CREATE", "REPLACE"}


def execute_sql(sql: str):
    """Execute a read-only SQL query and return results as a list of dicts.

    Args:
        sql: SQL query string to execute (SELECT only)

    Returns:
        list[dict]: Query results, one dict per row
        dict:       {"error": "..."} if query fails or is blocked
    """
    # Safety check — block any destructive SQL
    first_word = sql.strip().split()[0].upper() if sql.strip() else ""
    if first_word in BLOCKED:
        logger.warning(f"Blocked destructive SQL: {first_word}")
        return {"error": f"Operation '{first_word}' is not permitted. Only SELECT queries are allowed."}

    short = sql[:80] + "..." if len(sql) > 80 else sql
    logger.debug(f"Executing SQL: {short}")

    try:
        df      = run_query(sql)
        records = df.to_dict(orient="records")
        logger.info(f"SQL executed successfully — {len(records)} rows returned")
        return records

    except mysql.connector.Error as e:
        logger.error(f"MySQL error: {e}")
        return {"error": str(e)}

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"error": str(e)}