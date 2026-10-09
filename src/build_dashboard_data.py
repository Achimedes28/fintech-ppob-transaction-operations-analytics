"""Step 3 of the pipeline: aggregate the cleaned database and embed the result in dashboard/index.html.

The HTML dashboard has no server, so its data lives inside the page as a JavaScript object.

Run from the project root:  python src/build_dashboard_data.py
"""
import json
import os
import sqlite3

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "data", "database", "ppob_transactions_aug2026.db")
HTML = os.path.join(ROOT, "dashboard", "index.html")

df = pd.read_sql_query(
    "SELECT transaction_date, request_timestamp, product_code, biller_name, status, partner_name, customer_number FROM transactions",
    sqlite3.connect(DB),
)
df["product_code"] = df["product_code"].astype(str).str.strip().str.upper()
df["failed"] = (df["status"].str.lower() != "success").astype(int)
df["success"] = 1 - df["failed"]
df["transaction_hour"] = pd.to_datetime(df["request_timestamp"]).dt.hour
total_failed = int(df["failed"].sum())


def agg(keys):
    return df.groupby(keys).agg(total=("failed", "size"), success=("success", "sum"), failed=("failed", "sum")).reset_index()


def with_rates(g):
    g["fail_rate"] = (g["failed"] / g["total"] * 100).round(2)
    g["success_rate"] = (g["success"] / g["total"] * 100).round(2)
    g["fail_contribution"] = (g["failed"] / total_failed * 100).round(2)
    return g.sort_values("total", ascending=False, kind="stable")


def records(g):
    return json.loads(g.to_json(orient="records"))


data = {
    "summary": {
        "total_tx": int(len(df)),
        "total_success": int(df["success"].sum()),
        "total_failed": total_failed,
        "success_rate": round(float(df["success"].mean()) * 100, 2),
        "fail_rate": round(float(df["failed"].mean()) * 100, 2),
        "unique_products": int(df["product_code"].nunique()),
        "unique_billers": int(df["biller_name"].nunique()),
        "unique_partners": int(df["partner_name"].nunique()),
        "unique_customers": int(df["customer_number"].nunique()),
    },
    "daily": records(agg(["transaction_date"])),
    "hourly": records(agg(["transaction_hour"])),
    "billers": records(with_rates(agg(["biller_name"]))),
    "products": records(with_rates(agg(["product_code"]))),
    "hourly_biller": records(agg(["transaction_hour", "biller_name"])),
    "cube": records(agg(["transaction_date", "biller_name", "product_code"])),
}

html = open(HTML, encoding="utf-8").read()
start = html.index("const rawData = ") + len("const rawData = ")
_, end = json.JSONDecoder().raw_decode(html[start:])
html = html[:start] + json.dumps(data) + html[start + end:]
open(HTML, "w", encoding="utf-8").write(html)
print("Dashboard data rebuilt:", data["summary"])
