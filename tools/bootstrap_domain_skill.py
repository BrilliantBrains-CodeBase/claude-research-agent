#!/usr/bin/env python3
"""
Generate or seed domain_skill.md for a vertical before research begins.

Priority:
1. If memory/verticals/<vertical>.md exists → copy as seed (accumulated knowledge)
2. Otherwise → render domain_skill.template.md with built-in vertical defaults
"""

import argparse
import json
import os
import sys
import time
import uuid
from pathlib import Path
from string import Template

# ---------------------------------------------------------------------------
# Built-in vertical knowledge
# ---------------------------------------------------------------------------

VERTICAL_KNOWLEDGE: dict[str, dict] = {
    "hospital": {
        "query_patterns": [
            '"{vertical} {geo}"',
            '"best {vertical} in {geo}"',
            '"multispeciality {vertical} {geo}"',
            '"{vertical} near {geo}"',
            '"top {vertical} {geo}"',
        ],
        "standard_sections": [
            "Header (Logo + Phone + CTA)",
            "Hero (Primary headline + CTA)",
            "Services / Specialities",
            "Doctors / Specialists",
            "Facilities & Infrastructure",
            "Why Choose Us / Stats",
            "Testimonials / Patient Stories",
            "Accreditations & Awards",
            "FAQ",
            "Contact Form",
            "Footer",
        ],
        "trust_signal_categories": [
            "NABH accreditation",
            "NABL accreditation",
            "JCI accreditation",
            "ISO certification",
            "Years in operation",
            "Number of beds",
            "Number of specialists / doctors",
            "Number of procedures performed",
            "Insurance / cashless tie-ups",
            "Emergency availability (24x7)",
        ],
        "insurance_payment_relevant": True,
        "competitor_red_flags": [
            "No phone visible above fold",
            "No emergency/24x7 mention",
            "No accreditation badges",
            "Generic stock photos only (no real doctors/facilities)",
            "No speciality listing",
        ],
        "national_chains_exclude": [
            "apollohospitals.com", "fortishealthcare.com", "manipalhospitals.com",
            "maxhealthcare.in", "medanta.org", "narayanahealth.org",
            "aster", "cloudnine", "lilavati",
        ],
    },
    "school": {
        "query_patterns": [
            '"{vertical} {geo}"',
            '"best {vertical} in {geo}"',
            '"cbse {vertical} {geo}"',
            '"icse {vertical} {geo}"',
            '"top {vertical} near {geo}"',
        ],
        "standard_sections": [
            "Header (Logo + Phone + Admission CTA)",
            "Hero (Headline + Admission CTA)",
            "About the School",
            "Programs / Classes Offered",
            "Faculty",
            "Infrastructure / Campus",
            "Achievements & Awards",
            "Testimonials (Parents / Alumni)",
            "Gallery",
            "FAQ",
            "Contact Form / Admission Form",
            "Footer",
        ],
        "trust_signal_categories": [
            "CBSE / ICSE / IB / IGCSE affiliation",
            "Years established",
            "Student strength / enrollment",
            "Pass percentage / board results",
            "Sports / extra-curricular achievements",
            "Alumni achievements",
            "Fee structure transparency",
        ],
        "insurance_payment_relevant": False,
        "competitor_red_flags": [
            "No admission CTA above fold",
            "No affiliation board mentioned",
            "No faculty credentials",
            "Outdated gallery",
            "No result/achievement stats",
        ],
        "national_chains_exclude": [
            "allen.ac.in", "fiitjee.com", "resonance.ac.in",
            "delhipublicschool", "ryan international", "dav",
        ],
    },
    "clinic": {
        "query_patterns": [
            '"{vertical} {geo}"',
            '"best {vertical} in {geo}"',
            '"{specialty} {vertical} {geo}"',
            '"top {vertical} near {geo}"',
        ],
        "standard_sections": [
            "Header (Logo + Phone + Book Appointment CTA)",
            "Hero (Doctor/Clinic intro + CTA)",
            "About the Doctor / Clinic",
            "Services / Treatments",
            "Conditions Treated",
            "Testimonials",
            "FAQ",
            "Contact Form / Appointment Booking",
            "Footer",
        ],
        "trust_signal_categories": [
            "MBBS / MD / MS / DNB qualifications",
            "Years of experience",
            "Number of patients treated",
            "Hospital affiliations",
            "Recognition / awards",
        ],
        "insurance_payment_relevant": True,
        "competitor_red_flags": [
            "No doctor credentials visible",
            "No appointment booking flow",
            "No location/map",
        ],
        "national_chains_exclude": [
            "practo.com", "lybrate.com", "justdial.com",
        ],
    },
    "real_estate": {
        "query_patterns": [
            '"property developer {geo}"',
            '"real estate {geo}"',
            '"flats for sale {geo}"',
            '"apartments {geo}"',
            '"property builder {geo}"',
        ],
        "standard_sections": [
            "Header (Logo + Phone + Enquire Now)",
            "Hero (Project highlight + CTA)",
            "Projects / Properties",
            "Location Advantages",
            "Amenities",
            "Floor Plans",
            "Testimonials",
            "About the Builder",
            "FAQ",
            "Contact Form / Site Visit CTA",
            "Footer",
        ],
        "trust_signal_categories": [
            "RERA registration number",
            "Years in real estate",
            "Projects delivered",
            "Happy customers",
            "Awards / recognitions",
        ],
        "insurance_payment_relevant": False,
        "competitor_red_flags": [
            "No RERA number",
            "No floor plans",
            "No location map",
            "No project handover dates",
        ],
        "national_chains_exclude": [
            "99acres.com", "magicbricks.com", "housing.com",
            "godrej", "lodha", "prestige", "dlf",
        ],
    },
    "coaching": {
        "query_patterns": [
            '"coaching institute {geo}"',
            '"best coaching {geo}"',
            '"{exam} coaching {geo}"',
            '"tuition classes {geo}"',
        ],
        "standard_sections": [
            "Header (Logo + Phone + Enroll CTA)",
            "Hero (Results/Success rate + CTA)",
            "Courses / Programs",
            "Faculty",
            "Results / Selections",
            "Study Material / Methodology",
            "Testimonials / Student Stories",
            "FAQ",
            "Contact Form / Demo Class CTA",
            "Footer",
        ],
        "trust_signal_categories": [
            "Selections / rank holders",
            "Years established",
            "Student count / batch size",
            "Faculty credentials",
            "Success rate percentage",
        ],
        "insurance_payment_relevant": False,
        "competitor_red_flags": [
            "No selection stats",
            "No faculty credentials",
            "No batch size / schedule info",
        ],
        "national_chains_exclude": [
            "allen.ac.in", "fiitjee.com", "resonance.ac.in",
            "akash", "byju", "unacademy", "vedantu",
        ],
    },
}

FALLBACK_VERTICAL = {
    "query_patterns": [
        '"{vertical} {geo}"',
        '"best {vertical} in {geo}"',
        '"top {vertical} near {geo}"',
    ],
    "standard_sections": [
        "Header (Logo + Phone + CTA)",
        "Hero",
        "Services / Offerings",
        "About Us",
        "Testimonials",
        "FAQ",
        "Contact Form",
        "Footer",
    ],
    "trust_signal_categories": [
        "Years in operation",
        "Number of clients / customers served",
        "Awards / certifications",
    ],
    "insurance_payment_relevant": False,
    "competitor_red_flags": [
        "No phone above fold",
        "No clear CTA",
        "No trust signals",
    ],
    "national_chains_exclude": [],
}

# ---------------------------------------------------------------------------

TEMPLATE_STR = """\
---
status: ready
vertical: {vertical}
geo: {geo}
generated_date: {date}
insurance_payment_relevant: {insurance}
source: {source}
---

# Domain Skill — {vertical_title}

## Query patterns for competitor discovery

Use these query variants when calling `firecrawl_search.py`:

{query_patterns}

## Standard sections for this vertical

These sections are expected on any {vertical_title} landing page. Include sections
not found in competitors as `high` priority in `section_inventory.md`.

{standard_sections}

## Trust signal categories

Look for these on competitor pages. Record which ones appear in the competitor analysis.

{trust_signals}

## Insurance / payment relevance

`insurance_payment_relevant: {insurance}` — {"Include insurance/cashless questions in domain_questions.md." if ins else "Skip insurance/payment section in domain questions."}

## National chains to exclude from competitor search

These are too large to be meaningful benchmarks for a local {vertical_title}:

{national_chains}

## Competitor red flags (gaps = our opportunities)

If a competitor is missing these, note them as weaknesses:

{red_flags}

## Lessons learned (append after each project)

<!-- Orchestrator appends here after each research run. Format:
- YYYY-MM-DD [{geo}]: <finding>
-->
"""


def render_template(vertical: str, geo: str, knowledge: dict) -> str:
    vertical_title = vertical.replace("_", " ").title()
    ins = knowledge["insurance_payment_relevant"]

    query_patterns = "\n".join(
        f"- {p.format(vertical=vertical, geo=geo)}"
        for p in knowledge["query_patterns"]
    )
    standard_sections = "\n".join(f"- {s}" for s in knowledge["standard_sections"])
    trust_signals = "\n".join(f"- {t}" for t in knowledge["trust_signal_categories"])
    national_chains = "\n".join(f"- {c}" for c in knowledge["national_chains_exclude"]) or "- (none specified)"
    red_flags = "\n".join(f"- {r}" for r in knowledge["competitor_red_flags"])

    return TEMPLATE_STR.format(
        vertical=vertical,
        vertical_title=vertical_title,
        geo=geo,
        date=time.strftime("%Y-%m-%d"),
        insurance=str(ins).lower(),
        ins=ins,
        source="built-in vertical knowledge",
        query_patterns=query_patterns,
        standard_sections=standard_sections,
        trust_signals=trust_signals,
        national_chains=national_chains,
        red_flags=red_flags,
    )


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


def main():
    parser = argparse.ArgumentParser(description="Bootstrap domain_skill.md for a vertical")
    parser.add_argument("--vertical", required=True, help="Vertical slug (e.g. hospital, school, clinic)")
    parser.add_argument("--geo", required=True, help="Geography (e.g. 'Mumbai', 'Pune')")
    parser.add_argument("--output-dir", default="01_research", help="Directory to write domain_skill.md")
    args = parser.parse_args()

    vertical = args.vertical.lower().replace(" ", "_")
    output_dir = Path(args.output_dir)
    output_path = output_dir / "domain_skill.md"

    if output_path.exists():
        print(f"domain_skill.md already exists at {output_path} — skipping bootstrap")
        print(str(output_path))
        return

    # Priority 1: use accumulated memory if available
    memory_path = Path(f"memory/verticals/{vertical}.md")
    if memory_path.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
        content = memory_path.read_text()
        # Update geo in frontmatter line
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if line.startswith("geo:"):
                lines[i] = f"geo: {args.geo}"
                break
        output_path.write_text("\n".join(lines))
        log("domain_skill_bootstrapped", {"vertical": vertical, "geo": args.geo, "source": "memory"})
        print(f"Bootstrapped from memory: {output_path}", file=sys.stderr)
        print(str(output_path))
        return

    # Priority 2: use built-in knowledge or fallback
    knowledge = VERTICAL_KNOWLEDGE.get(vertical, FALLBACK_VERTICAL)
    if vertical not in VERTICAL_KNOWLEDGE:
        print(f"Warning: no built-in knowledge for '{vertical}', using generic fallback", file=sys.stderr)

    content = render_template(vertical, args.geo, knowledge)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content)

    log("domain_skill_bootstrapped", {"vertical": vertical, "geo": args.geo, "source": "built-in"})
    print(f"Bootstrapped from built-in knowledge: {output_path}", file=sys.stderr)
    print(str(output_path))


if __name__ == "__main__":
    main()
