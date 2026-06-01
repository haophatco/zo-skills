#!/usr/bin/env python3
"""
HPG Places Scanner - Quét data B2B từ Google Places API (New)

Usage:
    python3 scan_places.py --query "cửa hàng kính mắt" --city "Ho Chi Minh City" --output out.xlsx
    python3 scan_places.py --query "shop kính" --lat 10.77 --lng 106.70 --radius 5000 --output out.xlsx
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from openpyxl import Workbook

API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY")
TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
NEARBY_SEARCH_URL = "https://places.googleapis.com/v1/places:searchNearby"

FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.internationalPhoneNumber",
    "places.nationalPhoneNumber",
    "places.websiteUri",
    "places.rating",
    "places.userRatingCount",
    "places.businessStatus",
    "places.location",
    "places.types",
    "places.regularOpeningHours",
    "places.priceLevel",
    "nextPageToken",
])


def text_search(query: str, city: str = None, max_pages: int = 3) -> list[dict]:
    """Search places by text query, optionally biased by city."""
    if not API_KEY:
        sys.exit("ERROR: GOOGLE_PLACES_API_KEY not set in environment")

    full_query = f"{query} {city}" if city else query
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": FIELD_MASK,
    }
    payload = {"textQuery": full_query, "languageCode": "vi", "regionCode": "VN"}

    all_places = []
    page_token = None

    for page in range(max_pages):
        if page_token:
            payload["pageToken"] = page_token
            time.sleep(2)

        resp = requests.post(TEXT_SEARCH_URL, headers=headers, json=payload, timeout=30)
        if resp.status_code != 200:
            print(f"ERROR: {resp.status_code} - {resp.text}", file=sys.stderr)
            break

        data = resp.json()
        places = data.get("places", [])
        all_places.extend(places)
        print(f"  Page {page + 1}: +{len(places)} places (total {len(all_places)})")

        page_token = data.get("nextPageToken")
        if not page_token:
            break

    return all_places


def nearby_search(query: str, lat: float, lng: float, radius: int = 5000) -> list[dict]:
    """Search places near coordinates."""
    if not API_KEY:
        sys.exit("ERROR: GOOGLE_PLACES_API_KEY not set in environment")

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": FIELD_MASK,
    }
    payload = {
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": float(radius),
            }
        },
        "languageCode": "vi",
        "regionCode": "VN",
        "maxResultCount": 20,
    }

    resp = requests.post(NEARBY_SEARCH_URL, headers=headers, json=payload, timeout=30)
    if resp.status_code != 200:
        print(f"ERROR: {resp.status_code} - {resp.text}", file=sys.stderr)
        return []

    return resp.json().get("places", [])


def flatten_place(p: dict) -> dict:
    """Flatten nested Place object into a flat row."""
    loc = p.get("location", {})
    opening = p.get("regularOpeningHours", {})
    opening_str = " | ".join(opening.get("weekdayDescriptions", []))

    return {
        "place_id": p.get("id", ""),
        "name": (p.get("displayName") or {}).get("text", ""),
        "address": p.get("formattedAddress", ""),
        "phone": p.get("nationalPhoneNumber") or p.get("internationalPhoneNumber", ""),
        "website": p.get("websiteUri", ""),
        "email": "",
        "rating": p.get("rating", ""),
        "user_ratings_total": p.get("userRatingCount", ""),
        "business_status": p.get("businessStatus", ""),
        "lat": loc.get("latitude", ""),
        "lng": loc.get("longitude", ""),
        "types": ", ".join(p.get("types", [])),
        "price_level": p.get("priceLevel", ""),
        "opening_hours": opening_str,
        "scanned_at": datetime.now().isoformat(timespec="seconds"),
    }


def save_xlsx(rows: list[dict], output_path: str):
    """Save rows to Excel file."""
    if not rows:
        print("No rows to save")
        return

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = "Places"

    headers = list(rows[0].keys())
    ws.append(headers)
    for row in rows:
        ws.append([row.get(h, "") for h in headers])

    for i, h in enumerate(headers, 1):
        ws.column_dimensions[chr(64 + i) if i <= 26 else f"A{chr(64 + i - 26)}"].width = max(15, len(h) + 2)

    wb.save(output_path)
    print(f"Saved {len(rows)} rows to {output_path}")


def main():
    ap = argparse.ArgumentParser(description="Quét data B2B từ Google Places API")
    ap.add_argument("--query", required=True, help="Từ khóa tìm kiếm (vd: 'cửa hàng kính mắt')")
    ap.add_argument("--city", help="Thành phố để bias kết quả (vd: 'Ho Chi Minh City')")
    ap.add_argument("--lat", type=float, help="Vĩ độ (dùng cho nearby search)")
    ap.add_argument("--lng", type=float, help="Kinh độ (dùng cho nearby search)")
    ap.add_argument("--radius", type=int, default=5000, help="Bán kính (m) cho nearby search")
    ap.add_argument("--max-pages", type=int, default=3, help="Số trang tối đa (mỗi trang ~20 results)")
    ap.add_argument("--output", required=True, help="Đường dẫn file Excel output")
    ap.add_argument("--json-dump", help="Dump raw JSON response để debug")
    args = ap.parse_args()

    if args.lat is not None and args.lng is not None:
        print(f"Nearby search: '{args.query}' tại ({args.lat}, {args.lng}) bán kính {args.radius}m")
        places = nearby_search(args.query, args.lat, args.lng, args.radius)
    else:
        print(f"Text search: '{args.query}'" + (f" tại {args.city}" if args.city else ""))
        places = text_search(args.query, args.city, args.max_pages)

    print(f"\nTotal places found: {len(places)}")

    if args.json_dump:
        Path(args.json_dump).write_text(json.dumps(places, ensure_ascii=False, indent=2))
        print(f"Raw JSON dumped to {args.json_dump}")

    rows = [flatten_place(p) for p in places]
    save_xlsx(rows, args.output)


if __name__ == "__main__":
    main()
