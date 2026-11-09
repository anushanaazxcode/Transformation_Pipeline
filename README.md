# Task 02 — Transformation Pipeline

## Overview
This project reads `sales_data.csv`, loads it into a raw SQLite table, creates a
typed staging table, and produces a clean final table for analysis.

## Input file
Keep `sales_data.csv` in the same folder as `transform.py`. It must contain:

- `order_id`
- `product`
- `category`
- `quantity`
- `unit_price`

## Pipeline layers

1. **Raw layer — `sales`:** source CSV values are loaded as text. The CSV file
   remains unchanged.
2. **Staging layer — `staging_sales`:** `order_id` and `quantity` are converted
   to integers; `unit_price` is converted to a decimal-style REAL value.
   Rows that cannot be converted are rejected.
3. **Final layer — `final_sales`:** blank product/category values, quantities
   less than or equal to zero, and negative prices are excluded. Duplicate
   `order_id` values are reduced to one row (the first valid source row).
   `total_amount` is calculated as `quantity * unit_price`.

## Tools
- Python 3
- SQLite
- SQL

Only Python's standard library is used; no pip packages are required.

## Run locally
1. Clone or download this repository.
2. Keep `sales_data.csv` and `transform.py` in the same folder.
3. Run:

   ```bash
   python transform.py
   ```

The script automatically creates `sales.db`, builds all three tables, and
prints row counts and a preview of the final table.

## Run in Google Colab

```python
!git clone https://github.com/anushanaazxcode/Transformation_Pipeline.git
%cd Transformation_Pipeline
!python transform.py
```

## Verify the output

```python
import sqlite3

conn = sqlite3.connect("sales.db")

for table in ("sales", "staging_sales", "final_sales"):
    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(table, count)

print(conn.execute("SELECT * FROM final_sales LIMIT 5").fetchall())
conn.close()
```

## Notes
The pipeline recreates its raw, staging, and final tables each time it runs, so
re-running it with the same CSV produces a fresh result. `sales.db` is generated
when the script runs and does not need to be committed to GitHub.
