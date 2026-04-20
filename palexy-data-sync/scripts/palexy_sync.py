#!/usr/bin/env python3
"""Palexy API → DuckDB sync script for Mắt Việt stores."""

import os
import sys
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta, date
import duckdb

API_BASE = "https://ica.palexy.com"
API_KEY = os.environ.get("Palexy_API_KEY", "")
DB_PATH = "/home/workspace/Data/palexy.duckdb"

DIMENSIONS = [
    "store_id", "store_code", "store_name",
    "store_metadata_1", "store_metadata_2", "store_metadata_3",
    "day"
]

METRICS = [
    "visits", "walk_ins", "average_dwell_time",
    "interacted_customers", "interaction_rate", "average_interaction_time",
    "pass_by_traffic", "capture_rate",
    "net_sales_transactions", "conversion_rate", "sales_per_visitor",
    "net_sales_amount", "net_sales_items", "atv", "upt", "asp",
    "average_visitors_per_staff_at_an_hour",
    "group_rate", "average_group_size",
    "greeting_rate", "on_time_greeting_rate",
]

def api_get(endpoint, params=None):
    url = f"{API_BASE}{endpoint}"
    if params:
        parts = []
        for k, v in params:
            parts.append(f"{urllib.parse.quote(k)}={urllib.parse.quote(str(v))}")
        url += "?" + "&".join(parts)
    req = urllib.request.Request(url, headers={"api_key": API_KEY})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode())

def fetch_store_report(from_date: str, to_date: str):
    params = []
    for d in DIMENSIONS:
        params.append(("dimensions", d))
    for m in METRICS:
        params.append(("metrics", m))
    params.append(("fromDate", from_date))
    params.append(("toDate", to_date))
    data = api_get("/api/v2/report/getStoreReport", params)
    return data.get("rows", [])

def fetch_stores():
    data = api_get("/api/v2/model/stores")
    return data.get("stores", [])

def init_db(con):
    con.execute("""
        CREATE TABLE IF NOT EXISTS stores (
            store_id INTEGER PRIMARY KEY,
            store_code VARCHAR,
            store_name VARCHAR
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS daily_store_metrics (
            store_id INTEGER,
            store_code VARCHAR,
            store_name VARCHAR,
            store_type VARCHAR,
            area_manager VARCHAR,
            tier VARCHAR,
            day DATE,
            visits INTEGER,
            walk_ins INTEGER,
            average_dwell_time DOUBLE,
            interacted_customers INTEGER,
            interaction_rate DOUBLE,
            average_interaction_time DOUBLE,
            pass_by_traffic INTEGER,
            capture_rate DOUBLE,
            net_sales_transactions INTEGER,
            conversion_rate DOUBLE,
            sales_per_visitor DOUBLE,
            net_sales_amount DOUBLE,
            net_sales_items INTEGER,
            atv DOUBLE,
            upt DOUBLE,
            asp DOUBLE,
            average_visitors_per_staff DOUBLE,
            group_rate DOUBLE,
            average_group_size DOUBLE,
            greeting_rate DOUBLE,
            on_time_greeting_rate DOUBLE,
            synced_at TIMESTAMP DEFAULT current_timestamp,
            PRIMARY KEY (store_id, day)
        )
    """)

def parse_val(v, typ="float"):
    if v is None or v == "":
        return None
    if typ == "int":
        return int(float(v))
    return float(v)

def rows_to_tuples(rows):
    tuples = []
    for row in rows:
        tuples.append((
            parse_val(row.get("store_id"), "int"),
            row.get("store_code", ""),
            row.get("store_name", ""),
            row.get("store_metadata_1", ""),
            row.get("store_metadata_2", ""),
            row.get("store_metadata_3", ""),
            row.get("day", ""),
            parse_val(row.get("visits"), "int"),
            parse_val(row.get("walk_ins"), "int"),
            parse_val(row.get("average_dwell_time")),
            parse_val(row.get("interacted_customers"), "int"),
            parse_val(row.get("interaction_rate")),
            parse_val(row.get("average_interaction_time")),
            parse_val(row.get("pass_by_traffic"), "int"),
            parse_val(row.get("capture_rate")),
            parse_val(row.get("net_sales_transactions"), "int"),
            parse_val(row.get("conversion_rate")),
            parse_val(row.get("sales_per_visitor")),
            parse_val(row.get("net_sales_amount")),
            parse_val(row.get("net_sales_items"), "int"),
            parse_val(row.get("atv")),
            parse_val(row.get("upt")),
            parse_val(row.get("asp")),
            parse_val(row.get("average_visitors_per_staff_at_an_hour")),
            parse_val(row.get("group_rate")),
            parse_val(row.get("average_group_size")),
            parse_val(row.get("greeting_rate")),
            parse_val(row.get("on_time_greeting_rate")),
        ))
    return tuples

def batch_insert(con, rows):
    if not rows:
        return 0
    tuples = rows_to_tuples(rows)
    con.execute("DELETE FROM daily_store_metrics WHERE day IN (SELECT DISTINCT day FROM (VALUES " +
                ",".join([f"('{r.get('day','')}'::DATE)" for r in rows]) + ") AS t(day))")
    con.executemany("""
        INSERT INTO daily_store_metrics (
            store_id, store_code, store_name,
            store_type, area_manager, tier, day,
            visits, walk_ins, average_dwell_time,
            interacted_customers, interaction_rate, average_interaction_time,
            pass_by_traffic, capture_rate,
            net_sales_transactions, conversion_rate, sales_per_visitor,
            net_sales_amount, net_sales_items, atv, upt, asp,
            average_visitors_per_staff,
            group_rate, average_group_size,
            greeting_rate, on_time_greeting_rate
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, tuples)
    return len(tuples)

def sync_date_range(con, start: date, end: date, chunk_days=90):
    """Pull data in chunks (default 90 days for speed)."""
    total = 0
    current = start
    while current <= end:
        chunk_end = min(current + timedelta(days=chunk_days - 1), end)
        from_str = current.strftime("%Y-%m-%d")
        to_str = chunk_end.strftime("%Y-%m-%d")
        print(f"  Fetching {from_str} → {to_str} ...", flush=True)
        rows = fetch_store_report(from_str, to_str)
        count = batch_insert(con, rows)
        total += count
        print(f"  → {count} rows inserted.", flush=True)
        current = chunk_end + timedelta(days=1)
    return total

def sync_stores(con):
    stores = fetch_stores()
    con.executemany("""
        INSERT OR REPLACE INTO stores (store_id, store_code, store_name)
        VALUES (?, ?, ?)
    """, [(s["id"], s.get("code", ""), s["name"]) for s in stores])
    print(f"  Synced {len(stores)} stores.", flush=True)

def cmd_full(args):
    start = date.fromisoformat(args[0]) if len(args) > 0 else date(2025, 1, 1)
    end = date.fromisoformat(args[1]) if len(args) > 1 else (date.today() - timedelta(days=1))
    print(f"=== Full sync: {start} → {end} ===", flush=True)
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = duckdb.connect(DB_PATH)
    init_db(con)
    sync_stores(con)
    total = sync_date_range(con, start, end)
    row_count = con.execute("SELECT count(*) FROM daily_store_metrics").fetchone()[0]
    print(f"=== Done. {total} rows synced. DB total: {row_count} ===", flush=True)
    con.close()

def cmd_daily(args):
    yesterday = date.today() - timedelta(days=1)
    target = date.fromisoformat(args[0]) if len(args) > 0 else yesterday
    print(f"=== Daily sync: {target} ===", flush=True)
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = duckdb.connect(DB_PATH)
    init_db(con)
    sync_stores(con)
    total = sync_date_range(con, target, target, chunk_days=1)
    print(f"=== Done. {total} rows synced for {target} ===", flush=True)
    con.close()

def cmd_status(args):
    con = duckdb.connect(DB_PATH, read_only=True)
    total = con.execute("SELECT count(*) FROM daily_store_metrics").fetchone()[0]
    min_day = con.execute("SELECT min(day) FROM daily_store_metrics").fetchone()[0]
    max_day = con.execute("SELECT max(day) FROM daily_store_metrics").fetchone()[0]
    stores = con.execute("SELECT count(DISTINCT store_id) FROM daily_store_metrics").fetchone()[0]
    print(f"Total rows: {total:,}")
    print(f"Date range: {min_day} → {max_day}")
    print(f"Stores: {stores}")
    by_type = con.execute("SELECT store_type, count(DISTINCT store_id) as n FROM daily_store_metrics GROUP BY store_type ORDER BY store_type").fetchall()
    for t, n in by_type:
        print(f"  {t}: {n} stores")
    by_tier = con.execute("SELECT tier, count(DISTINCT store_id) as n FROM daily_store_metrics GROUP BY tier ORDER BY tier").fetchall()
    for t, n in by_tier:
        print(f"  {t}: {n} stores")
    con.close()

def main():
    if not API_KEY:
        print("ERROR: Palexy_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    if len(sys.argv) < 2:
        print("Usage: palexy_sync.py <full|daily|status> [args...]")
        print("  full [start_date] [end_date]  — Full historical sync")
        print("  daily [date]                   — Sync one day (default: yesterday)")
        print("  status                         — Show DB stats")
        sys.exit(0)
    cmd = sys.argv[1]
    args = sys.argv[2:]
    {"full": cmd_full, "daily": cmd_daily, "status": cmd_status}.get(cmd, lambda a: print(f"Unknown: {cmd}"))(args)

if __name__ == "__main__":
    main()
