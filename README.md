# Task 02 — Transformation Pipeline

This project continues Task 01 (Extract and Load). It reads the raw `sales` table
from the SQLite database and creates two separate layers:

1. **Staging layer (`staging_sales`)** — converts values to the required data
   types: order ID and quantity to integers, and unit price to a real number.
2. **Final layer (`final_sales`)** — removes duplicate order IDs, filters invalid
   records, and calculates `total_amount = quantity * unit_price`.

## Technology
- Python 3
- SQLite
- SQL

## Project files
- `transform.py` — readable transformation pipeline
- `sales.db` — copy this database from Task 01 before running the script

## How to run
1. Download or clone this repository.
2. Copy `sales.db` from your Task 01 `Extract_and_Load` project into this folder.
3. Open a terminal in this folder.
4. Run:

   ```bash
   python transform.py
   ```

No extra Python packages are required.

## How to check the result
The script prints the raw, staging, and final row counts and displays the final
table. You can also open `sales.db` with a SQLite viewer and inspect:
- `sales` — original raw landing table
- `staging_sales` — typed staging layer
- `final_sales` — clean table for analysis

## Transformation decisions
- The raw `sales` table is kept unchanged.
- Staging and final tables are separate.
- Rows that cannot be type-cast are skipped during staging.
- Blank product/category values, non-positive quantities, and negative prices
  are excluded from the final table.
- Duplicate `order_id` values are reduced to one record in the final layer.

## Expected result for the Task 01 sample data
The source file contains 8 sales records. With the supplied sample data, the
staging and final layers should each contain 8 rows.
