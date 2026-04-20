#!/usr/bin/env python3
"""tools.audits.url_freeze — fail CI when a public URL disappears.

Reads the previous release's ``dist/manifest.json`` (fetched from the
``baseline`` git ref) and compares it to the current build's
``dist/api/manifest.json``. Any URL that was present in the baseline and
is missing in HEAD fails the audit.

Usage
-----
    python3 tools/audits/url_freeze.py \\
        --baseline-tag v7.0.0 \\
        --head dist/api/manifest.json

Exit codes
----------
0 — no removals
1 — at least one URL was removed (lists them on stderr)
2 — invocation error (e.g., baseline tag not found)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Iterable


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="url_freeze")
    parser.add_argument(
        "--baseline-tag",
        required=True,
        help="git tag of the previous release whose manifest sets the contract.",
    )
    parser.add_argument(
        "--baseline-path",
        default="dist/api/manifest.json",
        help="Path within the baseline tag's tree (default: dist/api/manifest.json).",
    )
    parser.add_argument(
        "--head",
        default="dist/api/manifest.json",
        help="Path to the freshly-built manifest (default: dist/api/manifest.json).",
    )
    args = parser.parse_args(argv)

    head_path = Path(args.head)
    if not head_path.exists():
        sys.stderr.write(f"[url_freeze] missing HEAD manifest: {head_path}\n")
        return 2

    baseline = _load_baseline(args.baseline_tag, args.baseline_path)
    if baseline is None:
        sys.stderr.write(
            f"[url_freeze] baseline tag {args.baseline_tag} has no "
            f"{args.baseline_path}; treating as first-release allowlist.\n"
        )
        return 0

    head = json.loads(head_path.read_text(encoding="utf-8"))
    baseline_urls = _extract_urls(baseline)
    head_urls = _extract_urls(head)

    removed = sorted(baseline_urls - head_urls)
    if not removed:
        sys.stdout.write(
            f"[url_freeze] OK ({len(head_urls)} URLs, "
            f"+{len(head_urls - baseline_urls)} new since {args.baseline_tag})\n"
        )
        return 0

    sys.stderr.write(
        f"[url_freeze] FAIL: {len(removed)} URL(s) removed since {args.baseline_tag}\n"
    )
    for url in removed[:50]:
        sys.stderr.write(f"  - {url}\n")
    if len(removed) > 50:
        sys.stderr.write(f"  ... and {len(removed) - 50} more\n")
    sys.stderr.write(
        "\n"
        "Once published, public URLs are permanent (see docs/url-scheme.md).\n"
        "If the removal is intentional, file an RFC under docs/governance.md\n"
        "and follow the deprecation process in docs/api-versioning.md.\n"
    )
    return 1


def _load_baseline(tag: str, path: str) -> dict | None:
    try:
        out = subprocess.check_output(
            ["git", "show", f"{tag}:{path}"],
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return None


def _extract_urls(manifest: dict) -> set[str]:
    urls: set[str] = set()
    paths = manifest.get("paths", {})
    for group in paths.values():
        if not isinstance(group, list):
            continue
        for entry in group:
            if not isinstance(entry, dict):
                continue
            for key in ("html", "json", "url", "path"):
                v = entry.get(key)
                if isinstance(v, str):
                    urls.add(v)
    return urls


def _walk(value, into: Iterable[str]) -> set[str]:
    out: set[str] = set()
    if isinstance(value, dict):
        for v in value.values():
            out |= _walk(v, into)
    elif isinstance(value, list):
        for v in value:
            out |= _walk(v, into)
    elif isinstance(value, str):
        if value.startswith("/"):
            out.add(value)
    return out


if __name__ == "__main__":
    sys.exit(main())
