"""SQL execution tool for the AI Analyst Agent.

This module provides a safe interface for executing SQL queries
against the DuckDB database with proper error handling.
"""

from app.core.database import run_query
from app.core.logging_config import setup_logger

logger = setup_logger(__name__)

def execute_sql(sql: str):
    """Execute a SQL query and return results.
    
    Provides a safe wrapper around database query execution with
    error handling and consistent return format.
    
    Args:
        sql: SQL query string to execute
        
    Returns:
        list: Query results as list of dictionaries
        dict: Error information if query fails
    """
    logger.debug(f"Executing SQL via tool: {sql[:50] + '...' if len(sql) > 50 else sql}")
    
    try:
        # Execute the query and convert to list of dictionaries
        result = run_query(sql)
        records = result.to_dict(orient="records")
        logger.info(f"SQL tool executed successfully, returned {len(records)} rows")
        return records
    except Exception as e:
        # Return error information for debugging
        logger.error(f"SQL tool execution failed: {e}")
        return {"error": str(e)}