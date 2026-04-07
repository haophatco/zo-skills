#!/usr/bin/env python3.12
"""One-click installer for AI Usage Auto-Reporter.

Run on any team Zo Computer to:
1. Test ccusage works
2. Do a test report to the API
3. Print instructions for creating a scheduled agent

Usage:
    python3.12 install.py --account mkt
    python3.12 install.py --account cs
    python3.12 install.py --account ecom
"""

import argparse
import json
import subprocess
import sys

VALID_ACCOUNTS = {"cs": "CS Team", "mkt": "MKT Team", "ecom": "ECOM Team", "edward": "Edward (Personal)", "thanh": "Sếp Thành"}


def check_ccusage():
    """Verify ccusage can run."""
    print("Step 1/3: Checking ccusage...")
    try:
        result = subprocess.run(
            ["npx", "-y", "ccusage@latest", "--version"],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"  OK — ccusage {version}")
            return True
        else:
            print(f"  FAIL — {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"  FAIL — {e}")
        return False


def test_collect():
    """Test that ccusage can read local logs."""
    print("\nStep 2/3: Testing data collection...")
    try:
        result = subprocess.run(
            ["npx", "-y", "ccusage@latest", "daily", "--json", "--since",
             __import__("datetime").datetime.now().strftime("%Y%m%d")],
            capture_output=True, text=True, timeout=300
        )
        if result.returncode != 0:
            print(f"  FAIL — ccusage error: {result.stderr[:200]}")
            return False
        data = json.loads(result.stdout)
        daily = data.get("daily", [])
        if daily:
            tokens = sum(d.get("totalTokens", 0) for d in daily)
            print(f"  OK — Found {len(daily)} day(s), {tokens:,} tokens")
        else:
            print("  OK — No usage data for today yet (normal if you haven't used Claude Code today)")
        return True
    except Exception as e:
        print(f"  FAIL — {e}")
        return False


def test_api(account_id):
    """Test API connectivity with a dry ping."""
    import urllib.request
    import urllib.error

    print("\nStep 3/3: Testing API connectivity...")
    try:
        req = urllib.request.Request(
            "https://phatology.zo.space/api/usage-report",
            method="GET",
            headers={"Accept": "application/json", "User-Agent": "ZoUsageReporter/2.0"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("ok"):
                accounts = data.get("accounts", [])
                print(f"  OK — API reachable, {len(accounts)} accounts on leaderboard")
                return True
    except urllib.error.URLError as e:
        print(f"  FAIL — Cannot reach API: {e.reason}")
    except Exception as e:
        print(f"  FAIL — {e}")
    return False


def main():
    parser = argparse.ArgumentParser(description="Install AI Usage Auto-Reporter")
    parser.add_argument("--account", required=True, choices=list(VALID_ACCOUNTS.keys()),
                        help="Your team account ID")
    args = parser.parse_args()

    account_id = args.account
    account_label = VALID_ACCOUNTS[account_id]

    print("=" * 55)
    print("  AI Usage Auto-Reporter — Installation")
    print(f"  Account: {account_id} ({account_label})")
    print("=" * 55)
    print()

    ok1 = check_ccusage()
    ok2 = test_collect()
    ok3 = test_api(account_id)

    print()
    if ok1 and ok2 and ok3:
        print("=" * 55)
        print("  ALL CHECKS PASSED")
        print("=" * 55)
        print()
        print("To set up daily auto-reporting, tell your Zo:")
        print()
        print(f'  "Create a scheduled agent that runs daily at 1:00 AM')
        print(f'   Vietnam time. It should run this command:')
        print(f'   python3.12 /home/workspace/Skills/zo-usage-reporter/scripts/auto_report.py --account {account_id} --days 3')
        print(f'   Report any errors to me via chat."')
        print()
        print("Or create the agent manually at: /?t=automations")
        print()
        print(f"Leaderboard: https://phatology.zo.space/ai-leaderboard")
    else:
        print("=" * 55)
        print("  SOME CHECKS FAILED — see above for details")
        print("=" * 55)
        print()
        if not ok1:
            print("  Fix: Install Node.js from https://nodejs.org/en/download")
        if not ok2:
            print("  Fix: Make sure Claude Code has been used on this machine")
        if not ok3:
            print("  Fix: Check internet connection")


if __name__ == "__main__":
    main()
