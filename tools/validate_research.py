#!/usr/bin/env python3
"""
Mechanized enforcement of the Research Agent self-review checklist.

Checks:
  competitor_analysis.md  — ≥3 competitors, populated fields, cross-competitor section
  section_inventory.md    — ≥6 sections, mandatory sections present, FAQ before Contact Form
  domain_questions.md     — ≥5 questions, every question has _Gap addressed:_, no generic questions

Exit 0 = all checks pass. Exit 1 = one or more checks failed.
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

MANDATORY_SECTIONS = {"header", "hero", "faq", "contact form", "footer"}

GENERIC_DENY_LIST = [
    r"what is your (name|business|company)",
    r"tell us about (yourself|your business|your company)",
    r"what do you do",
    r"who are you",
    r"describe your business",
    r"what is the name of",
    r"what services do you offer\??$",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_file(path: Path, label: str) -> str:
    if not path.exists():
        return f"__MISSING__"
    return path.read_text(encoding="utf-8")


def section_name_lower(row: str) -> str:
    """Extract section name from a markdown table row and lowercase it."""
    # Row format: | 1 | Header | /5 | mandatory | ... |
    parts = [p.strip() for p in row.strip().strip("|").split("|")]
    if len(parts) >= 2:
        return parts[1].lower().strip()
    return ""


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_competitor_analysis(content: str) -> list[str]:
    failures = []
    if content == "__MISSING__":
        return ["competitor_analysis.md is MISSING"]

    # Count competitor header blocks (## Competitor N:)
    competitor_blocks = re.findall(r"^## Competitor \d+:", content, re.MULTILINE)
    if len(competitor_blocks) < 3:
        failures.append(
            f"competitor_analysis.md: only {len(competitor_blocks)} competitor block(s) found — need ≥3"
        )

    # Check cross-competitor section is non-empty
    cross_match = re.search(
        r"## Cross-competitor patterns(.*?)(?=^##|\Z)", content, re.DOTALL | re.MULTILINE
    )
    if not cross_match:
        failures.append("competitor_analysis.md: '## Cross-competitor patterns' section missing")
    else:
        cross_body = cross_match.group(1).strip()
        # All bullets should have real content (not just "-")
        bullets = [b.strip() for b in re.findall(r"^-\s*(.*)", cross_body, re.MULTILINE)]
        empty_bullets = [b for b in bullets if not b]
        if not bullets or all(not b for b in bullets):
            failures.append("competitor_analysis.md: cross-competitor patterns section is empty")

    # For each competitor block, check required sub-sections exist and are non-empty
    required_subsections = [
        "section structure",
        "trust signals",
        "ctas observed",
        "contact visibility",
    ]
    for i, block_match in enumerate(
        re.finditer(r"(## Competitor \d+:.*?)(?=^## Competitor|\Z)", content, re.DOTALL | re.MULTILINE)
    ):
        block = block_match.group(1).lower()
        for sub in required_subsections:
            if sub not in block:
                failures.append(
                    f"competitor_analysis.md: Competitor {i+1} missing sub-section '{sub}'"
                )

    return failures


def check_section_inventory(content: str) -> list[str]:
    failures = []
    if content == "__MISSING__":
        return ["section_inventory.md is MISSING"]

    # Extract table rows (skip header and separator rows)
    table_rows = [
        line for line in content.splitlines()
        if line.startswith("|") and not re.match(r"\|[-\s|]+\|", line)
    ]
    # First row is likely the header row — filter it
    data_rows = [r for r in table_rows if not re.search(r"section name", r, re.IGNORECASE)]
    section_names = [section_name_lower(r) for r in data_rows if section_name_lower(r)]

    if len(section_names) < 6:
        failures.append(
            f"section_inventory.md: only {len(section_names)} section(s) found — need ≥6"
        )

    # Mandatory sections check
    for mandatory in MANDATORY_SECTIONS:
        found = any(mandatory in name for name in section_names)
        if not found:
            failures.append(f"section_inventory.md: mandatory section '{mandatory}' not found")

    # FAQ must appear before Contact Form in "Recommended section order"
    order_match = re.search(
        r"## Recommended section order.*?\n(.*?)(?=^##|\Z)", content, re.DOTALL | re.MULTILINE
    )
    if order_match:
        order_text = order_match.group(1).lower()
        faq_pos = order_text.find("faq")
        contact_pos = order_text.find("contact form")
        if faq_pos == -1:
            failures.append("section_inventory.md: FAQ not listed in recommended section order")
        elif contact_pos == -1:
            failures.append("section_inventory.md: Contact Form not listed in recommended section order")
        elif faq_pos > contact_pos:
            failures.append(
                "section_inventory.md: FAQ appears AFTER Contact Form in recommended order — must be before"
            )
    else:
        failures.append("section_inventory.md: '## Recommended section order' section missing")

    return failures


def check_domain_questions(content: str) -> list[str]:
    failures = []
    if content == "__MISSING__":
        return ["domain_questions.md is MISSING"]

    # Find all questions — **Q1:**, **Q2:**, etc.
    question_matches = list(re.finditer(r"\*\*Q(\d+):\*\*\s*(.*?)(?=\*\*Q\d+:|\Z)", content, re.DOTALL))

    if len(question_matches) < 5:
        failures.append(
            f"domain_questions.md: only {len(question_matches)} question(s) found — need ≥5"
        )

    for m in question_matches:
        q_num = m.group(1)
        q_body = m.group(2).strip()

        # Must have non-empty body
        body_lines = [l.strip() for l in q_body.splitlines() if l.strip()]
        if not body_lines:
            failures.append(f"domain_questions.md: Q{q_num} has no body text")
            continue

        # Must have _Gap addressed:_ with non-empty content
        gap_match = re.search(r"_Gap addressed:_\s*(.*)", q_body)
        if not gap_match:
            failures.append(f"domain_questions.md: Q{q_num} missing '_Gap addressed:_' annotation")
        elif not gap_match.group(1).strip():
            failures.append(f"domain_questions.md: Q{q_num} has empty '_Gap addressed:_'")

        # Check against generic deny-list
        question_text = body_lines[0].lower()
        for pattern in GENERIC_DENY_LIST:
            if re.search(pattern, question_text, re.IGNORECASE):
                failures.append(
                    f"domain_questions.md: Q{q_num} matches generic pattern '{pattern}' — too broad"
                )

    return failures


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def write_report(failures: list[str], run_dir: Path | None) -> str:
    passed = len(failures) == 0
    lines = [
        f"# Research Validation Report",
        f"",
        f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}",
        f"**Result:** {'PASSED' if passed else 'FAILED'}",
        f"",
    ]
    if passed:
        lines += ["All checks passed. Files are ready for status: review."]
    else:
        lines += [f"**{len(failures)} check(s) failed:**", ""]
        for i, f in enumerate(failures, 1):
            lines.append(f"{i}. {f}")
        lines += [
            "",
            "Fix the above issues and re-run the reviewer before setting status: review.",
        ]

    report = "\n".join(lines)

    if run_dir:
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "validation_report.md").write_text(report)

    return report


def log(event: str, payload: dict):
    current = Path(".tmp/runs/current")
    if not current.exists():
        return
    run_id = current.read_text().strip()
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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Validate research output files")
    parser.add_argument("--research-dir", default="01_research", help="Directory containing output files")
    parser.add_argument("--run-id", help="Run ID for report destination")
    args = parser.parse_args()

    research_dir = Path(args.research_dir)

    ca_content = load_file(research_dir / "competitor_analysis.md", "competitor_analysis.md")
    si_content = load_file(research_dir / "section_inventory.md", "section_inventory.md")
    dq_content = load_file(research_dir / "domain_questions.md", "domain_questions.md")

    all_failures = (
        check_competitor_analysis(ca_content)
        + check_section_inventory(si_content)
        + check_domain_questions(dq_content)
    )

    # Determine run dir for report
    run_dir = None
    if args.run_id:
        run_dir = Path(f".tmp/runs/{args.run_id}")
    elif Path(".tmp/runs/current").exists():
        run_id = Path(".tmp/runs/current").read_text().strip()
        run_dir = Path(f".tmp/runs/{run_id}")

    report = write_report(all_failures, run_dir)
    print(report)

    passed = len(all_failures) == 0
    log(
        "validation_passed" if passed else "validation_failed",
        {"failures": all_failures, "failure_count": len(all_failures)},
    )

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
