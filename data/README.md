# Data

| File | What it is |
|---|---|
| `raw/ppob_transactions_aug2026_masked.csv` | Masked export of every transaction on 1, 5 and 6 August 2026 (316,376 rows, 10 columns). This is the single source for every number in the project, including the Power BI model. |
| `database/ppob_transactions_aug2026.db` | SQLite copy of the same data after cleaning, with indexes and three views. Rebuilt by `python src/build_database.py`. Used by the SQL queries and the Python scripts. |

## Columns

| Raw CSV column | Database column | Description |
|---|---|---|
| Biller Transaction ID | `biller_transaction_id` | Reference returned by the biller. Empty for 4,644 rows (stored as NULL). |
| Transaction ID | `transaction_id` | Unique gateway transaction number. |
| Request Timestamp | `request_timestamp` | When the partner sent the request (WIB, `YYYY-MM-DD HH:MM:SS`). |
| Product Code | `product_code` | SKU, for example `SB20`. Upper-cased in the database (see below). |
| Customer Number | `customer_number` | Pseudonymised customer ID (`CUST_` + hash). |
| Biller Name | `biller_name` | Pseudonymised upstream supplier (`Biller_01` to `Biller_31`). |
| Status | `status` | `success` or `failed`. |
| Partner Name | `partner_name` | Pseudonymised downstream partner (46 partners). |
| Serial Number | `serial_number` | Token or receipt number from the biller, with names masked. Empty for all 32,150 failed rows. |
| Transaction Date | `transaction_date` | Date part of the request timestamp. |
| | `transaction_hour` | Hour 0 to 23, derived from the request timestamp. |
| | `day_of_week` | Day name, derived from the request timestamp. |

Database views: `v_daily_biller_summary` (volume and success rate per day and biller), `v_hourly_traffic`
(volume and failures per hour) and `v_customer_frequency` (transactions per customer).

## Cleaning

- Product codes are trimmed and upper-cased. The source mixes cases for the same SKU (`XDG1` and `xdg1`), so the
  318 raw codes collapse to 294 SKUs. The raw CSV is left untouched; the Power BI query applies the same rule.
- Status is lower-cased. Empty text fields become NULL.
- No rows are dropped.

## Masking

Customer numbers, biller, partner and personal names were replaced with deterministic pseudonyms before the data
was published. The mapping file is kept out of version control (see `.gitignore`).
