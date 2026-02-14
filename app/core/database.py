import duckdb
import pandas as pd
import os

DB_PATH = "data/analytics.duckdb"
DATA_FOLDER = "data"


def init_db():
    conn = duckdb.connect(DB_PATH)

    for file in os.listdir(DATA_FOLDER):
        if file.endswith(".csv"):
            table_name = file.replace(".csv", "")
            file_path = os.path.join(DATA_FOLDER, file)

            df = pd.read_csv(file_path)

            # Convert date columns properly
            if "order_date" in df.columns:
                df["order_date"] = pd.to_datetime(df["order_date"])

            conn.execute(
                f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df"
            )

            print(f"Loaded table: {table_name}")

    conn.close()
    print("Database initialized successfully.")

def run_query(sql: str):
    conn = duckdb.connect(DB_PATH)
    result = conn.execute(sql).fetchdf()
    conn.close()
    return result