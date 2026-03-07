"""Database management module for the AI Analyst Agent.

This module handles database initialization, connection management,
and query execution using DuckDB for analytics operations.
"""

import duckdb
import pandas as pd
import os
import time
from .logging_config import setup_logger, log_query_execution

logger = setup_logger(__name__)

# Database configuration
DB_PATH = "data/analytics.duckdb"
DATA_FOLDER = "data"


def init_db():
    """Initialize the DuckDB database with CSV data.
    
    Scans the data folder for CSV files and creates corresponding tables
    in DuckDB. Automatically handles date column conversion for known columns.
    """
    logger.info("Starting database initialization")
    logger.debug(f"Database path: {DB_PATH}")
    logger.debug(f"Data folder: {DATA_FOLDER}")
    
    try:
        # Connect to DuckDB database
        logger.debug("Connecting to DuckDB database")
        conn = duckdb.connect(DB_PATH)
        logger.info("Successfully connected to DuckDB database")

        # Check if data folder exists
        if not os.path.exists(DATA_FOLDER):
            logger.error(f"Data folder does not exist: {DATA_FOLDER}")
            raise FileNotFoundError(f"Data folder not found: {DATA_FOLDER}")
        
        # Process each CSV file in the data folder
        csv_files = [f for f in os.listdir(DATA_FOLDER) if f.endswith(".csv")]
        logger.info(f"Found {len(csv_files)} CSV files to process")
        
        for file in csv_files:
            logger.debug(f"Processing file: {file}")
            
            # Extract table name from filename
            table_name = file.replace(".csv", "")
            file_path = os.path.join(DATA_FOLDER, file)
            
            try:
                # Read CSV into pandas DataFrame
                logger.debug(f"Reading CSV file: {file_path}")
                df = pd.read_csv(file_path)
                logger.info(f"Loaded {len(df)} rows from {file}")

                # Convert date columns to proper datetime format
                if "order_date" in df.columns:
                    logger.debug("Converting order_date column to datetime")
                    df["order_date"] = pd.to_datetime(df["order_date"])

                # Create or replace table in DuckDB
                logger.debug(f"Creating table: {table_name}")
                conn.execute(
                    f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df"
                )
                logger.info(f"Successfully created table: {table_name} with {len(df.columns)} columns")

            except Exception as e:
                logger.error(f"Failed to process file {file}: {e}")
                continue

        # Close database connection
        conn.close()
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


def run_query(sql: str):
    """Execute a SQL query against the DuckDB database.
    
    Args:
        sql: SQL query string to execute
        
    Returns:
        pandas.DataFrame: Query results as a DataFrame
    """
    logger.debug(f"Executing SQL query: {sql}")
    start_time = time.time()
    
    try:
        # Connect to database
        logger.debug("Connecting to database for query execution")
        conn = duckdb.connect(DB_PATH)
        
        # Execute query and fetch results as DataFrame
        logger.debug("Executing SQL query")
        result = conn.execute(sql).fetchdf()
        
        # Calculate execution time
        execution_time = time.time() - start_time
        row_count = len(result)
        
        # Log successful query execution
        log_query_execution(logger, sql, execution_time, row_count)
        
        # Close connection
        conn.close()
        logger.debug("Database connection closed")
        
        return result
        
    except Exception as e:
        execution_time = time.time() - start_time
        error_msg = str(e)
        log_query_execution(logger, sql, execution_time, 0, error_msg)
        logger.error(f"Query execution failed: {error_msg}")
        raise