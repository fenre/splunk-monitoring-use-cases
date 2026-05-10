#!/usr/bin/env python3
"""Surface near-duplicate SPL queries across the JSON SSOT.

This is an **informational** linter — it never exits non-zero and is
not wired into the CI gate. Its job is to flag UCs whose ``spl`` field
is byte-for-byte identical after normalisation (whitespace collapse +
macro-argument masking). These clusters warrant a closer look: the UCs
may be legitimately related, but more often they are symptoms of an
over-zealous ESCU mirror where the detection query was replaced by a
generic ``from datamodel Risk.All_Risk`` stub.

Pre-v8.2.0 this audit walked ``use-cases/cat-*.md``. The legacy
markdown corpus has been deleted; the JSON SSOT is the only place SPL
lives now.

Output
------
Clusters of 2+ UCs that share the same canonical SPL, sorted by cluster
size descending. Only the top 30 clusters are printed by default.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from collections import defaultdict

from splunk_uc.audits._uc_walk import iter_uc_sidecars

RE_WS = re.compile(r"\s+")
RE_MACRO_ARGS = re.compile(r"`([a-z_]+)\([^)]*\)`")


def _canonical_spl(spl: str) -> str:
    """Normalise SPL to a stable, hashable form.

    * Collapse all whitespace to single spaces.
    * Mask macro arguments (`foo(bar,baz)` → `foo(..)`).
    * Lowercase the result — SPL keywords are case-insensitive.
    """
    text = RE_MACRO_ARGS.sub(r"`\1(..)`", spl)
    text = RE_WS.sub(" ", text).strip().lower()
    return text


def _collect() -> dict[str, list[tuple[str, str, str]]]:
    clusters: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for path, payload in iter_uc_sidecars():
        spl = payload.get("spl")
        if not isinstance(spl, str) or not spl.strip():
            continue
        uc_id = f"UC-{payload.get('id', '<unknown>')}"
        title = str(payload.get("title", "")).strip() or "(no title)"
        canonical = _canonical_spl(spl)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]
        clusters[digest].append((path.name, uc_id, title))
    return clusters


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)

    clusters = _collect()
    dup_clusters = {h: members for h, members in clusters.items() if len(members) > 1}

    total_ucs = sum(len(m) for m in clusters.values())
    dup_ucs = sum(len(m) for m in dup_clusters.values())
    unique_clusters = len(dup_clusters)

    print("=" * 72)
    print("SPL duplicate audit (informational)")
    print("=" * 72)
    print(f"UCs with SPL:           {total_ucs}")
    print(f"UCs in a dup cluster:   {dup_ucs}")
    print(f"Distinct dup clusters:  {unique_clusters}")

    if not dup_clusters:
        print("\nNo duplicate SPL clusters found.")
        return 0

    sorted_clusters = sorted(dup_clusters.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    print("\nTop clusters (size, first 5 UCs):")
    print("-" * 72)
    for digest, members in sorted_clusters[:30]:
        print(f"[{digest}] size={len(members)}")
        for file, uc_id, title in members[:5]:
            print(f"    {uc_id} ({file}) — {title}")
        if len(members) > 5:
            print(f"    ... and {len(members) - 5} more")
    if len(sorted_clusters) > 30:
        print(f"\n... and {len(sorted_clusters) - 30} more clusters.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
