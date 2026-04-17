#!/usr/bin/env python3
"""Extract a release-notes body from ``CHANGELOG.md`` for a given version.

Usage:
    python3 scripts/extract_release_notes.py <version>       # writes to stdout
    python3 scripts/extract_release_notes.py <version> out.md

- <version> must match the ``## [x.y.z]`` heading in CHANGELOG.md exactly
  (without the square brackets).
- If the version heading is not found the script writes a minimal
  fall-back body so the release workflow never fails "empty".
- The extracted section is appended with a boilerplate paragraph that
  lists the three content packs produced by the release workflow; this
  keeps GitHub Release pages self-contained.

The script is side-effect-free (apart from writing the target file) and
safe to re-run any number of times.
"""

from __future__ import annotations

import os
import re
import sys
from typing import Optional

CHANGELOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "CHANGELOG.md")

BOILERPLATE = """

## Splunk content packs

This release ships three self-contained Splunk apps:

- `TA-splunk-use-cases-{ver}.spl` — Quick-Start saved searches for the Splunk search head.
- `DA-ITSI-monitoring-use-cases-{ver}.spl` — KPI base searches, thresholds and service templates for Splunk ITSI.
- `DA-ESS-monitoring-use-cases-{ver}.spl` — Correlation searches, MITRE mappings and analytic stories for Splunk Enterprise Security.

See `SHA256SUMS.txt` for integrity verification, and the
[Enterprise deployment guide](docs/enterprise-deployment.md) for installation
instructions and upgrade paths.
"""


def extract_section(version: str) -> Optional[str]:
    try:
        with open(CHANGELOG, "r", encoding="utf-8") as fh:
            src = fh.read()
    except FileNotFoundError:
        return None
    # Match "## [VER] ..." up to the next "## [" header (or EOF).
    pattern = re.compile(
        rf"(^##\s+\[{re.escape(version)}\][^\n]*\n)(?P<body>.+?)(?=^##\s+\[|\Z)",
        re.M | re.S,
    )
    m = pattern.search(src)
    if not m:
        return None
    return m.group("body").rstrip() + "\n"


def build_body(version: str) -> str:
    section = extract_section(version)
    if section is None:
        section = (
            f"## {version}\n\n"
            "Release notes are documented in [CHANGELOG.md](CHANGELOG.md).\n"
        )
    return section + BOILERPLATE.format(ver=version)


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: extract_release_notes.py <version> [output]", file=sys.stderr)
        return 2
    version = argv[0]
    body = build_body(version)
    if len(argv) > 1:
        out = argv[1]
        os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(body)
        print(f"wrote {out} ({len(body)} chars)")
    else:
        sys.stdout.write(body)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
