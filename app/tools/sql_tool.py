"""SQL execution tool for the AI Analyst Agent.

This module provides a safe interface for executing SQL queries
against the DuckDB database with proper error handling.
"""

from app.core.database import run_query


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
    try:
        # Execute the query and convert to list of dictionaries
        result = run_query(sql)
        return result.to_dict(orient="records")
    except Exception as e:
        # Return error information for debugging
        return {"error": str(e)}