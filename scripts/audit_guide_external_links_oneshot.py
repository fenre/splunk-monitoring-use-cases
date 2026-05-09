#!/usr/bin/env python3
"""One-shot external link audit for ``docs/guides/*.md``.

Reuses ``splunk_uc.audits.links.check_url`` for HEAD/GET probing and
per-host throttling. Writes a JSON report to
``reports/guide-external-links.json`` for downstream cleanup.

This is intentionally a one-shot driver, not a registered verb. If
external-link rot proves systemic across the guides, we'll promote it
into ``src/splunk_uc/audits/guide_external_links.py`` with proper CLI
ergonomics, ignore-list support, and CI gating. Until then it lives as
a Batch 12 cleanup driver only.
"""

from __future__ import annotations

import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from splunk_uc.audits.links import (
    MAX_WORKERS,
    PER_HOST_DELAY_SEC,
    check_url,
    load_ignore_patterns,
    normalize_url,
)

URL_RE = re.compile(r"https?://[^\s,<>\"'\]\)]+")
GUIDES_DIR = REPO_ROOT / "docs" / "guides"
REPORT_PATH = REPO_ROOT / "reports" / "guide-external-links.json"


def collect_urls() -> dict[str, list[str]]:
    """Return ``url -> [source guide basenames]`` mapping."""
    sources: dict[str, list[str]] = {}
    for path in sorted(GUIDES_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for raw in URL_RE.findall(text):
            url = normalize_url(raw)
            if not url.startswith(("http://", "https://")):
                continue
            sources.setdefault(url, []).append(path.name)
    return sources


def main() -> int:
    sources = collect_urls()
    all_urls = sorted(sources.keys())
    ignore = load_ignore_patterns()

    def is_ignored(u: str) -> bool:
        return any(p.search(u) for p in ignore)

    urls = [u for u in all_urls if not is_ignored(u)]
    ignored = [u for u in all_urls if is_ignored(u)]

    print(f"Probing {len(urls)} unique URLs ({len(ignored)} ignored)...", flush=True)

    by_host: dict[str, list[str]] = {}
    skipped_malformed: list[str] = []
    for u in urls:
        try:
            host = urlsplit(u).netloc.lower()
        except ValueError:
            # URL is malformed (e.g. unbalanced brackets, invalid IPv6 literal).
            # Surface it explicitly rather than silently dropping — that way
            # the source guide still gets a fix surfaced in the report.
            skipped_malformed.append(u)
            continue
        by_host.setdefault(host, []).append(u)

    def check_host(host_urls: list[str]) -> list[tuple[str, tuple[bool, str]]]:
        out: list[tuple[str, tuple[bool, str]]] = []
        for i, u in enumerate(host_urls):
            if i:
                time.sleep(PER_HOST_DELAY_SEC)
            try:
                out.append((u, check_url(u)))
            except Exception as e:  # never let one URL kill the whole host
                out.append((u, (False, repr(e))))
        return out

    results: dict[str, tuple[bool, str]] = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = {ex.submit(check_host, host_urls): host for host, host_urls in by_host.items()}
        done = 0
        for fut in as_completed(futs):
            host = futs[fut]
            for url, outcome in fut.result():
                results[url] = outcome
            done += 1
            print(f"  ... {done}/{len(by_host)} hosts complete (just finished {host})", flush=True)

    broken: list[dict[str, object]] = []
    ok_count = 0
    for u in urls:
        if u in skipped_malformed:
            broken.append(
                {
                    "url": u,
                    "detail": "MALFORMED (urlsplit raised ValueError)",
                    "guides": sources[u],
                }
            )
            continue
        good, detail = results[u]
        if good:
            ok_count += 1
        else:
            broken.append({"url": u, "detail": detail, "guides": sources[u]})

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(broken, indent=2) + "\n", encoding="utf-8")

    print()
    print("Summary")
    print("-------")
    print(f"  URLs checked (unique): {len(urls)}")
    print(f"  OK:                    {ok_count}")
    print(f"  Broken:                {len(broken)}")
    print(f"  Ignored (fragile):     {len(ignored)}")
    print(f"  Report:                {REPORT_PATH.relative_to(REPO_ROOT)}")
    print()
    if broken:
        print(f"=== Broken links ({len(broken)}) ===")
        for b in broken[:50]:
            print(f"  [{b['detail']}] {b['url']}")
            print(f"    sources: {', '.join(sorted(set(b['guides'])))}")  # type: ignore[arg-type]
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
