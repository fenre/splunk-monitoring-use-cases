#!/usr/bin/env python3
"""Manual audit: check http(s) URLs on - **References:** lines in use-cases/cat-*.md."""

from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REFERENCES_LINE = re.compile(r"^\s*-\s*\*\*References:\*\*\s*(.*)$")
URL_PATTERN = re.compile(r"https?://[^\s,<>]+")
BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
HEAD_FALLBACK_CODES = frozenset({400, 403, 405, 501})
TIMEOUT_SEC = 10
MAX_WORKERS = 10


def normalize_url(raw: str) -> str:
    return raw.rstrip(").;,]")


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


def check_url(url: str) -> tuple[bool, str]:
    """Return (ok, detail). detail is status code or error message."""

    def head_code() -> int:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as resp:
            return resp.getcode()

    def get_code() -> int:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": BROWSER_UA},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as resp:
            code = resp.getcode()
            # Avoid pulling entire body on large pages; enough to complete handshake.
            try:
                resp.read(65536)
            except (OSError, ValueError, urllib.error.HTTPError):
                pass
            return code

    def finish_with_get(head_detail: str) -> tuple[bool, str]:
        try:
            code = get_code()
            if code >= 400:
                return False, f"GET {code} ({head_detail})"
            return True, f"GET {code} ({head_detail})"
        except urllib.error.HTTPError as ge:
            return False, f"GET {ge.code} ({head_detail})"
        except urllib.error.URLError as ge:
            return False, f"GET {ge.reason!s} ({head_detail})"

    try:
        code = head_code()
        if code < 400:
            return True, f"HEAD {code}"
        if code in HEAD_FALLBACK_CODES:
            return finish_with_get(f"HEAD {code}")
        return False, f"HEAD {code}"
    except urllib.error.HTTPError as e:
        if e.code in HEAD_FALLBACK_CODES:
            return finish_with_get(f"HEAD {e.code}")
        if e.code >= 400:
            return False, f"HEAD {e.code}"
        return True, f"HEAD {e.code}"
    except urllib.error.URLError as e:
        return finish_with_get(f"HEAD {e.reason!s}")


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
    urls = sorted(url_sources.keys())

    if not urls:
        print("No URLs found on - **References:** lines.", file=sys.stderr)
        return 0

    if args.dry_run:
        print(f"Dry run: {len(urls)} unique URL(s)\n")
        for u in urls:
            print(u)
        print(f"\nTotal unique URLs: {len(urls)}")
        return 0

    results: dict[str, tuple[bool, str]] = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = {ex.submit(check_url, u): u for u in urls}
        for fut in as_completed(futs):
            u = futs[fut]
            try:
                results[u] = fut.result()
            except Exception as e:  # noqa: BLE001 — surface unexpected failures
                results[u] = (False, repr(e))

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

    return 1 if bad_count else 0


if __name__ == "__main__":
    sys.exit(main())
