"""Transform raw sales records into staging and analyst-ready tables."""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "sales.db"


def connect_database():
    """Open the SQLite database created in Task 01."""
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            "sales.db not found. Copy sales.db from your Task 01 repository "
            "into this project folder."
        )
    return sqlite3.connect(DATABASE_PATH)


def create_staging_layer(connection):
    """Create a typed staging table from the raw landing table."""
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

    raw_rows = connection.execute("""
        SELECT order_id, product, category, quantity, unit_price
        FROM sales
    """).fetchall()

    staged_rows = []
    for row in raw_rows:
        order_id, product, category, quantity, unit_price = row
        try:
            staged_rows.append((
                int(order_id),
                str(product).strip(),
                str(category).strip(),
                int(quantity),
                float(unit_price)
            ))
        except (TypeError, ValueError):
            # Skip rows that cannot be converted to the required data types.
            continue

    connection.executemany("""
        INSERT INTO staging_sales
        (order_id, product, category, quantity, unit_price)
        VALUES (?, ?, ?, ?, ?)
    """, staged_rows)

    return len(raw_rows), len(staged_rows)


def create_final_layer(connection):
    """Remove duplicates and invalid values, then create the final table."""
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

    # Keep one record per order_id and reject blank or non-positive values.
    connection.execute("""
        INSERT INTO final_sales
        (order_id, product, category, quantity, unit_price, total_amount)
        SELECT
            order_id,
            product,
            category,
            quantity,
            unit_price,
            ROUND(quantity * unit_price, 2)
        FROM staging_sales
        WHERE product IS NOT NULL
          AND TRIM(product) <> ''
          AND category IS NOT NULL
          AND TRIM(category) <> ''
          AND quantity > 0
          AND unit_price >= 0
        GROUP BY order_id
    """)


def show_results(connection, raw_count, staged_count):
    """Print row counts and a small preview for verification."""
    final_count = connection.execute(
        "SELECT COUNT(*) FROM final_sales"
    ).fetchone()[0]

    print("Transformation pipeline completed.")
    print(f"Raw rows read:       {raw_count}")
    print(f"Staging rows:        {staged_count}")
    print(f"Final clean rows:    {final_count}")
    print("\nFinal analyst-ready table:")
    for row in connection.execute("""
        SELECT order_id, product, category, quantity, unit_price, total_amount
        FROM final_sales
        ORDER BY order_id
    """):
        print(row)


def main():
    connection = connect_database()
    try:
        raw_count, staged_count = create_staging_layer(connection)
        create_final_layer(connection)
        connection.commit()
        show_results(connection, raw_count, staged_count)
    finally:
        connection.close()


if __name__ == "__main__":
    main()
