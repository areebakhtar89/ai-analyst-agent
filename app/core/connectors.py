"""
app/core/connectors.py

Unified database connector layer.
Supports MySQL, PostgreSQL, SQLite, DuckDB.
All agents call run_query() — they never touch connection details directly.

Active connection is stored in:
    st.session_state["db_connection"] = {
        "type":     "mysql" | "postgresql" | "sqlite" | "duckdb",
        "host":     "...",
        "port":     3306,
        "user":     "...",
        "password": "...",
        "database": "...",
        "file":     "path/to/file.db"   # sqlite / duckdb only
    }
"""

import os
import pandas as pd
import decimal
import datetime
import math
from app.core.logging_config import setup_logger

logger = setup_logger(__name__)


# ── Type normalisation ────────────────────────────────────────────────────────

def _normalise_df(df: pd.DataFrame) -> pd.DataFrame:
    """Convert MySQL/PG-specific types to JSON-safe Python natives."""
    for col in df.columns:
        if df.empty:
            break
        sample = df[col].dropna()
        if sample.empty:
            continue
        first = sample.iloc[0]
        if isinstance(first, decimal.Decimal):
            df[col] = df[col].apply(lambda x: float(x) if isinstance(x, decimal.Decimal) else x)
        elif isinstance(first, datetime.timedelta):
            df[col] = df[col].astype(str)
    # Replace NaN → None (NaN is not JSON serialisable)
    df = df.where(df.notna(), other=None)
    return df


# ── MySQL ─────────────────────────────────────────────────────────────────────

def _mysql_query(config: dict, sql: str) -> pd.DataFrame:
    import mysql.connector
    conn = mysql.connector.connect(
        host=config["host"],
        port=int(config.get("port", 3306)),
        user=config["user"],
        password=config["password"],
        database=config["database"],
        charset="utf8mb4"
    )
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return pd.DataFrame(rows)


def _mysql_test(config: dict) -> tuple[bool, str]:
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host=config["host"],
            port=int(config.get("port", 3306)),
            user=config["user"],
            password=config["password"],
            database=config["database"],
            charset="utf8mb4",
            connect_timeout=5
        )
        conn.close()
        return True, "Connected successfully."
    except Exception as e:
        return False, str(e)


def _mysql_tables(config: dict) -> list[dict]:
    import mysql.connector
    conn = mysql.connector.connect(
        host=config["host"],
        port=int(config.get("port", 3306)),
        user=config["user"],
        password=config["password"],
        database=config["database"],
        charset="utf8mb4"
    )
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = [row[0] for row in cursor.fetchall()]
    schema = []
    for table in tables:
        cursor.execute(f"DESCRIBE {table}")
        cols = [{"name": r[0], "type": r[1]} for r in cursor.fetchall()]
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        schema.append({"table": table, "columns": cols, "row_count": count})
    cursor.close()
    conn.close()
    return schema


# ── PostgreSQL ────────────────────────────────────────────────────────────────

def _pg_query(config: dict, sql: str) -> pd.DataFrame:
    import psycopg2
    import psycopg2.extras
    conn = psycopg2.connect(
        host=config["host"],
        port=int(config.get("port", 5432)),
        user=config["user"],
        password=config["password"],
        dbname=config["database"]
    )
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(sql)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return pd.DataFrame([dict(r) for r in rows])


def _pg_test(config: dict) -> tuple[bool, str]:
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=config["host"],
            port=int(config.get("port", 5432)),
            user=config["user"],
            password=config["password"],
            dbname=config["database"],
            connect_timeout=5
        )
        conn.close()
        return True, "Connected successfully."
    except Exception as e:
        return False, str(e)


def _pg_tables(config: dict) -> list[dict]:
    import psycopg2
    import psycopg2.extras
    conn = psycopg2.connect(
        host=config["host"], port=int(config.get("port", 5432)),
        user=config["user"], password=config["password"], dbname=config["database"]
    )
    cursor = conn.cursor()
    cursor.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)
    tables = [row[0] for row in cursor.fetchall()]
    schema = []
    for table in tables:
        cursor.execute(f"""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = '{table}' AND table_schema = 'public'
        """)
        cols = [{"name": r[0], "type": r[1]} for r in cursor.fetchall()]
        cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
        count = cursor.fetchone()[0]
        schema.append({"table": table, "columns": cols, "row_count": count})
    cursor.close()
    conn.close()
    return schema


# ── SQLite ────────────────────────────────────────────────────────────────────

def _sqlite_query(config: dict, sql: str) -> pd.DataFrame:
    import sqlite3
    conn = sqlite3.connect(config["file"])
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    conn.close()
    return pd.DataFrame([dict(r) for r in rows])


def _sqlite_test(config: dict) -> tuple[bool, str]:
    try:
        import sqlite3
        if not os.path.exists(config["file"]):
            return False, f"File not found: {config['file']}"
        conn = sqlite3.connect(config["file"])
        conn.close()
        return True, "Connected successfully."
    except Exception as e:
        return False, str(e)


def _sqlite_tables(config: dict) -> list[dict]:
    import sqlite3
    conn = sqlite3.connect(config["file"])
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    schema = []
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        cols = [{"name": r[1], "type": r[2]} for r in cursor.fetchall()]
        cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
        count = cursor.fetchone()[0]
        schema.append({"table": table, "columns": cols, "row_count": count})
    conn.close()
    return schema


# ── DuckDB ────────────────────────────────────────────────────────────────────

def _duckdb_query(config: dict, sql: str) -> pd.DataFrame:
    import duckdb
    conn = duckdb.connect(config.get("file", ":memory:"))
    result = conn.execute(sql).fetchdf()
    conn.close()
    return result


def _duckdb_test(config: dict) -> tuple[bool, str]:
    try:
        import duckdb
        file = config.get("file", ":memory:")
        if file != ":memory:" and not os.path.exists(file):
            return False, f"File not found: {file}"
        conn = duckdb.connect(file)
        conn.close()
        return True, "Connected successfully."
    except Exception as e:
        return False, str(e)


def _duckdb_tables(config: dict) -> list[dict]:
    import duckdb
    conn = duckdb.connect(config.get("file", ":memory:"))
    tables_df = conn.execute("SHOW TABLES").fetchdf()
    schema = []
    for table in tables_df["name"].tolist():
        cols_df = conn.execute(f"DESCRIBE {table}").fetchdf()
        cols = [{"name": r["column_name"], "type": r["column_type"]}
                for _, r in cols_df.iterrows()]
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        schema.append({"table": table, "columns": cols, "row_count": count})
    conn.close()
    return schema


# ── Public API ────────────────────────────────────────────────────────────────

DRIVERS = {
    "mysql":      (_mysql_query,   _mysql_test,   _mysql_tables),
    "postgresql": (_pg_query,      _pg_test,      _pg_tables),
    "sqlite":     (_sqlite_query,  _sqlite_test,  _sqlite_tables),
    "duckdb":     (_duckdb_query,  _duckdb_test,  _duckdb_tables),
}


def run_query(config: dict, sql: str) -> pd.DataFrame:
    """Execute SQL against the given connection config. Returns a DataFrame."""
    db_type = config.get("type", "mysql").lower()
    if db_type not in DRIVERS:
        raise ValueError(f"Unsupported database type: {db_type}")
    query_fn, _, _ = DRIVERS[db_type]
    df = query_fn(config, sql)
    return _normalise_df(df)


def test_connection(config: dict) -> tuple[bool, str]:
    """Test connectivity. Returns (success: bool, message: str)."""
    db_type = config.get("type", "mysql").lower()
    if db_type not in DRIVERS:
        return False, f"Unsupported database type: {db_type}"
    _, test_fn, _ = DRIVERS[db_type]
    return test_fn(config)


def get_schema(config: dict) -> list[dict]:
    """Return list of {table, columns, row_count} for all tables."""
    db_type = config.get("type", "mysql").lower()
    if db_type not in DRIVERS:
        raise ValueError(f"Unsupported database type: {db_type}")
    _, _, schema_fn = DRIVERS[db_type]
    return schema_fn(config)
