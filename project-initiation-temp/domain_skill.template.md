---
status: pending
vertical: {{VERTICAL}}
geo: {{GEO}}
generated_date:
insurance_payment_relevant: {{true|false}}
source: {{built-in|memory|manual}}
---

# Domain Skill — {{VERTICAL}}

> **How this file is used:**
> `bootstrap_domain_skill.py` generates this file automatically from built-in knowledge or
> accumulated memory. If you need to create it manually, fill in all sections below and
> set `status: ready` before the Research pipeline begins.

## Query patterns for competitor discovery

Use these query variants when calling `tools/firecrawl_search.py`:

- "{{vertical}} {{geo}}"
- "best {{vertical}} in {{geo}}"
- "top {{vertical}} near {{geo}}"
- Add vertical-specific variants here (e.g. "multispeciality hospital Mumbai")

## Standard sections for this vertical

These sections are expected on any {{VERTICAL}} landing page. Include any section listed
here but NOT found in competitors as `high` priority in `section_inventory.md`.

- Header (Logo + Phone + CTA)
- Hero (Primary headline + CTA)
- Services / Core Offering
- About Us / Team
- Testimonials
- FAQ
- Contact Form
- Footer
- (Add vertical-specific sections here)

## Trust signal categories

Look for these on competitor pages when running the Analyzer agent.

- Years in operation
- Number of clients / customers served
- Awards / certifications
- (Add vertical-specific signals, e.g. NABH for hospitals, RERA for real estate)

## Insurance / payment relevance

`insurance_payment_relevant: {{true|false}}`

If `true`, include insurance/cashless/payment questions in `domain_questions.md`.
If `false`, skip the insurance section in the Question Generator.

## National chains to exclude from competitor search

Pass these as `--exclude-domains` to `firecrawl_search.py`:

- (List domain slugs, e.g. apollohospitals.com, 99acres.com)

## Competitor red flags (gaps = our opportunities)

If a competitor is missing these, note them as weaknesses in `competitor_analysis.md`:

- No phone visible above fold
- No clear CTA
- No trust signals
- (Add vertical-specific red flags)

## Lessons learned (append after each project)

<!-- Orchestrator appends here after each research run completes. Format:
- YYYY-MM-DD [geo]: <finding>
-->
