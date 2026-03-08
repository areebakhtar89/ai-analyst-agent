"""
setup_mysql.py

Creates the olist_db MySQL database, all 9 tables with proper schema,
and loads data from the downloaded Olist CSVs.

Run from project root AFTER setup_kaggle.py:
    python scripts/setup_mysql.py
"""

import os
import sys
from pathlib import Path

import pandas as pd
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# ── Load .env ─────────────────────────────────────────────────────────────────
load_dotenv()

MYSQL_HOST     = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT     = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_USER     = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "olist_db")

RAW_DIR = Path("data/raw")

# ── Table definitions ─────────────────────────────────────────────────────────
# Each entry: (csv_filename, table_name, create_sql)
# Column names match EXACTLY what is in the CSVs — verified against actual headers
TABLES = [

    (
        "olist_customers_dataset.csv",
        "customers",
        """
        CREATE TABLE customers (
            customer_id               VARCHAR(50)  PRIMARY KEY,
            customer_unique_id        VARCHAR(50)  NOT NULL,
            customer_zip_code_prefix  VARCHAR(10),
            customer_city             VARCHAR(100),
            customer_state            VARCHAR(5)
        )
        """
    ),

    (
        "olist_sellers_dataset.csv",
        "sellers",
        """
        CREATE TABLE sellers (
            seller_id                VARCHAR(50)  PRIMARY KEY,
            seller_zip_code_prefix   VARCHAR(10),
            seller_city              VARCHAR(100),
            seller_state             VARCHAR(5)
        )
        """
    ),

    (
        "olist_products_dataset.csv",
        "products",
        """
        CREATE TABLE products (
            product_id                   VARCHAR(50)  PRIMARY KEY,
            product_category_name        VARCHAR(100),
            product_name_lenght          INT,
            product_description_lenght   INT,
            product_photos_qty           INT,
            product_weight_g             FLOAT,
            product_length_cm            FLOAT,
            product_height_cm            FLOAT,
            product_width_cm             FLOAT
        )
        """
    ),

    (
        "olist_orders_dataset.csv",
        "orders",
        """
        CREATE TABLE orders (
            order_id                        VARCHAR(50)  PRIMARY KEY,
            customer_id                     VARCHAR(50),
            order_status                    VARCHAR(30),
            order_purchase_timestamp        DATETIME,
            order_approved_at               DATETIME,
            order_delivered_carrier_date    DATETIME,
            order_delivered_customer_date   DATETIME,
            order_estimated_delivery_date   DATETIME,
            INDEX idx_customer_id  (customer_id),
            INDEX idx_order_status (order_status),
            INDEX idx_purchase_ts  (order_purchase_timestamp)
        )
        """
    ),

    (
        "olist_order_items_dataset.csv",
        "order_items",
        """
        CREATE TABLE order_items (
            order_id             VARCHAR(50),
            order_item_id        INT,
            product_id           VARCHAR(50),
            seller_id            VARCHAR(50),
            shipping_limit_date  DATETIME,
            price                FLOAT,
            freight_value        FLOAT,
            PRIMARY KEY (order_id, order_item_id),
            INDEX idx_product_id (product_id),
            INDEX idx_seller_id  (seller_id)
        )
        """
    ),

    (
        "olist_order_payments_dataset.csv",
        "order_payments",
        """
        CREATE TABLE order_payments (
            order_id              VARCHAR(50),
            payment_sequential    INT,
            payment_type          VARCHAR(30),
            payment_installments  INT,
            payment_value         FLOAT,
            PRIMARY KEY (order_id, payment_sequential),
            INDEX idx_payment_type (payment_type)
        )
        """
    ),

    (
        "olist_order_reviews_dataset.csv",
        "order_reviews",
        """
        CREATE TABLE order_reviews (
            review_id                VARCHAR(50),
            order_id                 VARCHAR(50),
            review_score             INT,
            review_comment_title     VARCHAR(255),
            review_comment_message   TEXT,
            review_creation_date     DATETIME,
            review_answer_timestamp  DATETIME,
            PRIMARY KEY (review_id),
            INDEX idx_order_id     (order_id),
            INDEX idx_review_score (review_score)
        )
        """
    ),

    (
        "olist_geolocation_dataset.csv",
        "geolocation",
        """
        CREATE TABLE geolocation (
            geolocation_zip_code_prefix  VARCHAR(10),
            geolocation_lat              FLOAT,
            geolocation_lng              FLOAT,
            geolocation_city             VARCHAR(100),
            geolocation_state            VARCHAR(5),
            INDEX idx_zip (geolocation_zip_code_prefix)
        )
        """
    ),

    (
        "product_category_name_translation.csv",
        "product_category_translation",
        """
        CREATE TABLE product_category_translation (
            product_category_name          VARCHAR(100) PRIMARY KEY,
            product_category_name_english  VARCHAR(100)
        )
        """
    ),
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_connection(database=None):
    """Get MySQL connection, optionally targeting a specific database."""
    return mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=database,
        charset="utf8mb4"
    )


def create_database(cursor):
    """Drop and recreate olist_db cleanly."""
    print(f"Creating database '{MYSQL_DATABASE}'...")
    cursor.execute(f"DROP DATABASE IF EXISTS {MYSQL_DATABASE}")
    cursor.execute(
        f"CREATE DATABASE {MYSQL_DATABASE} "
        f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    cursor.execute(f"USE {MYSQL_DATABASE}")
    print(f"Database '{MYSQL_DATABASE}' created.")


def create_tables(cursor):
    """Create all 9 tables."""
    print("\nCreating tables...")
    for _, table_name, create_sql in TABLES:
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        cursor.execute(create_sql)
        print(f"  Created: {table_name}")


def load_table(conn, csv_file, table_name):
    """Load a single CSV into its MySQL table."""
    csv_path = RAW_DIR / csv_file

    if not csv_path.exists():
        print(f"  SKIP  {table_name:<30} CSV not found: {csv_path}")
        return 0

    print(f"  Loading {table_name:<30}", end=" ", flush=True)

    # Read CSV
    df = pd.read_csv(csv_path, encoding="utf-8", low_memory=False)

    # Fix 1: Drop ghost columns — trailing commas in CSV headers create columns
    # literally named NaN or "Unnamed: N". MySQL rejects these as "Unknown column 'nan'"
    df = df.loc[:, ~df.columns.isna()]                          # drop NaN-named cols
    df = df.loc[:, ~df.columns.str.match(r'^Unnamed')]          # drop Unnamed: N cols
    df.columns = df.columns.str.strip()                         # strip whitespace from names

    # Fix 2: Replace NaN values with None so MySQL stores NULL not the string "nan"
    import numpy as np
    df = df.replace({np.nan: None})

    # Fix 3: For string columns, replace the string "nan" / "NaN" with None
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].apply(lambda x: None if str(x).strip().lower() == "nan" else x)

    # Fix 3: Convert datetime columns
    datetime_cols = [c for c in df.columns if "timestamp" in c or "date" in c]
    for col in datetime_cols:
        df[col] = pd.to_datetime(df[col], errors="coerce")
        df[col] = df[col].apply(
            lambda x: x.strftime("%Y-%m-%d %H:%M:%S") if pd.notna(x) else None
        )

    # Fix 4: Drop duplicate primary keys to avoid insertion errors
    # order_reviews has duplicate review_ids in the source CSV
    pk_cols = {
        "customers":                    ["customer_id"],
        "sellers":                      ["seller_id"],
        "products":                     ["product_id"],
        "orders":                       ["order_id"],
        "order_items":                  ["order_id", "order_item_id"],
        "order_payments":               ["order_id", "payment_sequential"],
        "order_reviews":                ["review_id"],
        "product_category_translation": ["product_category_name"],
    }
    if table_name in pk_cols:
        before = len(df)
        df = df.drop_duplicates(subset=pk_cols[table_name], keep="first")
        dropped = before - len(df)
        if dropped > 0:
            print(f"(dropped {dropped} duplicates) ", end="", flush=True)

    cursor = conn.cursor()
    cols         = ", ".join(df.columns)
    placeholders = ", ".join(["%s"] * len(df.columns))
    # INSERT IGNORE skips any remaining duplicate key rows silently
    sql          = f"INSERT IGNORE INTO {table_name} ({cols}) VALUES ({placeholders})"

    # Batch insert in chunks of 1000
    # Convert row values: float nan → None so MySQL receives NULL not "nan"
    import math

    def clean_row(row):
        result = []
        for v in row:
            if v is None:
                result.append(None)
            elif isinstance(v, float) and math.isnan(v):
                result.append(None)
            elif isinstance(v, str) and v.strip().lower() == "nan":
                result.append(None)
            else:
                result.append(v)
        return tuple(result)

    CHUNK = 1000
    rows  = [clean_row(r) for r in df.itertuples(index=False, name=None)]
    total = 0

    for i in range(0, len(rows), CHUNK):
        batch = rows[i: i + CHUNK]
        cursor.executemany(sql, batch)
        conn.commit()
        total += len(batch)

    cursor.close()
    print(f"{total:>10,} rows loaded.")
    return total


def print_summary(conn):
    """Print row counts for all tables."""
    print("\nDatabase summary:")
    print("-" * 45)
    cursor = conn.cursor()
    for _, table_name, _ in TABLES:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"  {table_name:<35} {count:>10,} rows")
    print("-" * 45)
    cursor.close()


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("  Olist MySQL Setup")
    print("=" * 50)

    # Step 1: Connect and create DB + tables
    print(f"\nConnecting to MySQL at {MYSQL_HOST}:{MYSQL_PORT} as '{MYSQL_USER}'...")
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        print("Connected successfully.")
    except Error as e:
        print(f"ERROR: Could not connect to MySQL: {e}")
        sys.exit(1)

    try:
        create_database(cursor)
        create_tables(cursor)
        conn.commit()
        cursor.close()
        conn.close()
    except Error as e:
        print(f"ERROR during setup: {e}")
        sys.exit(1)

    # Step 2: Reconnect with DB selected and load data
    print("\nLoading CSV data into tables...")
    print("-" * 50)
    try:
        conn       = get_connection(database=MYSQL_DATABASE)
        total_rows = 0
        errors     = []

        for csv_file, table_name, _ in TABLES:
            try:
                total_rows += load_table(conn, csv_file, table_name)
            except Exception as e:
                print(f"  ERROR loading {table_name}: {e}")
                errors.append((table_name, str(e)))

        print(f"\nTotal rows loaded: {total_rows:,}")

        if errors:
            print(f"\nErrors in {len(errors)} table(s):")
            for table, err in errors:
                print(f"  {table}: {err}")
        else:
            print_summary(conn)
            print("\nSetup complete.")
            print("Next step: python scripts/test_connection.py")

        conn.close()

    except Error as e:
        print(f"ERROR: {e}")
        sys.exit(1)