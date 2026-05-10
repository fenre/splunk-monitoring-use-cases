"""Phase 0.2 — content-gap analysis for tier-1 regulatory frameworks.

P6 (scripts taxonomy, 2026-05-10) relocated this driver from
scripts/gap_analysis.py to src/splunk_uc/migrations/gap_analysis.py.
parents[3] resolves: gap_analysis.py -> migrations/ -> splunk_uc/ ->
src/ -> repo root. The legacy ``parents[1]`` chain assumed depth one
and is now wrong by two levels. The legacy shim re-exports ``main``
so any direct CLI invocation still works during the soak period.

This driver lives under ``migrations/`` because it is part of the
content-set evolution pipeline (each catalogue release runs gap
analysis to track which regulatory clauses we have / have not yet
covered). It is a reporting tool, not a schema migration: it always
exits 0 unless the upstream inventory is missing.

Correlates ``data/inventory/ucs.json`` (produced by
``scripts/inventory_ucs.py``) with ``data/regulations.draft.json`` and
emits:

* ``data/inventory/gap-analysis.json`` -- structured machine-readable report
* prints a summary table to stdout

The human-readable markdown report at ``docs/content-gap-analysis.md`` is
authored separately and references this JSON by filename and sha256.

Run:
    python -m splunk_uc inventory-ucs       # first, to refresh inventory
    python -m splunk_uc gap-analysis        # this driver

Exit 0 always (this is a reporting tool, not a validator).
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys
from collections import Counter, defaultdict
from typing import Any

REPO = pathlib.Path(__file__).resolve().parents[3]
INVENTORY = REPO / "data" / "inventory" / "ucs.json"
REGS = REPO / "data" / "regulations.draft.json"
OUT = REPO / "data" / "inventory" / "gap-analysis.json"

_NORMALISE = re.compile(r"\s+")


def norm(s: str) -> str:
    return _NORMALISE.sub(" ", s.strip().lower())


def resolve_aliases(raw_regs: list[str], alias_index: dict[str, str]) -> dict[str, Any]:
    """Return {framework_id: [raw labels that resolved to it]} plus unknowns."""
    resolved: dict[str, list[str]] = defaultdict(list)
    unknown: list[str] = []
    for r in raw_regs:
        key = norm(r)
        fid = alias_index.get(key)
        if fid:
            resolved[fid].append(r)
        else:
            unknown.append(r)
    return {"resolved": dict(resolved), "unknown": unknown}


def main(argv: list[str] | None = None) -> int:
    """Dispatcher entry-point. ``argv`` accepted for the registry contract; gap analysis takes no flags."""
    del argv
    if not INVENTORY.exists():
        sys.stderr.write(
            "ERROR: inventory missing. Run `python -m splunk_uc inventory-ucs` first.\n"
        )
        return 2
    if not REGS.exists():
        sys.stderr.write(f"ERROR: {REGS} missing.\n")
        return 2

    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    regs = json.loads(REGS.read_text(encoding="utf-8"))
    alias_index: dict[str, str] = {
        k: v for k, v in regs["aliasIndex"].items() if not k.startswith("$")
    }

    framework_by_id: dict[str, dict[str, Any]] = {f["id"]: f for f in regs["frameworks"]}

    ucs = inventory["useCases"]
    total_ucs = len(ucs)
    ucs_with_regs = [uc for uc in ucs if uc.get("regulations")]

    per_framework: dict[str, dict[str, Any]] = {
        fid: {
            "shortName": framework_by_id[fid]["shortName"],
            "name": framework_by_id[fid]["name"],
            "ucCount": 0,
            "ucIds": [],
            "commonClauseCount": len(framework_by_id[fid]["commonClauses"]),
        }
        for fid in framework_by_id
    }

    unknown_tag_counter: Counter[str] = Counter()

    for uc in ucs_with_regs:
        resolution = resolve_aliases(uc["regulations"], alias_index)
        for fid in resolution["resolved"]:
            per_framework[fid]["ucCount"] += 1
            per_framework[fid]["ucIds"].append(uc["uc_id"])
        for u in resolution["unknown"]:
            unknown_tag_counter[u] += 1

    for entry in per_framework.values():
        entry["ucIds"].sort()

    per_framework_rows: list[dict[str, Any]] = [
        {
            "id": fid,
            **entry,
        }
        for fid, entry in sorted(
            per_framework.items(),
            key=lambda kv: (-kv[1]["ucCount"], kv[1]["shortName"]),
        )
    ]
    unknown_rows: list[dict[str, Any]] = [
        {"label": label, "count": n} for label, n in unknown_tag_counter.most_common()
    ]
    gap_report: dict[str, Any] = {
        "generatedComment": "Regenerate with python -m splunk_uc gap-analysis",
        "schemaVersion": 1,
        "totalUseCases": total_ucs,
        "useCasesWithRegulationsTag": len(ucs_with_regs),
        "perFramework": per_framework_rows,
        "unknownRegulationTags": unknown_rows,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(gap_report, indent=2, ensure_ascii=False)
    OUT.write_text(payload + "\n", encoding="utf-8")
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()

    print(f"wrote {OUT.relative_to(REPO)}  sha256={digest}")
    print(f"\n{'Framework':<22}  {'UCs':>6}")
    print("-" * 30)
    for row in gap_report["perFramework"]:
        print(f"  {row['shortName']:<20}  {row['ucCount']:>6}")
    print(f"\nUnknown regulation tags ({len(gap_report['unknownRegulationTags'])}):")
    for row in gap_report["unknownRegulationTags"][:20]:
        print(f"  {row['count']:>4}  {row['label']}")
    if len(gap_report["unknownRegulationTags"]) > 20:
        print(f"  ... and {len(gap_report['unknownRegulationTags']) - 20} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
