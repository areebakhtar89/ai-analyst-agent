"""Database management module for the AI Analyst Agent.

This module handles database initialization, connection management,
and query execution using DuckDB for analytics operations.
"""

import duckdb
import pandas as pd
import os

# Database configuration
DB_PATH = "data/analytics.duckdb"
DATA_FOLDER = "data"


def init_db():
    """Initialize the DuckDB database with CSV data.
    
    Scans the data folder for CSV files and creates corresponding tables
    in DuckDB. Automatically handles date column conversion for known columns.
    """
    # Connect to DuckDB database
    conn = duckdb.connect(DB_PATH)

    # Process each CSV file in the data folder
    for file in os.listdir(DATA_FOLDER):
        if file.endswith(".csv"):
            # Extract table name from filename
            table_name = file.replace(".csv", "")
            file_path = os.path.join(DATA_FOLDER, file)

            # Read CSV into pandas DataFrame
            df = pd.read_csv(file_path)

            # Convert date columns to proper datetime format
            if "order_date" in df.columns:
                df["order_date"] = pd.to_datetime(df["order_date"])

            # Create or replace table in DuckDB
            conn.execute(
                f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df"
            )

            print(f"Loaded table: {table_name}")

    # Close database connection
    conn.close()
    print("Database initialized successfully.")


def run_query(sql: str):
    """Execute a SQL query against the DuckDB database.
    
    Args:
        sql: SQL query string to execute
        
    Returns:
        pandas.DataFrame: Query results as a DataFrame
    """
    # Connect to database
    conn = duckdb.connect(DB_PATH)
    
    # Execute query and fetch results as DataFrame
    result = conn.execute(sql).fetchdf()
    
    # Close connection
    conn.close()
    
    return result