#!/usr/bin/env python3
"""Manual audit: check http(s) URLs on - **References:** lines in use-cases/cat-*.md."""

from __future__ import annotations

import argparse
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parent.parent
REFERENCES_LINE = re.compile(r"^\s*-\s*\*\*References:\*\*\s*(.*)$")
URL_PATTERN = re.compile(r"https?://[^\s,<>]+")
BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
HEAD_FALLBACK_CODES = frozenset({400, 403, 405, 501})
RATE_LIMIT_CODES = frozenset({429, 503})
TIMEOUT_SEC = 10
MAX_WORKERS = 8
RETRY_AFTER_DEFAULT = 6
PER_HOST_DELAY_SEC = 0.75  # between sequential requests to the same host
IGNORE_FILE = REPO_ROOT / ".link-check-ignore"


def load_ignore_patterns() -> list[re.Pattern[str]]:
    """Load domain/URL regex patterns that should be excluded from checking.

    The ignore file lists known-fragile sources (bot-blocked WAFs, CDNs that
    return 403 to scripted user-agents, etc.) whose content is otherwise live.
    Matching URLs are surfaced separately in the report but do **not** count
    toward the broken-link total.
    """
    if not IGNORE_FILE.is_file():
        return []
    patterns: list[re.Pattern[str]] = []
    for raw in IGNORE_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            patterns.append(re.compile(line))
        except re.error:
            print(f"[warn] invalid ignore regex: {line!r}", file=sys.stderr)
    return patterns


def normalize_url(raw: str) -> str:
    """Strip trailing punctuation while keeping balanced parentheses.

    Bare URLs written in prose may be followed by punctuation like
    ``.``/``,``/``;`` that is not part of the URL.  Parentheses and brackets
    are trickier: a URL like
    ``https://en.wikipedia.org/wiki/Entropy_(information_theory)`` ends with
    a ``)`` that IS part of the URL.  We preserve parens whenever they are
    balanced inside the URL.
    """
    url = raw
    while url and url[-1] in ".,;!":
        url = url[:-1]
    # Strip trailing ')' or ']' only when unbalanced (surplus closers).
    while url and url[-1] in ")]":
        opener = "(" if url[-1] == ")" else "["
        closer = url[-1]
        if url.count(opener) < url.count(closer):
            url = url[:-1]
        else:
            break
    return url


def collect_urls() -> dict[str, list[str]]:
    """Map URL -> list of 'file:line' locations (for reporting)."""
    url_sources: dict[str, list[str]] = {}
    md_dir = REPO_ROOT / "use-cases"
    for path in sorted(md_dir.glob("cat-*.md")):
        lines = path.read_text(encoding="utf-8").splitlines()
        for lineno, line in enumerate(lines, start=1):
            m = REFERENCES_LINE.match(line)
            if not m:
                continue
            tail = m.group(1)
            for raw in URL_PATTERN.findall(tail):
                url = normalize_url(raw)
                if not url.startswith(("http://", "https://")):
                    continue
                loc = f"{path.relative_to(REPO_ROOT)}:{lineno}"
                url_sources.setdefault(url, []).append(loc)
    return url_sources


def _head_code(url: str) -> int:
    req = urllib.request.Request(
        url, headers={"User-Agent": BROWSER_UA}, method="HEAD",
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as resp:
        return resp.getcode()


def _get_code(url: str) -> int:
    req = urllib.request.Request(
        url, headers={"User-Agent": BROWSER_UA}, method="GET",
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as resp:
        code = resp.getcode()
        try:
            resp.read(65536)
        except (OSError, ValueError, urllib.error.HTTPError):
            pass
        return code


def _finish_with_get(url: str, head_detail: str) -> tuple[bool, str]:
    try:
        code = _get_code(url)
        ok = code < 400
        return ok, f"GET {code} ({head_detail})"
    except urllib.error.HTTPError as ge:
        return False, f"GET {ge.code} ({head_detail})"
    except urllib.error.URLError as ge:
        return False, f"GET {ge.reason!s} ({head_detail})"


def _probe_once(url: str) -> tuple[bool, str, int | None]:
    """One round of HEAD → optional GET probing. Returns (ok, detail, code)."""
    try:
        code = _head_code(url)
    except urllib.error.HTTPError as e:
        if e.code in HEAD_FALLBACK_CODES:
            ok, det = _finish_with_get(url, f"HEAD {e.code}")
            return ok, det, e.code
        return e.code < 400, f"HEAD {e.code}", e.code
    except urllib.error.URLError as e:
        ok, det = _finish_with_get(url, f"HEAD {e.reason!s}")
        return ok, det, None

    if code < 400:
        return True, f"HEAD {code}", code
    if code in HEAD_FALLBACK_CODES:
        ok, det = _finish_with_get(url, f"HEAD {code}")
        return ok, det, code
    return False, f"HEAD {code}", code


def check_url(url: str) -> tuple[bool, str]:
    """Return (ok, detail). Retries once on 429/503 with exponential backoff."""
    ok, detail, code = _probe_once(url)
    if not ok and code in RATE_LIMIT_CODES:
        time.sleep(RETRY_AFTER_DEFAULT)
        ok2, detail2, _ = _probe_once(url)
        return ok2, f"{detail2} after retry"
    return ok, detail


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit http(s) links on References lines in use-cases/cat-*.md.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List unique URLs only; do not perform HTTP checks.",
    )
    args = parser.parse_args()

    url_sources = collect_urls()
    all_urls = sorted(url_sources.keys())

    if not all_urls:
        print("No URLs found on - **References:** lines.", file=sys.stderr)
        return 0

    ignore_patterns = load_ignore_patterns()

    def is_ignored(u: str) -> bool:
        return any(p.search(u) for p in ignore_patterns)

    urls = [u for u in all_urls if not is_ignored(u)]
    ignored = [u for u in all_urls if is_ignored(u)]

    if args.dry_run:
        print(f"Dry run: {len(urls)} unique URL(s), {len(ignored)} ignored\n")
        for u in urls:
            print(u)
        print(f"\nTotal unique URLs: {len(urls)}  (ignored: {len(ignored)})")
        return 0

    # Group URLs by host so we can throttle requests within each host while
    # still processing different hosts concurrently.
    by_host: dict[str, list[str]] = {}
    for u in urls:
        host = urlsplit(u).netloc.lower()
        by_host.setdefault(host, []).append(u)

    def check_host(host_urls: list[str]) -> list[tuple[str, tuple[bool, str]]]:
        out: list[tuple[str, tuple[bool, str]]] = []
        for i, u in enumerate(host_urls):
            if i:
                time.sleep(PER_HOST_DELAY_SEC)
            try:
                out.append((u, check_url(u)))
            except Exception as e:  # noqa: BLE001
                out.append((u, (False, repr(e))))
        return out

    results: dict[str, tuple[bool, str]] = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = {
            ex.submit(check_host, host_urls): host
            for host, host_urls in by_host.items()
        }
        for fut in as_completed(futs):
            for url, outcome in fut.result():
                results[url] = outcome

    broken: list[str] = []
    ok_count = 0
    for u in urls:
        good, detail = results[u]
        if good:
            ok_count += 1
        else:
            broken.append(u)
            for loc in url_sources[u]:
                print(f"BROKEN [{detail}] {u}", file=sys.stderr)
                print(f"  -> {loc}", file=sys.stderr)

    total = len(urls)
    bad_count = len(broken)
    print()
    print("Summary")
    print("-------")
    print(f"  URLs checked (unique): {total}")
    print(f"  OK:                    {ok_count}")
    print(f"  Broken:                {bad_count}")
    print(f"  Ignored (fragile):     {len(ignored)}")

    return 1 if bad_count else 0


if __name__ == "__main__":
    sys.exit(main())
