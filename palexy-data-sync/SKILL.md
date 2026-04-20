---
name: palexy-data-sync
description: Syncs Mắt Việt store analytics data from Palexy API into DuckDB. Pulls traffic, conversion, sales, interaction, greeting metrics daily. Use when analyzing store performance or when the user asks about Palexy data.
compatibility: Created for Zo Computer
metadata:
  author: hana.zo.computer
---

## Overview
Pulls Mắt Việt (MVG) in-store customer analytics from Palexy API and stores in DuckDB.

## Database
- **Path:** `Data/palexy.duckdb`
- **Table:** `daily_store_metrics` — one row per store per day

### Key columns
| Column | Description |
|--------|-------------|
| store_id, store_code, store_name | Store identifiers |
| store_type | Boutique / Counter W Refr. / Street |
| area_manager | AM name (Loan, Trang, Tiến, Luan, Hiền) |
| tier | PLATINUM / GOLD / SILVER |
| day | Date |
| visits, walk_ins | Traffic |
| conversion_rate | Transactions / Visits |
| net_sales_amount, net_sales_transactions | Revenue & transactions |
| atv, upt, asp | Avg transaction value, units per txn, avg selling price |
| interaction_rate, greeting_rate, on_time_greeting_rate | Service quality |
| average_dwell_time | Seconds in store |
| pass_by_traffic, capture_rate | Street/mall foot traffic (not available for Street stores) |
| group_rate, average_group_size | Group shopping metrics |
| average_visitors_per_staff | Staffing efficiency |

### Store classification
- **Types:** Boutique (in-mall), Counter W Refr. (counter in department store), Street (street-front)
- **Tiers:** Platinum, Gold, Silver
- **Note:** Street stores do NOT have pass_by_traffic or capture_rate data

## Scripts

```bash
# Full historical sync
python3 Skills/palexy-data-sync/scripts/palexy_sync.py full 2025-01-01 2026-04-12

# Daily sync (yesterday)
python3 Skills/palexy-data-sync/scripts/palexy_sync.py daily

# Sync specific date
python3 Skills/palexy-data-sync/scripts/palexy_sync.py daily 2026-04-13

# Check DB status
python3 Skills/palexy-data-sync/scripts/palexy_sync.py status
```

## Environment
- Requires `Palexy_API_KEY` in Zo secrets
- API base: https://ica.palexy.com
- Palexy updates MV sales data at ~7:30am VN time daily
- Daily sync scheduled at 8:00am VN time (1:00 UTC)
