"""Transform sales_data.csv into raw, staging, and final SQLite tables."""

import csv
import sqlite3
from pathlib import Path

HERE = Path(__file__).resolve().parent
CSV_FILE = HERE / "sales_data.csv"
DB_FILE = HERE / "sales.db"

EXPECTED_COLUMNS = ["order_id", "product", "category", "quantity", "unit_price"]


def load_raw_data(connection):
    """Load source CSV records into the raw sales table."""
    if not CSV_FILE.exists():
        raise FileNotFoundError(
            "sales_data.csv is missing. Put it in the same folder as transform.py."
        )

    with CSV_FILE.open("r", newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None or not set(EXPECTED_COLUMNS).issubset(reader.fieldnames):
            raise ValueError(f"CSV must contain these columns: {EXPECTED_COLUMNS}")

        rows = [
            tuple((record.get(column) or "").strip() for column in EXPECTED_COLUMNS)
            for record in reader
        ]

    connection.execute("DROP TABLE IF EXISTS sales")
    connection.execute("""
        CREATE TABLE sales (
            order_id TEXT,
            product TEXT,
            category TEXT,
            quantity TEXT,
            unit_price TEXT
        )
    """)
    connection.executemany(
        "INSERT INTO sales VALUES (?, ?, ?, ?, ?)", rows
    )
    return len(rows)


def build_staging(connection):
    """Cast raw text fields into typed staging columns."""
    connection.execute("DROP TABLE IF EXISTS staging_sales")
    connection.execute("""
        CREATE TABLE staging_sales (
            order_id INTEGER,
            product TEXT,
            category TEXT,
            quantity INTEGER,
            unit_price REAL
        )
    """)

    raw_rows = connection.execute(
        "SELECT order_id, product, category, quantity, unit_price FROM sales"
    ).fetchall()

    typed_rows = []
    rejected = 0

    for order_id, product, category, quantity, unit_price in raw_rows:
        try:
            typed_rows.append((
                int(order_id),
                product.strip(),
                category.strip(),
                int(quantity),
                float(unit_price)
            ))
        except (TypeError, ValueError):
            rejected += 1

    connection.executemany("""
        INSERT INTO staging_sales
        (order_id, product, category, quantity, unit_price)
        VALUES (?, ?, ?, ?, ?)
    """, typed_rows)

    return len(raw_rows), len(typed_rows), rejected


def build_final(connection):
    """Filter invalid records, keep one row per order, and calculate revenue."""
    connection.execute("DROP TABLE IF EXISTS final_sales")
    connection.execute("""
        CREATE TABLE final_sales (
            order_id INTEGER PRIMARY KEY,
            product TEXT NOT NULL,
            category TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            total_amount REAL NOT NULL
        )
    """)

    connection.execute("""
        INSERT INTO final_sales
        (order_id, product, category, quantity, unit_price, total_amount)
        SELECT order_id, product, category, quantity, unit_price,
               ROUND(quantity * unit_price, 2)
        FROM (
            SELECT *,
                   ROW_NUMBER() OVER (
                       PARTITION BY order_id ORDER BY rowid
                   ) AS row_num
            FROM staging_sales
            WHERE TRIM(product) <> ''
              AND TRIM(category) <> ''
              AND quantity > 0
              AND unit_price >= 0
        )
        WHERE row_num = 1
    """)


def print_report(connection, raw_count, staging_count, rejected_count):
    """Print row-count checks and a preview of the final table."""
    final_count = connection.execute(
        "SELECT COUNT(*) FROM final_sales"
    ).fetchone()[0]

    print("Transformation pipeline completed.")
    print(f"Raw rows loaded: {raw_count}")
    print(f"Staging rows: {staging_count}")
    print(f"Rows rejected during type casting: {rejected_count}")
    print(f"Final clean rows: {final_count}")
    print("\\nFinal analyst-ready data:")
    for row in connection.execute("""
        SELECT order_id, product, category, quantity, unit_price, total_amount
        FROM final_sales
        ORDER BY order_id
    """):
        print(row)


def main():
    connection = sqlite3.connect(DB_FILE)
    try:
        raw_count = load_raw_data(connection)
        _, staging_count, rejected_count = build_staging(connection)
        build_final(connection)
        connection.commit()
        print_report(connection, raw_count, staging_count, rejected_count)
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    main()
