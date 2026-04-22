#!/usr/bin/env python3
"""Append a structured event to the current run's JSONL event log."""

import argparse
import json
import os
import sys
import time
import uuid
from pathlib import Path


def get_run_dir(run_id: str | None) -> Path:
    runs_root = Path(".tmp/runs")
    if run_id:
        run_dir = runs_root / run_id
    else:
        current_file = runs_root / "current"
        if current_file.exists():
            run_id = current_file.read_text().strip()
            run_dir = runs_root / run_id
        else:
            run_id = str(uuid.uuid4())[:8]
            run_dir = runs_root / run_id
            runs_root.mkdir(parents=True, exist_ok=True)
            current_file.write_text(run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def log_event(event: str, payload: dict, run_id: str | None) -> Path:
    run_dir = get_run_dir(run_id)
    log_file = run_dir / "events.jsonl"
    record = {
        "ts": time.time(),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "event": event,
        **payload,
    }
    with log_file.open("a") as f:
        f.write(json.dumps(record) + "\n")
    return log_file


def main():
    parser = argparse.ArgumentParser(description="Log a run event to JSONL")
    parser.add_argument("--event", required=True, help="Event name (e.g. search_started)")
    parser.add_argument("--payload", default="{}", help="JSON payload string")
    parser.add_argument("--run-id", help="Run ID (reads .tmp/runs/current if omitted)")
    args = parser.parse_args()

    try:
        payload = json.loads(args.payload)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON payload: {e}", file=sys.stderr)
        sys.exit(1)

    log_file = log_event(args.event, payload, args.run_id)
    print(str(log_file))


if __name__ == "__main__":
    main()
