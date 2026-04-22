#!/usr/bin/env python3
"""Search the web via Firecrawl /v1/search and return structured results."""

import argparse
import json
import os
import sys
import time
import uuid
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

DEFAULT_EXCLUDED = [
    "justdial.com", "practo.com", "99acres.com", "magicbricks.com",
    "apollohospitals.com", "fortishealthcare.com", "manipalhospitals.com",
    "maxhealthcare.in", "medanta.org", "narayanahealth.org",
    "sulekha.com", "indiamart.com", "yellowpages.in",
]

FIRECRAWL_BASE = "https://api.firecrawl.dev"


def get_run_id() -> str:
    current = Path(".tmp/runs/current")
    if current.exists():
        return current.read_text().strip()
    run_id = str(uuid.uuid4())[:8]
    current.parent.mkdir(parents=True, exist_ok=True)
    current.write_text(run_id)
    return run_id


def log(event: str, payload: dict, run_id: str):
    """Append event to run log without depending on log_run.py subprocess."""
    run_dir = Path(f".tmp/runs/{run_id}")
    run_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": time.time(),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "event": event,
        **payload,
    }
    with (run_dir / "events.jsonl").open("a") as f:
        f.write(json.dumps(record) + "\n")


def search(query: str, limit: int, api_key: str) -> list[dict]:
    """Call Firecrawl /v1/search with exponential backoff on 429/503."""
    url = f"{FIRECRAWL_BASE}/v1/search"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {"query": query, "limit": limit}

    for attempt in range(3):
        resp = requests.post(url, headers=headers, json=body, timeout=30)
        if resp.status_code in (429, 503):
            wait = 2 ** attempt * 2
            print(f"Rate limited ({resp.status_code}), retrying in {wait}s…", file=sys.stderr)
            time.sleep(wait)
            continue
        if not resp.ok:
            print(f"ERROR: Firecrawl search returned {resp.status_code}: {resp.text}", file=sys.stderr)
            sys.exit(1)
        data = resp.json()
        return data.get("data", data.get("results", []))

    print("ERROR: Firecrawl search failed after 3 retries", file=sys.stderr)
    sys.exit(1)


def filter_results(results: list[dict], excluded: list[str]) -> list[dict]:
    kept = []
    for r in results:
        url = r.get("url", "")
        if any(ex in url for ex in excluded):
            continue
        kept.append(r)
    return kept


def main():
    parser = argparse.ArgumentParser(description="Search web via Firecrawl")
    parser.add_argument("--query", required=True, help="Search query string")
    parser.add_argument("--geo", help="Geography hint (appended to query if not already present)")
    parser.add_argument("--limit", type=int, default=10, help="Max results (default 10)")
    parser.add_argument("--exclude-domains", help="Comma-separated domains to exclude")
    parser.add_argument("--run-id", help="Run ID (reads .tmp/runs/current if omitted)")
    parser.add_argument("--output", help="Write JSON results to this path (optional)")
    args = parser.parse_args()

    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        print("ERROR: FIRECRAWL_API_KEY not set in environment or .env", file=sys.stderr)
        sys.exit(1)

    run_id = args.run_id or get_run_id()
    query = args.query
    if args.geo and args.geo.lower() not in query.lower():
        query = f"{query} {args.geo}"

    excluded = DEFAULT_EXCLUDED[:]
    if args.exclude_domains:
        excluded.extend(d.strip() for d in args.exclude_domains.split(","))

    log("search_started", {"query": query, "limit": args.limit}, run_id)

    try:
        raw = search(query, args.limit, api_key)
        results = filter_results(raw, excluded)

        output = [
            {
                "url": r.get("url", ""),
                "title": r.get("title", ""),
                "description": r.get("description", ""),
                "rank": i + 1,
            }
            for i, r in enumerate(results)
        ]

        log("search_completed", {"query": query, "results_returned": len(output)}, run_id)

        # Write to .tmp if output path specified or build default
        out_path = args.output
        if not out_path:
            slug = query[:40].replace(" ", "_").replace("/", "-")
            out_path = f".tmp/runs/{run_id}/search_{slug}.json"
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_text(json.dumps(output, indent=2))

        # Also print to stdout for agent consumption
        print(json.dumps(output, indent=2))

    except Exception as e:
        log("search_failed", {"query": query, "error": str(e)}, run_id)
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
