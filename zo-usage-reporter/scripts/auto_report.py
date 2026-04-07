#!/usr/bin/env python3.12
"""AI Usage Auto-Reporter — collects ccusage data and POSTs to leaderboard.

Runs on any Zo Computer. Collects local Claude Code usage logs via ccusage
and sends them to the central leaderboard API.

Usage:
    python3.12 auto_report.py --account mkt           # Report for MKT team
    python3.12 auto_report.py --account cs --days 7    # Last 7 days only
    python3.12 auto_report.py --account ecom --dry-run # Preview without sending
"""

import argparse
import json
import platform
import socket
import subprocess
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

API_URL = "https://phatology.zo.space/api/usage-report"
VALID_ACCOUNTS = {"cs": "CS Team", "mkt": "MKT Team", "ecom": "ECOM Team", "edward": "Edward (Personal)", "thanh": "Sếp Thành"}
VN_TZ = timezone(timedelta(hours=7))


def run_ccusage(days=0):
    """Run ccusage and return parsed JSON daily data."""
    cmd = ["npx", "-y", "ccusage@latest", "daily", "--json", "--timezone", "Asia/Ho_Chi_Minh"]
    if days > 0:
        since = (datetime.now(VN_TZ) - timedelta(days=days)).strftime("%Y%m%d")
        cmd.extend(["--since", since])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            print(f"ERROR: ccusage failed: {result.stderr[:500]}")
            return None
        data = json.loads(result.stdout)
        return data.get("daily", [])
    except subprocess.TimeoutExpired:
        print("ERROR: ccusage timed out (300s)")
        return None
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"ERROR: {e}")
        return None


def post_to_api(account_id, daily, hostname):
    """POST usage data to the central leaderboard API."""
    payload = json.dumps({
        "account_id": account_id,
        "daily": daily,
        "source": "ccusage",
        "hostname": hostname,
    }).encode("utf-8")

    req = urllib.request.Request(
        API_URL, data=payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "ZoUsageReporter/2.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:300]
        print(f"ERROR: API returned {e.code}: {body}")
        return None
    except urllib.error.URLError as e:
        print(f"ERROR: Cannot connect to API: {e.reason}")
        return None


def main():
    parser = argparse.ArgumentParser(description="AI Usage Auto-Reporter")
    parser.add_argument("--account", required=True, choices=list(VALID_ACCOUNTS.keys()),
                        help="Account ID (cs, mkt, ecom, edward)")
    parser.add_argument("--days", type=int, default=0, help="Only last N days (0 = all)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without sending")
    args = parser.parse_args()

    account_id = args.account
    account_label = VALID_ACCOUNTS[account_id]
    hostname = f"{socket.gethostname()}-{platform.system()}"
    now_vn = datetime.now(VN_TZ).strftime("%Y-%m-%d %H:%M")

    print(f"[{now_vn}] Collecting usage for '{account_id}' ({account_label})")

    daily = run_ccusage(args.days)
    if daily is None:
        sys.exit(1)

    # Filter out zero-token days
    daily = [d for d in daily if d.get("totalTokens", 0) > 0]

    if not daily:
        print("No usage data found.")
        sys.exit(0)

    total_tokens = sum(d.get("totalTokens", 0) for d in daily)
    total_cost = sum(d.get("totalCost", 0) for d in daily)
    dates = [d["date"] for d in daily]

    print(f"  Days: {len(daily)} ({dates[0]} to {dates[-1]})")
    print(f"  Tokens: {total_tokens:,}")
    print(f"  Cost: ${total_cost:,.2f}")

    if args.dry_run:
        print("\n[DRY RUN] Would send to API. No changes made.")
        return

    result = post_to_api(account_id, daily, hostname)
    if result and result.get("ok"):
        print(f"\nSent: {result.get('inserted', 0)} new, {result.get('updated', 0)} updated")
        print(f"Account total: {result.get('account_total_days', '?')} days, ${result.get('account_total_cost', '?'):,.2f}")
    else:
        print("\nFailed to send data.")
        sys.exit(1)


if __name__ == "__main__":
    main()
