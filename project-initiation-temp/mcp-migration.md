## Plan: Replace HTTP with MCP Connectors

Replace only the external-call boundary (Firecrawl HTTP connectors) with MCP connectors, while keeping all domain-specific local tools and workflow logic intact. This gives connector standardization without disrupting your deterministic validation, logging, and markdown generation pipeline.

**Steps**
1. Phase 1: Baseline and contract lock.
2. Freeze current behavior by capturing baseline outputs from existing search and scrape connectors, including key fields, retry behavior, and failure payload shapes.
3. Define one connector contract for discovery and one for page extraction, matching today’s downstream expectations in workflows and output files. Depends on step 2.
4. Phase 2: Build MCP connector layer.
5. Implement MCP search and MCP scrape connectors that map one-to-one with current connector inputs and outputs, including timeout and retry semantics. Depends on step 3.
6. Add a connector selection switch (MCP or legacy HTTP) so migration can run in shadow mode and rollback is immediate. Depends on step 5.
7. Phase 3: Workflow cutover.
8. Update Discoverer workflow to call MCP search while preserving scoring, filtering, and competitor JSON format. Depends on step 6.
9. Update Analyzer workflow to call MCP scrape while preserving extracted keys used for competitor analysis appends and summary rows. Depends on step 6.
10. Keep Orchestrator control flow unchanged except invocation wiring and explicit fallback branch when MCP call fails. Depends on steps 8 and 9.
11. Phase 4: Observability and compatibility hardening.
12. Preserve existing run telemetry events and report generation so migration does not break run history or review diagnostics. Parallel with steps 8 and 9.
13. Run parity checks across at least one full project run and one failure-path run (rate-limit/timeout) before declaring default MCP path. Depends on steps 10 and 12.
14. Phase 5: Default switch and deprecation.
15. Promote MCP path to default after parity pass, keep legacy connectors behind fallback for one release cycle, then deprecate.

**Relevant files**
- /Users/anujjainbatu/Desktop/website-content-writer/workflows/research/00_orchestrator.md — preserve sequence; adjust connector invocation and fallback branch.
- /Users/anujjainbatu/Desktop/website-content-writer/workflows/research/01_discoverer.md — replace direct HTTP script call path with MCP search connector usage.
- /Users/anujjainbatu/Desktop/website-content-writer/workflows/research/02_analyzer.md — replace direct HTTP script call path with MCP scrape connector usage.
- /Users/anujjainbatu/Desktop/website-content-writer/tools/firecrawl_search.py — reference behavior contract for query, exclusion filtering, retries, and output schema.
- /Users/anujjainbatu/Desktop/website-content-writer/tools/firecrawl_scrape.py — reference behavior contract for scrape payload, metadata extraction, and structured failure output.
- /Users/anujjainbatu/Desktop/website-content-writer/tools/log_run.py — ensure event continuity under MCP path.
- /Users/anujjainbatu/Desktop/website-content-writer/tools/report_run.py — verify reporting remains compatible with unchanged event model.
- /Users/anujjainbatu/Desktop/website-content-writer/.env — retain FIRECRAWL_API_KEY and add any MCP connector configuration keys.

**Verification**
1. Contract parity: confirm MCP search returns URL, title, description, rank fields consumed by discoverer scoring and output file writing.
2. Contract parity: confirm MCP scrape returns url, markdown, html excerpt, links, and metadata keys consumed by analyzer extraction logic.
3. Failure parity: confirm retry/backoff and failure payload behavior for rate limits and timeouts are equivalent to current expectations.
4. End-to-end parity: run full orchestrator flow and verify discovered competitors, competitor analysis completeness, and reviewer pass behavior are unchanged.
5. Rollback test: force fallback to legacy path and confirm the same run can continue without pipeline redesign.

**Decisions**
- Included: replacing external Firecrawl HTTP connector invocation with MCP connectors.
- Excluded: replacing local deterministic tools (bootstrap, validator, logger, reporter) and synthesis/question logic.
- Cutover strategy: phased migration with dual-path fallback until MCP parity is validated.
- Success criterion: no behavioral regression in output files, quality-gate outcomes, or run telemetry.

**Further Considerations**
1. Runtime toggle location: environment variable switch versus orchestrator-level argument switch.
2. Fallback retention window: one release cycle is recommended before connector deprecation.
3. If MCP response ranking differs, normalize ordering in Discoverer scoring layer rather than in connector layer.
