#!/usr/bin/env python3
"""Fail when a use case's search is the ESCU risk drill-down.

ESCU ships two searches per detection: the detection itself and a
"view risk events for $token$" drill-down that reads the Risk data model
for one dashboard token. The drill-down detects nothing on its own, so a
use case whose ``spl`` (or ``cimSpl`` / ``splVariants[].spl`` /
``splVariants[].cimSpl``) is that drill-down has no working search.

``data/escu-drilldown-backlog.json`` lists the use cases that still
carry the drill-down because ``splunk/security_content`` has no
detection with the same name. The list may only shrink: ``--check``
fails on a hit that is not listed and on a listed use case that no
longer has the drill-down.

Run::

    PYTHONPATH=src python3 -m splunk_uc audit-escu-drilldown-spl
    PYTHONPATH=src python3 -m splunk_uc audit-escu-drilldown-spl --check
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from splunk_uc.audits._uc_walk import REPO, iter_uc_sidecars

BACKLOG = REPO / "data" / "escu-drilldown-backlog.json"

DRILLDOWN_RE = re.compile(
    r"from\s+datamodel\s*=?\s*Risk\.All_Risk\s*\|\s*search\s+normalized_risk_object\s+IN\b",
    re.IGNORECASE,
)


def _searches(uc: dict[str, Any]) -> Iterable[tuple[str, str]]:
    for key in ("spl", "cimSpl"):
        value = uc.get(key)
        if isinstance(value, str):
            yield key, value
    for i, variant in enumerate(uc.get("splVariants") or []):
        if not isinstance(variant, dict):
            continue
        for key in ("spl", "cimSpl"):
            value = variant.get(key)
            if isinstance(value, str):
                yield f"splVariants[{i}].{key}", value


def drilldown_fields(uc: dict[str, Any]) -> list[str]:
    """Fields of one use case whose search is the ESCU risk drill-down."""
    return [field for field, text in _searches(uc) if DRILLDOWN_RE.search(text)]


def collect() -> dict[str, list[str]]:
    hits: dict[str, list[str]] = {}
    for _path, uc in iter_uc_sidecars():
        fields = drilldown_fields(uc)
        if fields:
            hits[f"UC-{uc.get('id')}"] = fields
    return hits


def load_backlog(path: Path = BACKLOG) -> set[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {entry["id"] for entry in data.get("useCases", [])}


def compare(hits: dict[str, list[str]], backlog: set[str]) -> tuple[list[str], list[str]]:
    """Return (new hits not in the backlog, backlog entries that no longer hit)."""
    new = sorted(uc for uc in hits if uc not in backlog)
    stale = sorted(uc for uc in backlog if uc not in hits)
    return new, stale


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="Exit 1 on unlisted or stale entries.")
    args = parser.parse_args(argv)

    hits = collect()
    backlog = load_backlog()
    new, stale = compare(hits, backlog)

    print(f"ESCU drill-down searches: {len(hits)} use cases ({len(backlog)} in backlog)")
    for uc in new:
        print(f"  NEW   {uc}: {', '.join(hits[uc])}")
    for uc in stale:
        print(f"  STALE {uc}: no longer a drill-down; remove it from {BACKLOG.relative_to(REPO)}")

    if args.check and (new or stale):
        print(
            "FAIL: replace the drill-down with the ESCU detection search, "
            "or write a real search for the use case."
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
