#!/usr/bin/env python3
"""Generate dashboard JSON from Palexy DuckDB for zo.space dashboard."""
import duckdb
import json
import os
from datetime import datetime, timedelta

DB_PATH = "/home/workspace/Data/palexy.duckdb"
OUT_PATH = "/home/workspace/Data/palexy_dashboard.json"

CLOSED_STORES = [
    "Counter - Lotte Cần Thơ",
    "Street - Tôn Thất Tùng",
    "Counter - Vincom Liễu Giai",
    "Counter - Vincom Thảo Điền",
    "Boutique - Vincom Center Trần Duy Hưng",
]

def closed_filter(alias=""):
    prefix = f"{alias}." if alias else ""
    conditions = " AND ".join([f"{prefix}store_name != '{s}'" for s in CLOSED_STORES])
    return f"AND {conditions}"

def run():
    con = duckdb.connect(DB_PATH, read_only=True)

    # Use latest available date in DB, not today
    latest_date = con.execute("SELECT MAX(day) FROM daily_store_metrics").fetchone()[0]
    yesterday = latest_date  # this is the most recent data date

    # Date ranges
    # Current week (Mon-Sun)
    current_week_start = yesterday - timedelta(days=yesterday.weekday())
    current_week_end = yesterday

    # Last week
    last_week_end = current_week_start - timedelta(days=1)
    last_week_start = last_week_end - timedelta(days=last_week_end.weekday())

    # Current month
    current_month_start = yesterday.replace(day=1)

    # YoY comparisons
    yesterday_ly = yesterday.replace(year=yesterday.year - 1)
    cw_start_ly = current_week_start.replace(year=current_week_start.year - 1)
    cw_end_ly = current_week_end.replace(year=current_week_end.year - 1)
    cm_start_ly = current_month_start.replace(year=current_month_start.year - 1)
    cm_end_ly = yesterday.replace(year=yesterday.year - 1)

    result = {}

    # 1. Overall KPIs: yesterday, this week, this month + YoY
    for label, start, end, start_ly, end_ly in [
        ("yesterday", yesterday, yesterday, yesterday_ly, yesterday_ly),
        ("this_week", current_week_start, current_week_end, cw_start_ly, cw_end_ly),
        ("this_month", current_month_start, yesterday, cm_start_ly, cm_end_ly),
    ]:
        q = f"""
        SELECT
            SUM(visits) as visits,
            SUM(walk_ins) as walk_ins,
            SUM(pass_by_traffic) as pass_by,
            SUM(net_sales_transactions) as transactions,
            SUM(net_sales_amount) as revenue,
            SUM(net_sales_items) as items,
            CASE WHEN SUM(visits)>0 THEN SUM(net_sales_transactions)*1.0/SUM(visits) ELSE 0 END as cr,
            CASE WHEN SUM(net_sales_transactions)>0 THEN SUM(net_sales_amount)/SUM(net_sales_transactions) ELSE 0 END as atv,
            CASE WHEN SUM(net_sales_transactions)>0 THEN SUM(net_sales_items)*1.0/SUM(net_sales_transactions) ELSE 0 END as upt,
            CASE WHEN SUM(net_sales_items)>0 THEN SUM(net_sales_amount)/SUM(net_sales_items) ELSE 0 END as asp,
            CASE WHEN SUM(pass_by_traffic)>0 THEN SUM(walk_ins)*1.0/SUM(pass_by_traffic) ELSE NULL END as capture_rate,
            AVG(interaction_rate) as interaction_rate,
            AVG(greeting_rate) as greeting_rate
        FROM daily_store_metrics
        WHERE day BETWEEN '{start}' AND '{end}'
          {closed_filter()}
        """
        cur = con.execute(q).fetchone()
        cols = ["visits","walk_ins","pass_by","transactions","revenue","items","cr","atv","upt","asp","capture_rate","interaction_rate","greeting_rate"]
        current = {c: (float(v) if v is not None else None) for c, v in zip(cols, cur)}

        q_ly = q.replace(f"'{start}'", f"'{start_ly}'").replace(f"'{end}'", f"'{end_ly}'")
        cur_ly = con.execute(q_ly).fetchone()
        ly = {c: (float(v) if v is not None else None) for c, v in zip(cols, cur_ly)}

        yoy = {}
        for c in cols:
            if current[c] and ly[c] and ly[c] != 0:
                if c in ("cr", "atv", "upt", "asp", "capture_rate", "interaction_rate", "greeting_rate"):
                    yoy[c] = current[c] - ly[c]  # absolute diff for rates
                else:
                    yoy[c] = (current[c] - ly[c]) / ly[c]  # pct change
            else:
                yoy[c] = None

        result[label] = {"current": current, "last_year": ly, "yoy_change": yoy}

    # 2. By store type
    by_type = {}
    for stype in ["Boutique", "Counter W Refr.", "Street"]:
        q = f"""
        SELECT
            SUM(visits) as visits,
            SUM(net_sales_transactions) as transactions,
            SUM(net_sales_amount) as revenue,
            CASE WHEN SUM(visits)>0 THEN SUM(net_sales_transactions)*1.0/SUM(visits) ELSE 0 END as cr,
            CASE WHEN SUM(net_sales_transactions)>0 THEN SUM(net_sales_amount)/SUM(net_sales_transactions) ELSE 0 END as atv,
            CASE WHEN SUM(net_sales_transactions)>0 THEN SUM(net_sales_items)*1.0/SUM(net_sales_transactions) ELSE 0 END as upt
        FROM daily_store_metrics
        WHERE day BETWEEN '{current_week_start}' AND '{current_week_end}'
          AND store_type = '{stype}'
          {closed_filter()}
        """
        cur = con.execute(q).fetchone()
        cols2 = ["visits","transactions","revenue","cr","atv","upt"]
        current_vals = {c: (float(v) if v is not None else None) for c, v in zip(cols2, cur)}

        q_ly = q.replace(f"'{current_week_start}'", f"'{cw_start_ly}'").replace(f"'{current_week_end}'", f"'{cw_end_ly}'")
        cur_ly = con.execute(q_ly).fetchone()
        ly_vals = {c: (float(v) if v is not None else None) for c, v in zip(cols2, cur_ly)}

        key = stype.replace(" W Refr.", "").lower()
        by_type[key] = {"current": current_vals, "last_year": ly_vals}
    result["by_type"] = by_type

    # 3. Daily trend (last 30 days)
    q_trend = f"""
    SELECT day::VARCHAR as day,
        SUM(visits) as visits,
        SUM(net_sales_transactions) as transactions,
        SUM(net_sales_amount) as revenue,
        CASE WHEN SUM(visits)>0 THEN SUM(net_sales_transactions)*1.0/SUM(visits) ELSE 0 END as cr,
        CASE WHEN SUM(net_sales_transactions)>0 THEN SUM(net_sales_amount)/SUM(net_sales_transactions) ELSE 0 END as atv
    FROM daily_store_metrics
    WHERE day BETWEEN '{yesterday - timedelta(days=29)}' AND '{yesterday}'
      {closed_filter()}
    GROUP BY day ORDER BY day
    """
    trend = con.execute(q_trend).fetchall()
    result["daily_trend"] = [
        {"day": r[0], "visits": int(r[1]) if r[1] else 0, "transactions": int(r[2]) if r[2] else 0,
         "revenue": float(r[3]) if r[3] else 0, "cr": float(r[4]) if r[4] else 0, "atv": float(r[5]) if r[5] else 0}
        for r in trend
    ]

    # Same period last year trend
    q_trend_ly = f"""
    SELECT day::VARCHAR as day,
        SUM(visits) as visits,
        SUM(net_sales_transactions) as transactions,
        SUM(net_sales_amount) as revenue,
        CASE WHEN SUM(visits)>0 THEN SUM(net_sales_transactions)*1.0/SUM(visits) ELSE 0 END as cr,
        CASE WHEN SUM(net_sales_transactions)>0 THEN SUM(net_sales_amount)/SUM(net_sales_transactions) ELSE 0 END as atv
    FROM daily_store_metrics
    WHERE day BETWEEN '{(yesterday - timedelta(days=29)).replace(year=yesterday.year-1)}' AND '{yesterday_ly}'
      {closed_filter()}
    GROUP BY day ORDER BY day
    """
    trend_ly = con.execute(q_trend_ly).fetchall()
    result["daily_trend_ly"] = [
        {"day": r[0], "visits": int(r[1]) if r[1] else 0, "transactions": int(r[2]) if r[2] else 0,
         "revenue": float(r[3]) if r[3] else 0, "cr": float(r[4]) if r[4] else 0, "atv": float(r[5]) if r[5] else 0}
        for r in trend_ly
    ]

    # 4. Store rankings (this week)
    q_rank = f"""
    SELECT store_name, store_type, tier,
        SUM(visits) as visits,
        SUM(net_sales_transactions) as transactions,
        SUM(net_sales_amount) as revenue,
        CASE WHEN SUM(visits)>0 THEN SUM(net_sales_transactions)*1.0/SUM(visits) ELSE 0 END as cr,
        CASE WHEN SUM(net_sales_transactions)>0 THEN SUM(net_sales_amount)/SUM(net_sales_transactions) ELSE 0 END as atv,
        CASE WHEN SUM(net_sales_transactions)>0 THEN SUM(net_sales_items)*1.0/SUM(net_sales_transactions) ELSE 0 END as upt,
        AVG(interaction_rate) as interaction_rate,
        AVG(greeting_rate) as greeting_rate
    FROM daily_store_metrics
    WHERE day BETWEEN '{current_week_start}' AND '{current_week_end}'
      {closed_filter()}
    GROUP BY store_name, store_type, tier
    ORDER BY revenue DESC
    """
    stores = con.execute(q_rank).fetchall()
    store_cols = ["store_name","store_type","tier","visits","transactions","revenue","cr","atv","upt","interaction_rate","greeting_rate"]
    result["store_rankings"] = [
        {c: (float(v) if isinstance(v, (int, float)) and v is not None else v) for c, v in zip(store_cols, row)}
        for row in stores
    ]

    # 5. Store rankings last year same week (for YoY per store)
    q_rank_ly = q_rank.replace(f"'{current_week_start}'", f"'{cw_start_ly}'").replace(f"'{current_week_end}'", f"'{cw_end_ly}'")
    stores_ly = con.execute(q_rank_ly).fetchall()
    result["store_rankings_ly"] = [
        {c: (float(v) if isinstance(v, (int, float)) and v is not None else v) for c, v in zip(store_cols, row)}
        for row in stores_ly
    ]

    # 6. Weekly trend (last 12 weeks)
    q_weekly = f"""
    SELECT DATE_TRUNC('week', day)::DATE::VARCHAR as week_start,
        SUM(visits) as visits,
        SUM(net_sales_transactions) as transactions,
        SUM(net_sales_amount) as revenue,
        CASE WHEN SUM(visits)>0 THEN SUM(net_sales_transactions)*1.0/SUM(visits) ELSE 0 END as cr,
        CASE WHEN SUM(net_sales_transactions)>0 THEN SUM(net_sales_amount)/SUM(net_sales_transactions) ELSE 0 END as atv
    FROM daily_store_metrics
    WHERE day BETWEEN '{yesterday - timedelta(weeks=12)}' AND '{yesterday}'
      {closed_filter()}
    GROUP BY week_start ORDER BY week_start
    """
    weekly = con.execute(q_weekly).fetchall()
    result["weekly_trend"] = [
        {"week": r[0], "visits": int(r[1]) if r[1] else 0, "transactions": int(r[2]) if r[2] else 0,
         "revenue": float(r[3]) if r[3] else 0, "cr": float(r[4]) if r[4] else 0, "atv": float(r[5]) if r[5] else 0}
        for r in weekly
    ]

    # Metadata
    result["meta"] = {
        "generated_at": datetime.now().isoformat(),
        "data_range": f"{con.execute('SELECT MIN(day) FROM daily_store_metrics').fetchone()[0]} to {con.execute('SELECT MAX(day) FROM daily_store_metrics').fetchone()[0]}",
        "total_stores": con.execute(f"SELECT COUNT(DISTINCT store_name) FROM daily_store_metrics WHERE 1=1 {closed_filter()}").fetchone()[0],
        "yesterday": str(yesterday),
        "current_week": f"{current_week_start} to {current_week_end}",
        "current_month_start": str(current_month_start),
    }

    con.close()

    with open(OUT_PATH, 'w') as f:
        json.dump(result, f, ensure_ascii=False)
    print(f"Dashboard JSON generated: {OUT_PATH} ({os.path.getsize(OUT_PATH)} bytes)")

if __name__ == "__main__":
    run()
