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
    "Boutique - Vincom Times City",
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

    # 7. WEEKLY SUMMARY — this week vs last week & same week LY, growth/decline drivers
    # Already have: this_week (current+ly), last week computed below
    q_lw = f"""
    SELECT
        SUM(visits) as visits,
        SUM(net_sales_transactions) as transactions,
        SUM(net_sales_amount) as revenue,
        CASE WHEN SUM(visits)>0 THEN SUM(net_sales_transactions)*1.0/SUM(visits) ELSE 0 END as cr,
        CASE WHEN SUM(net_sales_transactions)>0 THEN SUM(net_sales_amount)/SUM(net_sales_transactions) ELSE 0 END as atv
    FROM daily_store_metrics
    WHERE day BETWEEN '{last_week_start}' AND '{last_week_end}'
      {closed_filter()}
    """
    lw = con.execute(q_lw).fetchone()
    last_week_vals = {
        "visits": int(lw[0] or 0), "transactions": int(lw[1] or 0),
        "revenue": float(lw[2] or 0), "cr": float(lw[3] or 0), "atv": float(lw[4] or 0),
    }

    # Per-store WoW revenue change to identify growth/decline drivers
    q_drivers = f"""
    WITH cw AS (
        SELECT store_name, store_type, tier,
            SUM(net_sales_amount) as revenue,
            SUM(visits) as visits,
            SUM(net_sales_transactions) as transactions
        FROM daily_store_metrics
        WHERE day BETWEEN '{current_week_start}' AND '{current_week_end}'
          {closed_filter()}
        GROUP BY store_name, store_type, tier
    ),
    lw AS (
        SELECT store_name,
            SUM(net_sales_amount) as revenue,
            SUM(visits) as visits,
            SUM(net_sales_transactions) as transactions
        FROM daily_store_metrics
        WHERE day BETWEEN '{last_week_start}' AND '{last_week_end}'
          {closed_filter()}
        GROUP BY store_name
    )
    SELECT cw.store_name, cw.store_type, cw.tier,
        cw.revenue as cw_rev, COALESCE(lw.revenue,0) as lw_rev,
        cw.revenue - COALESCE(lw.revenue,0) as rev_delta,
        cw.visits as cw_visits, COALESCE(lw.visits,0) as lw_visits,
        cw.transactions as cw_tx, COALESCE(lw.transactions,0) as lw_tx
    FROM cw LEFT JOIN lw ON cw.store_name = lw.store_name
    ORDER BY rev_delta DESC
    """
    drivers = con.execute(q_drivers).fetchall()
    growth_drivers = []
    decline_drivers = []
    for r in drivers:
        item = {
            "store_name": r[0], "store_type": r[1], "tier": r[2],
            "cw_revenue": float(r[3] or 0), "lw_revenue": float(r[4] or 0),
            "revenue_delta": float(r[5] or 0),
            "cw_visits": int(r[6] or 0), "lw_visits": int(r[7] or 0),
            "cw_transactions": int(r[8] or 0), "lw_transactions": int(r[9] or 0),
        }
        if item["revenue_delta"] > 0:
            growth_drivers.append(item)
        elif item["revenue_delta"] < 0:
            decline_drivers.append(item)
    growth_drivers.sort(key=lambda x: x["revenue_delta"], reverse=True)
    decline_drivers.sort(key=lambda x: x["revenue_delta"])

    result["weekly_summary"] = {
        "current_week": {"start": str(current_week_start), "end": str(current_week_end)},
        "last_week": {"start": str(last_week_start), "end": str(last_week_end)},
        "last_week_vals": last_week_vals,
        "top_growth": growth_drivers[:5],
        "top_decline": decline_drivers[:5],
        "growth_count": len(growth_drivers),
        "decline_count": len(decline_drivers),
    }

    # 8. TOP PERFORMERS — top 5 stores this week, with KPI comparison vs same-type avg
    q_type_avg = f"""
    SELECT store_type,
        AVG(cr_per_store) as avg_cr,
        AVG(atv_per_store) as avg_atv,
        AVG(upt_per_store) as avg_upt
    FROM (
        SELECT store_name, store_type,
            CASE WHEN SUM(visits)>0 THEN SUM(net_sales_transactions)*1.0/SUM(visits) ELSE 0 END as cr_per_store,
            CASE WHEN SUM(net_sales_transactions)>0 THEN SUM(net_sales_amount)/SUM(net_sales_transactions) ELSE 0 END as atv_per_store,
            CASE WHEN SUM(net_sales_transactions)>0 THEN SUM(net_sales_items)*1.0/SUM(net_sales_transactions) ELSE 0 END as upt_per_store
        FROM daily_store_metrics
        WHERE day BETWEEN '{current_week_start}' AND '{current_week_end}'
          {closed_filter()}
        GROUP BY store_name, store_type
    )
    GROUP BY store_type
    """
    type_avg = {r[0]: {"cr": float(r[1] or 0), "atv": float(r[2] or 0), "upt": float(r[3] or 0)}
                for r in con.execute(q_type_avg).fetchall()}

    # Top 5 by revenue
    top5 = result["store_rankings"][:5]
    top_performers = []
    for s in top5:
        ta = type_avg.get(s["store_type"], {"cr": 0, "atv": 0, "upt": 0})
        reasons = []
        if s["cr"] and ta["cr"] and s["cr"] > ta["cr"] * 1.05:
            reasons.append(f"CR {s['cr']*100:.1f}% vượt trung bình {s['store_type']} ({ta['cr']*100:.1f}%) → đội ngũ chốt sale tốt")
        if s["atv"] and ta["atv"] and s["atv"] > ta["atv"] * 1.05:
            reasons.append(f"ATV {s['atv']/1000:.0f}K vượt trung bình {ta['atv']/1000:.0f}K → up-sell/cross-sell hiệu quả")
        if s["upt"] and ta["upt"] and s["upt"] > ta["upt"] * 1.05:
            reasons.append(f"UPT {s['upt']:.2f} vượt trung bình {ta['upt']:.2f} → bán kèm tốt")
        if s.get("greeting_rate") and s["greeting_rate"] > 0.7:
            reasons.append(f"Greeting rate {s['greeting_rate']*100:.0f}% — đón khách chuẩn")
        if s.get("interaction_rate") and s["interaction_rate"] > 0.5:
            reasons.append(f"Interaction rate {s['interaction_rate']*100:.0f}% cao — NV chủ động")
        if not reasons:
            reasons.append(f"Traffic lớn ({int(s['visits']):,} visits) là động lực doanh thu chính")
        top_performers.append({**s, "reasons": reasons, "type_avg": ta})
    result["top_performers"] = top_performers

    # 9. WEAK STORES — bottom 5 by revenue (with at least some traffic), with diagnosis
    weak_candidates = [s for s in result["store_rankings"] if s["visits"] and s["visits"] > 50]
    weak_candidates.sort(key=lambda x: x["revenue"] or 0)
    weak5 = weak_candidates[:5]
    weak_stores = []
    for s in weak5:
        ta = type_avg.get(s["store_type"], {"cr": 0, "atv": 0, "upt": 0})
        issues = []
        actions = []
        if s["cr"] and ta["cr"] and s["cr"] < ta["cr"] * 0.85:
            issues.append(f"CR {s['cr']*100:.1f}% thấp hơn trung bình {s['store_type']} ({ta['cr']*100:.1f}%)")
            actions.append("Đào tạo lại kỹ năng tư vấn & chốt sale; review camera 5 case khách rời mà không mua")
        if s["atv"] and ta["atv"] and s["atv"] < ta["atv"] * 0.85:
            issues.append(f"ATV {s['atv']/1000:.0f}K thấp hơn trung bình {ta['atv']/1000:.0f}K")
            actions.append("Push các SKU cao cấp & combo gọng+tròng; coaching up-sell")
        if s["upt"] and ta["upt"] and s["upt"] < ta["upt"] * 0.85:
            issues.append(f"UPT {s['upt']:.2f} thấp hơn trung bình {ta['upt']:.2f}")
            actions.append("Bán kèm phụ kiện (hộp/khăn/dung dịch lau), bundle 2nd pair")
        if s.get("greeting_rate") and s["greeting_rate"] < 0.5:
            issues.append(f"Greeting rate {s['greeting_rate']*100:.0f}% thấp")
            actions.append("Yêu cầu chào khách trong 10s; check daily")
        if s.get("interaction_rate") and s["interaction_rate"] < 0.3:
            issues.append(f"Interaction rate {s['interaction_rate']*100:.0f}% thấp — NV thụ động")
            actions.append("KPI tương tác tối thiểu 50%; đứng đúng vị trí đón khách")
        if not issues:
            issues.append(f"Traffic thấp ({int(s['visits']):,} visits) — vấn đề từ vị trí/marketing")
            actions.append("Tăng activation tại điểm; chạy ads local; review hiệu quả mặt bằng")
        weak_stores.append({**s, "issues": issues, "actions": actions, "type_avg": ta})
    result["weak_stores"] = weak_stores

    # 10. NEXT-WEEK KPIs — targets per store-type based on type avg + 5% lift
    next_week_kpis = {}
    for stype, ta in type_avg.items():
        next_week_kpis[stype] = {
            "cr_target": ta["cr"] * 1.05 if ta["cr"] else 0,
            "atv_target": ta["atv"] * 1.03 if ta["atv"] else 0,
            "upt_target": ta["upt"] * 1.03 if ta["upt"] else 0,
            "current_avg": ta,
        }
    result["next_week_kpis"] = next_week_kpis

    # 11. TOP 5 NEXT-WEEK FOCUS — decision table: stores with highest revenue uplift potential
    # uplift = visits * (type_avg_cr - store_cr) * type_avg_atv  (if positive)
    focus_candidates = []
    for s in result["store_rankings"]:
        if not s["visits"] or s["visits"] < 30:
            continue
        ta = type_avg.get(s["store_type"], {"cr": 0, "atv": 0, "upt": 0})
        cr_gap = (ta["cr"] or 0) - (s["cr"] or 0)
        atv_gap = (ta["atv"] or 0) - (s["atv"] or 0)
        # potential additional revenue if CR closes to type average
        cr_uplift = max(0, cr_gap) * s["visits"] * (s["atv"] or ta["atv"] or 0)
        # potential additional revenue if ATV closes to type average
        atv_uplift = max(0, atv_gap) * (s["transactions"] or 0)
        total_uplift = cr_uplift + atv_uplift
        if total_uplift > 0:
            primary_lever = "CR" if cr_uplift >= atv_uplift else "ATV"
            focus_candidates.append({
                "store_name": s["store_name"],
                "store_type": s["store_type"],
                "tier": s["tier"],
                "current_revenue": s["revenue"],
                "current_cr": s["cr"],
                "current_atv": s["atv"],
                "type_avg_cr": ta["cr"],
                "type_avg_atv": ta["atv"],
                "uplift_potential": total_uplift,
                "primary_lever": primary_lever,
                "action": (
                    f"Đóng gap CR ({(s['cr'] or 0)*100:.1f}% → {(ta['cr'] or 0)*100:.1f}%) — coaching chốt sale"
                    if primary_lever == "CR" else
                    f"Đóng gap ATV ({(s['atv'] or 0)/1000:.0f}K → {(ta['atv'] or 0)/1000:.0f}K) — push cao cấp/combo"
                ),
            })
    focus_candidates.sort(key=lambda x: x["uplift_potential"], reverse=True)
    result["top5_next_week"] = focus_candidates[:5]

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
