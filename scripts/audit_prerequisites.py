#!/usr/bin/env python3
"""Audit the implementation-ordering graph encoded in catalog.json.

This is the CI-side enforcement gate that complements the in-build
validator in ``build.py::validate_prerequisites``.  Where the build
script reads parsed UC structures in memory and warns on graph shape,
this audit reads the *committed* ``catalog.json`` artefact directly so
that:

* Hand-edits to ``catalog.json`` (which should never happen, but do)
  are caught even if the catalogue was not regenerated.
* Reviewers can download a deterministic JSON report from CI artifacts
  without having to re-run ``build.py`` locally.
* Cycle / unknown-id / wave-monotonicity invariants are enforced as
  hard CI failures, with deterministic ordering so the same broken
  catalogue produces the same diff every time.

Hard failures (exit 1):
  * Unknown prerequisite id (UC referenced by ``pre`` does not exist).
  * Self-reference (UC lists its own id in ``pre``).
  * Cycle in the dependency graph (Kahn's topological sort).

Warnings (exit 0 unless ``--strict``):
  * Wave monotonicity violation — a lower-tier UC (crawl) declares a
    higher-tier UC (walk/run) as a prerequisite.  This is almost
    always an authoring error (the wave column was inverted) but the
    repository has historical fields where curators may have meant
    something more nuanced, so we warn first and let humans decide.

Output:
  * Always prints a one-line ``Waves:`` summary so CI logs are
    spot-checkable at a glance.
  * Optionally writes ``reports/prerequisites-audit.json`` with the
    fully-resolved dependency graph (forward + reverse), the wave
    distribution, and any errors / warnings.  ``--check`` regenerates
    this report into memory and diffs it against the committed file
    so hand-edits or forgotten regenerations fail CI.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG_PATH = os.path.join(REPO_ROOT, "catalog.json")
REPORT_PATH = os.path.join(REPO_ROOT, "reports", "prerequisites-audit.json")

UC_ID_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
PREREQ_UC_PATTERN = re.compile(r"^UC-\d+\.\d+\.\d+$")
VALID_WAVES = ("crawl", "walk", "run")
WAVE_RANK = {"crawl": 0, "walk": 1, "run": 2}


def _load_catalog() -> Dict[str, Any]:
    if not os.path.isfile(CATALOG_PATH):
        print(f"ERROR: catalog.json not found at {CATALOG_PATH}", file=sys.stderr)
        sys.exit(2)
    with open(CATALOG_PATH, encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            print(f"ERROR: catalog.json is not valid JSON: {e}", file=sys.stderr)
            sys.exit(2)


def _extract_uc_index(root: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Build a deterministic ``UC-X.Y.Z`` -> uc dict index from catalog DATA."""
    index: Dict[str, Dict[str, Any]] = {}
    data = root.get("DATA")
    if not isinstance(data, list):
        return index
    for cat in data:
        if not isinstance(cat, dict):
            continue
        for sub in cat.get("s", []) or []:
            if not isinstance(sub, dict):
                continue
            for uc in sub.get("u", []) or []:
                if not isinstance(uc, dict):
                    continue
                uid = uc.get("i")
                if not isinstance(uid, str) or not UC_ID_PATTERN.match(uid):
                    continue
                full = "UC-" + uid
                index[full] = uc
    return index


def _detect_cycle(adjacency: Dict[str, List[str]]) -> Optional[List[str]]:
    """Return a concrete cycle path or None.

    Edge direction: ``A -> B`` means A must complete before B (i.e. A is
    a prerequisite of B).  Implemented as iterative DFS with a coloured
    visit map (white=0, grey=1, black=2) to keep determinism without
    blowing the recursion stack.
    """
    WHITE, GREY, BLACK = 0, 1, 2
    color = {n: WHITE for n in adjacency}
    parent: Dict[str, Optional[str]] = {n: None for n in adjacency}

    def walk_back(stop: str, start: str) -> List[str]:
        path = [start]
        cursor: Optional[str] = parent[start]
        while cursor is not None and cursor != stop:
            path.append(cursor)
            cursor = parent[cursor]
        path.append(stop)
        path.reverse()
        path.append(start)
        return path

    for root in sorted(adjacency.keys()):
        if color[root] != WHITE:
            continue
        stack: List[Tuple[str, int]] = [(root, 0)]
        parent[root] = None
        color[root] = GREY
        while stack:
            node, idx = stack[-1]
            neighbours = adjacency[node]
            if idx < len(neighbours):
                nxt = neighbours[idx]
                stack[-1] = (node, idx + 1)
                if color.get(nxt, WHITE) == GREY:
                    return walk_back(nxt, node)
                if color.get(nxt, WHITE) == WHITE:
                    parent[nxt] = node
                    color[nxt] = GREY
                    stack.append((nxt, 0))
            else:
                color[node] = BLACK
                stack.pop()
    return None


def _build_graph(
    uc_index: Dict[str, Dict[str, Any]],
) -> Tuple[Dict[str, List[str]], Dict[str, List[str]], List[str], List[str]]:
    """Return forward (prereq->dependant) graph, reverse index, errors, warnings.

    Errors and warnings are returned as deterministic, pre-sorted lists
    so the JSON report is byte-stable across runs.
    """
    errors: List[str] = []
    warnings: List[str] = []
    forward: Dict[str, List[str]] = {uid: [] for uid in uc_index}
    reverse: Dict[str, List[str]] = {uid: [] for uid in uc_index}

    for uid in sorted(uc_index.keys()):
        uc = uc_index[uid]
        pre = uc.get("pre")
        if not isinstance(pre, list) or not pre:
            continue
        seen_in_uc: set[str] = set()
        for pi, dep in enumerate(pre):
            if not isinstance(dep, str):
                errors.append(
                    f"shape: {uid} pre[{pi}] is not a string ({type(dep).__name__})"
                )
                continue
            if not PREREQ_UC_PATTERN.match(dep):
                errors.append(
                    f"shape: {uid} pre[{pi}]={dep!r} does not match UC-X.Y.Z pattern"
                )
                continue
            if dep == uid:
                errors.append(f"self-reference: {uid} lists itself as a prerequisite")
                continue
            if dep in seen_in_uc:
                errors.append(f"duplicate-prereq: {uid} lists {dep} more than once")
                continue
            seen_in_uc.add(dep)
            if dep not in uc_index:
                errors.append(
                    f"unknown-prereq: {uid} references {dep} which does not exist"
                )
                continue
            if dep not in forward[dep]:
                forward[dep].append(uid)
            reverse[uid].append(dep)
            src_wave = uc.get("wv")
            dep_wave = uc_index[dep].get("wv")
            if (
                isinstance(src_wave, str)
                and isinstance(dep_wave, str)
                and src_wave in WAVE_RANK
                and dep_wave in WAVE_RANK
                and WAVE_RANK[dep_wave] > WAVE_RANK[src_wave]
            ):
                warnings.append(
                    "wave-monotonicity: "
                    f"{uid} (wave={src_wave}) depends on {dep} (wave={dep_wave}) — "
                    "a lower tier cannot depend on a higher one"
                )

    for uid in forward:
        forward[uid] = sorted(set(forward[uid]))
    for uid in reverse:
        reverse[uid] = sorted(set(reverse[uid]))

    errors.sort()
    warnings.sort()
    return forward, reverse, errors, warnings


def _wave_summary(uc_index: Dict[str, Dict[str, Any]]) -> Dict[str, int]:
    counts = {w: 0 for w in VALID_WAVES}
    counts["unassigned"] = 0
    for uc in uc_index.values():
        w = uc.get("wv")
        if isinstance(w, str) and w in counts:
            counts[w] += 1
        else:
            counts["unassigned"] += 1
    return counts


def _build_report(
    uc_index: Dict[str, Dict[str, Any]],
    forward: Dict[str, List[str]],
    reverse: Dict[str, List[str]],
    errors: List[str],
    warnings: List[str],
) -> Dict[str, Any]:
    cycle = None
    forward_with_self: Dict[str, List[str]] = {uid: list(forward.get(uid, [])) for uid in uc_index}
    cycle_path = _detect_cycle(forward_with_self)
    if cycle_path:
        cycle = cycle_path

    edges: List[List[str]] = []
    for uid in sorted(forward.keys()):
        for tgt in forward[uid]:
            edges.append([uid, tgt])

    waves: Dict[str, List[str]] = {w: [] for w in VALID_WAVES}
    waves["unassigned"] = []
    for uid in sorted(uc_index.keys()):
        w = uc_index[uid].get("wv")
        bucket = w if isinstance(w, str) and w in waves else "unassigned"
        waves[bucket].append(uid)

    report: Dict[str, Any] = {
        "_readme": (
            "Audit of the UC implementation-ordering graph encoded in "
            "catalog.json. Edges point from a prerequisite UC to the UC "
            "that depends on it. Regenerate with "
            "scripts/audit_prerequisites.py; CI guards drift via --check."
        ),
        "summary": {
            "ucs_with_prerequisites": sum(1 for v in reverse.values() if v),
            "ucs_with_dependants": sum(1 for v in forward.values() if v),
            "edges": len(edges),
            "wave_counts": _wave_summary(uc_index),
        },
        "waves": waves,
        "edges": edges,
        "reverseIndex": {uid: forward[uid] for uid in sorted(forward) if forward[uid]},
        "errors": errors,
        "warnings": warnings,
    }
    if cycle:
        report["cycle"] = cycle
    return report


def _serialise(report: Dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _read_existing_report() -> Optional[str]:
    if not os.path.isfile(REPORT_PATH):
        return None
    with open(REPORT_PATH, encoding="utf-8") as f:
        return f.read()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit catalog.json prerequisite graph (cycles, unknown ids, monotonicity)."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "Regenerate the report in memory and diff against "
            "reports/prerequisites-audit.json. Exits non-zero on drift. "
            "Use this in CI."
        ),
    )
    parser.add_argument(
        "--write-report",
        action="store_true",
        help=(
            "Write reports/prerequisites-audit.json with the resolved graph. "
            "Implied by --check (the diff target needs a baseline)."
        ),
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat wave-monotonicity warnings as hard errors.",
    )
    args = parser.parse_args()

    catalog = _load_catalog()
    uc_index = _extract_uc_index(catalog)
    forward, reverse, errors, warnings = _build_graph(uc_index)
    report = _build_report(uc_index, forward, reverse, errors, warnings)

    cycle = report.get("cycle")
    if cycle:
        errors = list(errors)
        errors.append("cycle: " + " -> ".join(cycle))
        errors.sort()
        report["errors"] = errors

    summary = report["summary"]["wave_counts"]
    print(
        "  Waves: crawl={crawl}, walk={walk}, run={run}, unassigned={unassigned}".format(
            **summary
        )
    )
    print(
        "  Graph: {ucs_with_prereqs} UC(s) with prerequisites, "
        "{ucs_with_deps} UC(s) enable others, {edges} edge(s).".format(
            ucs_with_prereqs=report["summary"]["ucs_with_prerequisites"],
            ucs_with_deps=report["summary"]["ucs_with_dependants"],
            edges=report["summary"]["edges"],
        )
    )

    for w in warnings:
        print(f"  WARN  {w}")
    for e in errors:
        print(f"  ERROR {e}", file=sys.stderr)

    serialised = _serialise(report)

    if args.check:
        existing = _read_existing_report()
        if existing is None:
            print(
                f"ERROR: --check requires {REPORT_PATH} to exist. "
                "Run scripts/audit_prerequisites.py --write-report and commit it.",
                file=sys.stderr,
            )
            return 1
        if existing != serialised:
            print(
                f"ERROR: {REPORT_PATH} is out of date — re-run "
                "scripts/audit_prerequisites.py --write-report and commit the result.",
                file=sys.stderr,
            )
            return 1

    if args.write_report:
        os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
        with open(REPORT_PATH, "w", encoding="utf-8") as f:
            f.write(serialised)
        print(f"  Wrote {os.path.relpath(REPORT_PATH, REPO_ROOT)}")

    if errors:
        print(
            f"Prerequisite audit failed with {len(errors)} error(s).",
            file=sys.stderr,
        )
        return 1
    if args.strict and warnings:
        print(
            f"Prerequisite audit failed with {len(warnings)} warning(s) under --strict.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
