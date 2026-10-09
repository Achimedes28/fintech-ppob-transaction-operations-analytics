"""Step 1 of the pipeline: build the cleaned SQLite database from the raw CSV export.

Cleaning applied:
  - column names converted to snake_case
  - product codes trimmed and upper-cased (the source mixes 'XDG1' and 'xdg1' for the same SKU)
  - status lower-cased ('success' / 'failed')
  - empty biller transaction IDs and serial numbers stored as NULL
  - transaction_hour and day_of_week derived from the request timestamp
Indexes and the analytical views used by sql/queries.sql are created at the end.

Run from the project root:  python src/build_database.py
"""
import os
import sqlite3

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_CSV = os.path.join(ROOT, "data", "raw", "ppob_transactions_aug2026_masked.csv")
DB = os.path.join(ROOT, "data", "database", "ppob_transactions_aug2026.db")

df = pd.read_csv(RAW_CSV, dtype=str, keep_default_na=False)
df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

df = df.replace("", None)
df["transaction_id"] = df["transaction_id"].astype("int64")
df["product_code"] = df["product_code"].str.strip().str.upper()
df["status"] = df["status"].str.strip().str.lower()
ts = pd.to_datetime(df["request_timestamp"])
df["transaction_hour"] = ts.dt.hour
df["day_of_week"] = ts.dt.day_name()

columns = ["biller_transaction_id", "transaction_id", "request_timestamp", "product_code", "customer_number",
           "biller_name", "status", "partner_name", "serial_number", "transaction_date", "transaction_hour",
           "day_of_week"]
df = df[columns]

os.makedirs(os.path.dirname(DB), exist_ok=True)
if os.path.exists(DB):
    os.remove(DB)
con = sqlite3.connect(DB)
con.executescript("""
CREATE TABLE transactions (
    biller_transaction_id TEXT,
    transaction_id        INTEGER,
    request_timestamp     TIMESTAMP,
    product_code          TEXT,
    customer_number       TEXT,
    biller_name           TEXT,
    status                TEXT,
    partner_name          TEXT,
    serial_number         TEXT,
    transaction_date      TEXT,
    transaction_hour      INTEGER,
    day_of_week           TEXT
);
""")
df.to_sql("transactions", con, if_exists="append", index=False)
con.executescript("""
CREATE INDEX idx_trans_date   ON transactions(transaction_date);
CREATE INDEX idx_biller_name  ON transactions(biller_name);
CREATE INDEX idx_partner_name ON transactions(partner_name);
CREATE INDEX idx_status       ON transactions(status);
CREATE INDEX idx_customer     ON transactions(customer_number);

CREATE VIEW v_daily_biller_summary AS
SELECT transaction_date,
       biller_name,
       COUNT(*) AS total_transactions,
       SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS success_count,
       SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_count,
       ROUND(SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS success_rate_pct
FROM transactions
GROUP BY transaction_date, biller_name;

CREATE VIEW v_hourly_traffic AS
SELECT transaction_hour,
       COUNT(*) AS total_transactions,
       SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS success_count,
       SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_count
FROM transactions
GROUP BY transaction_hour
ORDER BY transaction_hour;

CREATE VIEW v_customer_frequency AS
SELECT customer_number,
       COUNT(*) AS transaction_count,
       MIN(transaction_date) AS first_seen,
       MAX(transaction_date) AS last_seen,
       COUNT(DISTINCT product_code) AS distinct_products_bought
FROM transactions
GROUP BY customer_number
ORDER BY transaction_count DESC;
""")
con.execute("VACUUM")
con.close()
print(f"Built {DB} with {len(df):,} rows and {df['product_code'].nunique()} SKUs")
