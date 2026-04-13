#!/usr/bin/env python3
"""
Zo Memory Service - powered by mem0
Stores and retrieves conversation memories for persistent context across Zo sessions.

Usage:
  python3 memory.py add --user hana --text "some conversation or fact"
  python3 memory.py search --user hana --query "what do I know about X"
  python3 memory.py list --user hana
  python3 memory.py delete --id <memory_id>
  python3 memory.py stats --user hana
"""

import argparse
import json
import sys
import os

from mem0 import Memory

MEMORY_DIR = os.path.expanduser("~/.zo-memory")
os.makedirs(MEMORY_DIR, exist_ok=True)

def get_memory():
    config = {
        "llm": {
            "provider": "openai",
            "config": {
                "model": "gpt-4.1-mini",
                "api_key": os.environ.get("OPENAI_API_KEY"),
                "temperature": 0.1,
                "max_tokens": 2000,
            }
        },
        "embedder": {
            "provider": "openai",
            "config": {
                "model": "text-embedding-3-small",
                "api_key": os.environ.get("OPENAI_API_KEY"),
            }
        },
        "vector_store": {
            "provider": "chroma",
            "config": {
                "collection_name": "zo_memories_v2",
                "path": os.path.join(MEMORY_DIR, "chroma_db_v2"),
            }
        },
        "history_db_path": os.path.join(MEMORY_DIR, "history_v2.db"),
    }
    return Memory.from_config(config)


def cmd_add(args):
    m = get_memory()
    result = m.add(args.text, user_id=args.user)
    print(json.dumps(result, indent=2, default=str))


def cmd_search(args):
    m = get_memory()
    results = m.search(args.query, user_id=args.user, limit=args.limit)
    if hasattr(results, 'results'):
        entries = results.results
    elif isinstance(results, dict) and 'results' in results:
        entries = results['results']
    elif isinstance(results, list):
        entries = results
    else:
        entries = []

    for entry in entries:
        if isinstance(entry, dict):
            print(f"[{entry.get('id', '?')[:8]}] (score: {entry.get('score', '?')}) {entry.get('memory', entry.get('text', ''))}")
        else:
            print(entry)

    if not entries:
        print("No relevant memories found.")


def cmd_list(args):
    m = get_memory()
    results = m.get_all(user_id=args.user)
    if hasattr(results, 'results'):
        entries = results.results
    elif isinstance(results, dict) and 'results' in results:
        entries = results['results']
    elif isinstance(results, list):
        entries = results
    else:
        entries = []

    print(f"Total memories: {len(entries)}")
    for entry in entries:
        if isinstance(entry, dict):
            mid = entry.get('id', '?')[:8]
            text = entry.get('memory', entry.get('text', ''))
            print(f"  [{mid}] {text}")
        else:
            print(f"  {entry}")


def cmd_delete(args):
    m = get_memory()
    m.delete(args.id)
    print(f"Deleted memory: {args.id}")


def cmd_stats(args):
    m = get_memory()
    results = m.get_all(user_id=args.user)
    if hasattr(results, 'results'):
        entries = results.results
    elif isinstance(results, dict) and 'results' in results:
        entries = results['results']
    elif isinstance(results, list):
        entries = results
    else:
        entries = []
    print(f"User: {args.user}")
    print(f"Total memories stored: {len(entries)}")
    db_path = os.path.join(MEMORY_DIR, "chroma_db")
    if os.path.exists(db_path):
        total = sum(
            os.path.getsize(os.path.join(dp, f))
            for dp, _, fns in os.walk(db_path)
            for f in fns
        )
        print(f"Database size: {total / 1024 / 1024:.1f} MB")


def main():
    parser = argparse.ArgumentParser(description="Zo Memory - persistent conversation memory")
    sub = parser.add_subparsers(dest="command")

    p_add = sub.add_parser("add", help="Add a memory")
    p_add.add_argument("--user", default="hana")
    p_add.add_argument("--text", required=True)

    p_search = sub.add_parser("search", help="Search memories")
    p_search.add_argument("--user", default="hana")
    p_search.add_argument("--query", required=True)
    p_search.add_argument("--limit", type=int, default=5)

    p_list = sub.add_parser("list", help="List all memories")
    p_list.add_argument("--user", default="hana")

    p_del = sub.add_parser("delete", help="Delete a memory")
    p_del.add_argument("--id", required=True)

    p_stats = sub.add_parser("stats", help="Show memory stats")
    p_stats.add_argument("--user", default="hana")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    {"add": cmd_add, "search": cmd_search, "list": cmd_list, "delete": cmd_delete, "stats": cmd_stats}[args.command](args)


if __name__ == "__main__":
    main()
