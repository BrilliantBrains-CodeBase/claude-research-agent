#!/usr/bin/env python3
"""Generate a human-readable run summary from a run's events.jsonl."""

import argparse
import json
import sys
import time
from pathlib import Path


def load_events(run_dir: Path) -> list[dict]:
    log_file = run_dir / "events.jsonl"
    if not log_file.exists():
        return []
    events = []
    for line in log_file.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return events


def group_events(events: list[dict]) -> dict:
    counts = {
        "searches": 0, "search_failures": 0,
        "scrapes": 0, "scrape_failures": 0,
        "competitors_discovered": 0, "competitors_analyzed": 0,
        "domain_skill_bootstrapped": 0,
        "synthesis_completed": 0,
        "questions_generated": 0,
        "validation_passed": 0, "validation_failed": 0,
    }
    for e in events:
        ev = e.get("event", "")
        if ev == "search_completed":
            counts["searches"] += 1
        elif ev == "search_failed":
            counts["search_failures"] += 1
        elif ev == "scrape_completed":
            counts["scrapes"] += 1
        elif ev == "scrape_failed":
            counts["scrape_failures"] += 1
        elif ev == "competitor_discovered":
            counts["competitors_discovered"] += 1
        elif ev == "competitor_analyzed":
            counts["competitors_analyzed"] += 1
        elif ev == "domain_skill_bootstrapped":
            counts["domain_skill_bootstrapped"] += 1
        elif ev == "synthesis_completed":
            counts["synthesis_completed"] += 1
        elif ev == "questions_generated":
            counts["questions_generated"] += 1
        elif ev == "validation_passed":
            counts["validation_passed"] += 1
        elif ev == "validation_failed":
            counts["validation_failed"] += 1
    return counts


def format_ts(ts: float) -> str:
    return time.strftime("%H:%M:%S", time.gmtime(ts))


def build_report(run_id: str, events: list[dict], counts: dict, run_dir: Path) -> str:
    lines = [
        f"# Run Report — {run_id}",
        f"",
        f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}",
        f"",
        "## Summary",
        f"",
        f"| Metric | Count |",
        f"|--------|-------|",
        f"| Searches completed | {counts['searches']} |",
        f"| Search failures | {counts['search_failures']} |",
        f"| Pages scraped | {counts['scrapes']} |",
        f"| Scrape failures | {counts['scrape_failures']} |",
        f"| Competitors analyzed | {counts['competitors_analyzed']} |",
        f"| Domain skill bootstrapped | {'yes' if counts['domain_skill_bootstrapped'] else 'no'} |",
        f"| Synthesis completed | {'yes' if counts['synthesis_completed'] else 'no'} |",
        f"| Questions generated | {'yes' if counts['questions_generated'] else 'no'} |",
        f"| Validation | {'PASSED' if counts['validation_passed'] else 'FAILED' if counts['validation_failed'] else 'not run'} |",
        f"",
    ]

    # Outcome status
    if counts["validation_passed"]:
        lines += ["**Status: PASSED** — research output ready for review.", ""]
    elif counts["validation_failed"]:
        lines += ["**Status: FAILED** — see validation_report.md for details.", ""]
    else:
        lines += ["**Status: INCOMPLETE** — validation not run.", ""]

    # Failures detail
    failed_scrapes = [e for e in events if e.get("event") == "scrape_failed"]
    failed_searches = [e for e in events if e.get("event") == "search_failed"]
    if failed_scrapes or failed_searches:
        lines += ["## Failures", ""]
        for e in failed_searches:
            lines.append(f"- **Search failed:** query=`{e.get('query', '?')}` — {e.get('error', '?')}")
        for e in failed_scrapes:
            lines.append(f"- **Scrape failed:** url=`{e.get('url', '?')}` — {e.get('reason', e.get('error', '?'))}")
        lines.append("")

    # Timeline
    lines += ["## Event timeline", ""]
    if events:
        for e in events:
            ts_str = format_ts(e.get("ts", 0))
            ev = e.get("event", "?")
            detail = ""
            if "query" in e:
                detail = f"query={e['query']!r}"
            elif "url" in e:
                detail = f"url={e['url']}"
            elif "vertical" in e:
                detail = f"vertical={e['vertical']}, geo={e.get('geo', '?')}"
            elif "failure_count" in e:
                detail = f"failures={e['failure_count']}"
            lines.append(f"- `{ts_str}` {ev}" + (f" — {detail}" if detail else ""))
    else:
        lines.append("_No events recorded._")
    lines.append("")

    # Link to validation report if exists
    val_report = run_dir / "validation_report.md"
    if val_report.exists():
        lines += ["## Validation details", "", val_report.read_text(), ""]

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate human-readable run report")
    parser.add_argument("--run-id", help="Run ID (reads .tmp/runs/current if omitted)")
    args = parser.parse_args()

    run_id = args.run_id
    if not run_id:
        current = Path(".tmp/runs/current")
        if not current.exists():
            print("ERROR: No run ID specified and .tmp/runs/current not found", file=sys.stderr)
            sys.exit(1)
        run_id = current.read_text().strip()

    run_dir = Path(f".tmp/runs/{run_id}")
    if not run_dir.exists():
        print(f"ERROR: Run directory not found: {run_dir}", file=sys.stderr)
        sys.exit(1)

    events = load_events(run_dir)
    counts = group_events(events)
    report = build_report(run_id, events, counts, run_dir)

    out_path = run_dir / "report.md"
    out_path.write_text(report)
    print(report)
    print(f"\n(Written to {out_path})", file=sys.stderr)


if __name__ == "__main__":
    main()
