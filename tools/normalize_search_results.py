#!/usr/bin/env python3
"""
Normalize search results from any connector (WebSearch, Tavily, Firecrawl, raw)
to the canonical [{url, title, description, rank}] schema used by the Discoverer.

Usage:
  python tools/normalize_search_results.py --input results.json
  echo '<json>' | python tools/normalize_search_results.py
  python tools/normalize_search_results.py --input results.json --output discovered.json
"""

import argparse
import json
import sys
from pathlib import Path


def detect_format(data) -> str:
    """Detect input format from data shape."""
    if isinstance(data, list):
        if not data:
            return "empty"
        first = data[0]
        if isinstance(first, dict):
            # Already in canonical form if it has rank field
            if "rank" in first and "url" in first:
                return "canonical"
            return "raw_list"
    if isinstance(data, dict):
        # Tavily: {"results": [...], "query": "..."}
        if "results" in data and isinstance(data["results"], list):
            results = data["results"]
            if results and "score" in results[0]:
                return "tavily"
            return "nested_results"
        # WebFetch single result: {"url": "...", "content": "..."}
        if "url" in data and "content" in data:
            return "webfetch_single"
    return "unknown"


def normalize_item(item: dict, rank: int) -> dict:
    """Map any result dict to the canonical schema."""
    url = (
        item.get("url")
        or item.get("link")
        or item.get("href")
        or ""
    )
    title = (
        item.get("title")
        or item.get("name")
        or ""
    )
    description = (
        item.get("description")
        or item.get("snippet")
        or item.get("content")
        or item.get("summary")
        or item.get("extract")
        or ""
    )
    # Truncate long descriptions to 300 chars to match Firecrawl behavior
    if len(description) > 300:
        description = description[:297] + "..."
    return {"url": url, "title": title, "description": description, "rank": rank}


def normalize(data) -> list[dict]:
    fmt = detect_format(data)

    if fmt == "canonical":
        # Already correct format — re-sequence ranks just in case
        return [
            {**item, "rank": i + 1}
            for i, item in enumerate(data)
        ]

    if fmt in ("raw_list", "nested_results"):
        items = data if isinstance(data, list) else data.get("results", [])
        return [normalize_item(item, i + 1) for i, item in enumerate(items) if isinstance(item, dict)]

    if fmt == "tavily":
        # Tavily sorts by score descending — preserve that order
        items = sorted(data["results"], key=lambda r: r.get("score", 0), reverse=True)
        return [normalize_item(item, i + 1) for i, item in enumerate(items)]

    if fmt == "webfetch_single":
        return [normalize_item(data, 1)]

    if fmt == "empty":
        return []

    # Unknown: attempt best-effort list extraction
    print(f"WARNING: Unknown input format — attempting best-effort normalization", file=sys.stderr)
    items = data if isinstance(data, list) else data.get("results", data.get("data", []))
    if isinstance(items, list):
        return [normalize_item(item, i + 1) for i, item in enumerate(items) if isinstance(item, dict)]

    print("ERROR: Cannot normalize input — unrecognized structure", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Normalize search results to canonical schema")
    parser.add_argument("--input", "-i", help="Input JSON file (reads stdin if omitted)")
    parser.add_argument("--output", "-o", help="Write normalized JSON to this file (also prints to stdout)")
    args = parser.parse_args()

    if args.input:
        raw = Path(args.input).read_text()
    else:
        raw = sys.stdin.read()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON input — {e}", file=sys.stderr)
        sys.exit(1)

    results = normalize(data)

    output_json = json.dumps(results, indent=2, ensure_ascii=False)
    print(output_json)

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(output_json)


if __name__ == "__main__":
    main()
