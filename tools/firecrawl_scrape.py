#!/usr/bin/env python3
"""Scrape a single URL via Firecrawl /v1/scrape and return structured output."""

import argparse
import json
import os
import sys
import time
import uuid
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

load_dotenv()

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


def scrape(url: str, timeout: int, api_key: str) -> dict:
    """Call Firecrawl /v1/scrape with retry on 429/503."""
    endpoint = f"{FIRECRAWL_BASE}/v1/scrape"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {
        "url": url,
        "formats": ["markdown", "html", "links"],
        "timeout": timeout * 1000,  # Firecrawl expects ms
    }

    for attempt in range(3):
        resp = requests.post(endpoint, headers=headers, json=body, timeout=timeout + 10)
        if resp.status_code in (429, 503):
            wait = 2 ** attempt * 2
            print(f"Rate limited ({resp.status_code}), retrying in {wait}s…", file=sys.stderr)
            time.sleep(wait)
            continue
        if not resp.ok:
            raise RuntimeError(f"Firecrawl returned {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        return data.get("data", data)

    raise RuntimeError("Firecrawl scrape failed after 3 retries")


def extract_meta(raw: dict) -> dict:
    meta = raw.get("metadata", {})
    return {
        "title": meta.get("title", ""),
        "description": meta.get("description", ""),
        "og_title": meta.get("og:title", ""),
        "og_description": meta.get("og:description", ""),
        "status_code": meta.get("statusCode", 200),
    }


def main():
    parser = argparse.ArgumentParser(description="Scrape a URL via Firecrawl")
    parser.add_argument("--url", required=True, help="URL to scrape")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout in seconds (default 30)")
    parser.add_argument("--output", help="Write JSON to this path (default: .tmp/runs/<id>/scrape_<host>.json)")
    parser.add_argument("--run-id", help="Run ID (reads .tmp/runs/current if omitted)")
    args = parser.parse_args()

    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        print("ERROR: FIRECRAWL_API_KEY not set in environment or .env", file=sys.stderr)
        sys.exit(1)

    run_id = args.run_id or get_run_id()
    hostname = urlparse(args.url).netloc.replace("www.", "")

    log("scrape_started", {"url": args.url}, run_id)

    try:
        raw = scrape(args.url, args.timeout, api_key)

        html = raw.get("html", "")
        result = {
            "url": args.url,
            "markdown": raw.get("markdown", ""),
            "html_excerpt": html[:10240] if html else "",
            "links": raw.get("links", []),
            "meta": extract_meta(raw),
        }

        log("scrape_completed", {"url": args.url, "markdown_len": len(result["markdown"])}, run_id)

        out_path = args.output or f".tmp/runs/{run_id}/scrape_{hostname}.json"
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_text(json.dumps(result, indent=2))

        print(json.dumps(result, indent=2))

    except Exception as e:
        log("scrape_failed", {"url": args.url, "error": str(e)}, run_id)
        # Return structured failure so orchestrator can handle gracefully
        failure = {"status": "failed", "url": args.url, "reason": str(e)}
        print(json.dumps(failure, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
