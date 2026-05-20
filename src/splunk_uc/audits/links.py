#!/usr/bin/env python3
"""Audit ``references[].url`` URLs across the JSON SSOT.

Pre-v8.2.0 this audit walked References lines in
``use-cases/cat-*.md``. The legacy markdown corpus has been deleted;
references now live in the ``references`` array on every UC sidecar
under ``content/cat-*/UC-*.json``.
"""

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

from splunk_uc.audits._uc_walk import iter_uc_sidecars

REPO_ROOT = Path(__file__).resolve().parents[3]
# URL_PATTERN intentionally excludes characters that almost never appear
# inside a real URL but do appear as adjacent markdown / JSON / code-fence
# decoration in the catalogue's prose fields:
#
#   * whitespace (any) — natural URL terminator
#   * ``,``  — comma between URLs in a list
#   * ``<``  — angle-bracketed reference (``<https://x>``)
#   * ``>``  — closing angle bracket of the same
#   * `` ` `` — inline-code-fence backtick (``\`https://x\```)
#   * ``{`` / ``}`` — templated value placeholder
#     (``https://{host}/path``) — we deliberately strip these here so a
#     loose ``}`` next to a real URL doesn't pull into the match
#   * ``"`` / ``'`` — JSON-embedded URL (``{"url": "https://x"}``)
#   * ``\`` — escape character in JSON strings (``https://x\n``)
#
# Conservative trailing-punctuation cleanup still happens in
# ``normalize_url`` so e.g. ``http://x/y.``  →  ``http://x/y``.
URL_PATTERN = re.compile(r"https?://[^\s,<>`{}\"'\\]+")
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
    """Strip trailing decoration while preserving balanced parentheses.

    Bare URLs written in prose may be followed by punctuation like
    ``.`` / ``,`` / ``;`` / ``!`` that is not part of the URL, or by
    markdown / JSON / code-fence decoration like ``\\```, ``"``, ``'``,
    ``}``, ``\\``. We strip both classes here as a defence in depth on
    top of the regex (``URL_PATTERN``) — the regex already excludes
    most of these, but some sneak in through ``references[].url``
    fields where authors hand-paste a URL with adjacent quoting.

    Parentheses and brackets are trickier: a URL like
    ``https://en.wikipedia.org/wiki/Entropy_(information_theory)`` ends
    with a ``)`` that IS part of the URL. We preserve parens / brackets
    whenever they are balanced inside the URL, and strip them only
    when unbalanced (surplus closers).
    """

    url = raw

    # 1. Strip sentence punctuation and markdown / JSON / code-fence
    #    decoration that never belongs in a URL. Loop because the
    #    catalogue carries chains like ``http://x/y\`.,;!``.
    decoration = ".,;!`\"'}\\"
    while url and url[-1] in decoration:
        url = url[:-1]

    # 2. Strip trailing ')' or ']' only when unbalanced (surplus
    #    closers). Wikipedia URLs are the canonical preservation case.
    while url and url[-1] in ")]":
        opener = "(" if url[-1] == ")" else "["
        closer = url[-1]
        if url.count(opener) < url.count(closer):
            url = url[:-1]
        else:
            break

    return url


def collect_urls() -> dict[str, list[str]]:
    """Map URL -> list of UC locations (for reporting).

    Walks every UC sidecar in the JSON SSOT and harvests URLs from:

    * ``references[].url`` (canonical)
    * any ``http(s)://`` URL embedded in the prose fields
      ``description``, ``value``, ``implementation``,
      ``detailedImplementation``, ``dataSources``, ``app``.
    """
    url_sources: dict[str, list[str]] = {}
    prose_fields = (
        "description",
        "value",
        "implementation",
        "detailedImplementation",
        "dataSources",
        "app",
    )
    for path, payload in iter_uc_sidecars():
        rel = path.relative_to(REPO_ROOT)
        uc_id = f"UC-{payload.get('id', '<unknown>')}"
        loc = f"{rel} ({uc_id})"

        refs = payload.get("references")
        if isinstance(refs, list):
            for entry in refs:
                if not isinstance(entry, dict):
                    continue
                url = entry.get("url")
                if isinstance(url, str):
                    url = normalize_url(url.strip())
                    if url.startswith(("http://", "https://")):
                        url_sources.setdefault(url, []).append(loc)

        for field in prose_fields:
            v = payload.get(field)
            if not isinstance(v, str):
                continue
            for raw in URL_PATTERN.findall(v):
                url = normalize_url(raw)
                if url.startswith(("http://", "https://")):
                    url_sources.setdefault(url, []).append(loc)

    return url_sources


def _head_code(url: str) -> int:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": BROWSER_UA},
        method="HEAD",
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as resp:
        code: int = resp.getcode()
        return code


def _get_code(url: str) -> int:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": BROWSER_UA},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as resp:
        code: int = resp.getcode()
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Audit http(s) URLs in references[].url and prose fields "
            "across content/cat-*/UC-*.json."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List unique URLs only; do not perform HTTP checks.",
    )
    args = parser.parse_args(argv)

    url_sources = collect_urls()
    all_urls = sorted(url_sources.keys())

    if not all_urls:
        print(
            "No URLs found on references[].url or in UC prose.",
            file=sys.stderr,
        )
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
    #
    # ``urlsplit`` raises ``ValueError`` for malformed URLs (the catalogue
    # has historically carried placeholder literals like
    # ``https://[server]:[port]/...`` that Python rejects as bad IPv6).
    # A single bad URL must not abort the entire audit — warn and drop
    # from BOTH ``by_host`` (so we don't probe it) and ``urls`` (so the
    # downstream report loop doesn't ``KeyError`` looking it up).
    by_host: dict[str, list[str]] = {}
    malformed: list[tuple[str, str]] = []
    for u in urls:
        try:
            host = urlsplit(u).netloc.lower()
        except ValueError as exc:
            malformed.append((u, str(exc)))
            continue
        by_host.setdefault(host, []).append(u)
    if malformed:
        print(
            f"WARN: skipped {len(malformed)} malformed URL(s) "
            "that ``urlsplit`` rejected — first 5 shown:",
            file=sys.stderr,
        )
        for u, exc in malformed[:5]:
            print(f"  - {u!r}: {exc}", file=sys.stderr)
        malformed_set = {u for u, _ in malformed}
        urls = [u for u in urls if u not in malformed_set]

    def check_host(host_urls: list[str]) -> list[tuple[str, tuple[bool, str]]]:
        out: list[tuple[str, tuple[bool, str]]] = []
        for i, u in enumerate(host_urls):
            if i:
                time.sleep(PER_HOST_DELAY_SEC)
            try:
                out.append((u, check_url(u)))
            except Exception as e:
                out.append((u, (False, repr(e))))
        return out

    results: dict[str, tuple[bool, str]] = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = {ex.submit(check_host, host_urls): host for host, host_urls in by_host.items()}
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
