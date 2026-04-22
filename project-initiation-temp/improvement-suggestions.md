## Plan: Research Agent Capability Upgrade

Upgrade the research pipeline in three layers: unblock execution first (web discovery + scraping + validation), improve output quality second (synthesis + gap analysis), and add scale features last (knowledge base + observability). This minimizes risk while quickly improving reliability.

**Steps**
1. Phase 1: Foundation and reliability.
2. Add Firecrawl for search + scrape to replace manual web-fetch assumptions.
3. Add a domain skill bootstrap tool so domain_skill.md is always generated before research starts.
4. Add a research validator that enforces checklist constraints (competitor count, section count, mandatory sections, gap annotations).
5. Phase 2: Structured intelligence.
6. Add a Competitor Discoverer agent for URL selection and credibility scoring.
7. Add a Competitor Analyzer agent using strict extraction schema output.
8. Add a Research Synthesizer agent to generate cross-competitor patterns and section priority evidence.
9. Add a Domain Question Generator agent that derives questions from PID-vs-competitor gaps.
10. Phase 3: Scale and governance.
11. Add an Orchestrator reviewer agent to approve/block handoffs with quality reports.
12. Add a vertical knowledge memory store for reusable patterns across future projects.
13. Add telemetry/dashboard reporting for run traceability and failure analysis.

**Relevant files**
- /Users/anujjainbatu/Desktop/website-content-writer/CLAUDE.md — WAT operating model and tool-first execution constraints.
- /Users/anujjainbatu/Desktop/website-content-writer/project-initiation-temp/RESEARCH.md — current Research Agent SOP and hard rules.
- /Users/anujjainbatu/Desktop/website-content-writer/tools — deterministic scripts location for tool implementations.
- /Users/anujjainbatu/Desktop/website-content-writer/workflows — workflow docs for new orchestrator and specialized research agents.

**Verification**
1. Run one end-to-end sample project and confirm the pipeline produces at least 3 competitors, at least 6 sections, and at least 5 gap-tagged domain questions.
2. Confirm all mandatory sections are always present (Header, Hero, FAQ, Contact Form, Footer).
3. Confirm any failed scrape/search step is logged with a retry/fallback path.
4. Confirm reviewer agent blocks progression when checklist rules fail.

**Decisions**
- Included: MCP/plugin suggestions directly tied to discovery, extraction, synthesis, and validation.
- Excluded: downstream content/design/development automation until research stage is stable.
- Assumption: priority is better research quality and repeatability, not full multi-agent autonomy on day one.

**Further Considerations**
1. Prefer fastest rollout: Firecrawl + validator + 2 agent roles first.
2. Prefer best long-term leverage: add vertical memory store and orchestration governance next.
3. Decide tolerance for external dependency cost (MCP API usage) before scaling to all projects.
