"""
test_connection.py

Verifies MySQL connection and Olist schema are working correctly.
Runs row count checks on all 8 tables and a multi-table JOIN test.

Run from project root:
    python scripts/test_connection.py
"""

import os
import sys
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

load_dotenv()

MYSQL_HOST     = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT     = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_USER     = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "olist_db")

# Expected minimum row counts — if below these, something went wrong
MIN_ROWS = {
    "orders":         90_000,
    "order_items":   110_000,
    "customers":      90_000,
    "products":        3_000,
    "sellers":         3_000,
    "order_payments": 100_000,
    "order_reviews":   90_000,
    "geolocation":    900_000,
}

# Multi-table JOIN tests
JOIN_TESTS = [
    (
        "orders + customers JOIN",
        """
        SELECT COUNT(*) FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        """
    ),
    (
        "orders + order_items JOIN",
        """
        SELECT COUNT(*) FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        """
    ),
    (
        "orders + payments JOIN",
        """
        SELECT COUNT(*) FROM orders o
        JOIN order_payments op ON o.order_id = op.order_id
        """
    ),
    (
        "3-table JOIN (orders + items + products)",
        """
        SELECT COUNT(*) FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.product_id
        """
    ),
    (
        "Revenue by state (real business query)",
        """
        SELECT c.customer_state, ROUND(SUM(op.payment_value), 2) AS total_revenue
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        JOIN order_payments op ON o.order_id = op.order_id
        WHERE o.order_status = 'delivered'
        GROUP BY c.customer_state
        ORDER BY total_revenue DESC
        LIMIT 5
        """
    ),
]


def run_tests():
    print("=" * 55)
    print("  Olist MySQL Connection Test")
    print("=" * 55)

    # ── Connect ───────────────────────────────────────────────
    print(f"\nConnecting to {MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}...")
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        cursor = conn.cursor()
        print("Connected successfully.\n")
    except Error as e:
        print(f"FAILED: {e}")
        sys.exit(1)

    passed = 0
    failed = 0

    # ── Row count tests ───────────────────────────────────────
    print("Row count checks:")
    print("-" * 55)
    for table, min_count in MIN_ROWS.items():
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            if count >= min_count:
                print(f"  PASS  {table:<25} {count:>10,} rows")
                passed += 1
            else:
                print(f"  FAIL  {table:<25} {count:>10,} rows  (expected >= {min_count:,})")
                failed += 1
        except Error as e:
            print(f"  ERROR {table:<25} {e}")
            failed += 1

    # ── JOIN tests ────────────────────────────────────────────
    print("\nJoin and query tests:")
    print("-" * 55)
    for test_name, sql in JOIN_TESTS:
        try:
            cursor.execute(sql)
            result = cursor.fetchall()
            if test_name.startswith("Revenue"):
                print(f"  PASS  {test_name}")
                for row in result:
                    print(f"        {row[0]:<5}  R${row[1]:>12,.2f}")
            else:
                count = result[0][0]
                print(f"  PASS  {test_name:<40} {count:>10,} rows")
            passed += 1
        except Error as e:
            print(f"  FAIL  {test_name:<40} {e}")
            failed += 1

    # ── Summary ───────────────────────────────────────────────
    print("-" * 55)
    print(f"\nResults: {passed} passed, {failed} failed")

    if failed == 0:
        print("\nAll tests passed.")
        print("MySQL + Olist schema is ready.")
        print("\nNext steps:")
        print("  1. Update app/tools/sql_tool.py  (already done if you ran Task 1)")
        print("  2. Start the backend: uvicorn app.api.main:app --reload")
        print("  3. Start the frontend: streamlit run app/ui/app.py")
    else:
        print("\nSome tests failed.")
        print("Re-run setup_mysql.py to reload the data.")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    run_tests()
