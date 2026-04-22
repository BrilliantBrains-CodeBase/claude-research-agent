#!/usr/bin/env python3
"""
Normalize page scrape output from any connector (Playwright, WebFetch, Firecrawl)
to the canonical {url, markdown, html_excerpt, links, meta} schema used by the Analyzer.

Usage:
  python tools/normalize_scrape_output.py --input playwright_output.json
  echo '<json>' | python tools/normalize_scrape_output.py --url https://example.com
  python tools/normalize_scrape_output.py --input data.json --output scrape_result.json

Input format guide:
  Playwright/evaluate:
    {
      "source": "playwright",
      "url": "...",
      "title": "...",
      "body_text": "...",
      "links": ["https://..."],
      "meta_description": "...",
      "og_title": "...",
      "og_description": "..."
    }

  WebFetch:
    {"url": "...", "content": "...", "title": "..."}

  Firecrawl (pass-through):
    {url, markdown, html_excerpt, links, meta: {title, description, og_title, og_description, status_code}}

Playwright browser_evaluate script (paste into browser_evaluate to get input for this tool):

  (function() {
    var title = document.title;
    var desc = (document.querySelector('meta[name="description"]') || {}).content || '';
    var ogTitle = (document.querySelector('meta[property="og:title"]') || {}).content || '';
    var ogDesc = (document.querySelector('meta[property="og:description"]') || {}).content || '';
    var bodyText = document.body.innerText.substring(0, 60000);
    var links = Array.from(document.querySelectorAll('a[href]'))
      .map(function(a) { return a.href; })
      .filter(function(h) { return h.indexOf('http') === 0; })
      .slice(0, 200);
    return JSON.stringify({
      source: 'playwright',
      url: window.location.href,
      title: title,
      body_text: bodyText,
      links: links,
      meta_description: desc,
      og_title: ogTitle,
      og_description: ogDesc
    });
  })()
"""

import argparse
import json
import sys
from pathlib import Path


def detect_format(data: dict) -> str:
    if not isinstance(data, dict):
        return "unknown"
    # Canonical Firecrawl format: has markdown + html_excerpt + meta dict
    if "markdown" in data and "html_excerpt" in data and isinstance(data.get("meta"), dict):
        return "firecrawl"
    # Playwright evaluate format
    if data.get("source") == "playwright" or "body_text" in data:
        return "playwright"
    # WebFetch format: url + content (markdown-ish text) + optional title
    if "content" in data and "url" in data:
        return "webfetch"
    # Partial/minimal: has url + some text under various keys
    if "url" in data:
        return "minimal"
    return "unknown"


def build_meta(data: dict) -> dict:
    return {
        "title": data.get("title") or data.get("page_title") or "",
        "description": data.get("meta_description") or data.get("description") or "",
        "og_title": data.get("og_title") or "",
        "og_description": data.get("og_description") or "",
        "status_code": data.get("status_code", 200),
    }


def normalize(data: dict, url_override: str | None) -> dict:
    fmt = detect_format(data)

    if fmt == "firecrawl":
        # Already canonical — return as-is, apply url override if provided
        if url_override and not data.get("url"):
            data["url"] = url_override
        return data

    url = url_override or data.get("url", "")

    if fmt == "playwright":
        body = data.get("body_text", "")
        return {
            "url": url,
            "markdown": body,
            "html_excerpt": body[:10240],
            "links": data.get("links", []),
            "meta": build_meta(data),
        }

    if fmt == "webfetch":
        content = data.get("content", "")
        return {
            "url": url,
            "markdown": content,
            "html_excerpt": content[:10240],
            "links": data.get("links", []),
            "meta": {
                "title": data.get("title", ""),
                "description": "",
                "og_title": "",
                "og_description": "",
                "status_code": 200,
            },
        }

    if fmt == "minimal":
        text = (
            data.get("text")
            or data.get("markdown")
            or data.get("content")
            or data.get("body")
            or ""
        )
        return {
            "url": url,
            "markdown": text,
            "html_excerpt": text[:10240],
            "links": data.get("links", []),
            "meta": build_meta(data),
        }

    print("ERROR: Cannot normalize input — unrecognized structure", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Normalize page scrape output to canonical schema")
    parser.add_argument("--input", "-i", help="Input JSON file (reads stdin if omitted)")
    parser.add_argument("--url", help="URL being scraped (used if input JSON lacks it)")
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

    result = normalize(data, args.url)
    output_json = json.dumps(result, indent=2, ensure_ascii=False)
    print(output_json)

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(output_json)


if __name__ == "__main__":
    main()
