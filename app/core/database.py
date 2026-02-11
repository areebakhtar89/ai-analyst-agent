import duckdb
import pandas as pd

DB_PATH = "data/analytics.duckdb"


def init_db():
    conn = duckdb.connect(DB_PATH)

    # Load CSV into table
    df = pd.read_csv("data/sales.csv")
    conn.execute("CREATE OR REPLACE TABLE sales AS SELECT * FROM df")

    conn.close()


def run_query(sql: str):
    conn = duckdb.connect(DB_PATH)
    result = conn.execute(sql).fetchdf()
    conn.close()
    return result