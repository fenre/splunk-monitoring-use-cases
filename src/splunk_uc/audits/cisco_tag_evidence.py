#!/usr/bin/env python3
"""Classify Cisco-tagged use cases by whether their search can see Cisco data.

Compares each use case's ``cisco_*`` model tags with the sourcetypes,
indexes and macros its ``spl`` / ``cimSpl`` names, using the per-model
``evidence`` blocks in the ``EQUIPMENT`` registry.

Categories:

- ``A``  a tagged model is backed by a sourcetype in the search (other
  tagged models may be unbacked extras; see ``detail``).
- ``E1`` a tagged model is backed, but only by an index or macro.
- ``B``  the search reads only a competing vendor's sourcetypes; ``app``
  lists a Cisco product (multi-vendor use case, needs a Cisco variant).
- ``E2`` as B, but the competing vendor is named by index / macro only.
- ``C``  nothing in the search or ``app`` relates to the tagged model.
- ``D``  the search names only generic sourcetypes (syslog, SNMP, ...).
- ``E3`` no sourcetype; generic index only.
- ``E4`` no sourcetype; CIM data model / CIM macro.
- ``E5`` no sourcetype and no index (lookups, REST, makeresults, ...).
- ``F``  ``equipment: cisco`` with no ``cisco_*`` model tag.
- ``G``  the search reads Cisco data, but none of the tagged models.

Run::

    PYTHONPATH=src python3 -m splunk_uc audit-cisco-tag-evidence --summary
    PYTHONPATH=src python3 -m splunk_uc audit-cisco-tag-evidence \\
        --write-csv reports/cisco-tag-audit.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from splunk_uc import equipment_evidence as ev_mod
from splunk_uc.audits._uc_walk import iter_uc_sidecars

REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPTS_DIR = REPO_ROOT / "scripts"
VENDOR = "cisco"

ACTIONS = {
    "A": "keep",
    "E1": "keep",
    "B": "add-cisco-variant",
    "E2": "add-cisco-variant",
    "C": "remove-tag",
    "D": "human-review",
    "E3": "human-review",
    "E4": "keep; record add-on CIM coverage in registry",
    "E5": "human-review",
    "F": "human-review: pick a model or drop",
    "G": "retag-model",
}
CATEGORY_ORDER = ("A", "E1", "B", "E2", "C", "D", "E3", "E4", "E5", "F", "G")


@dataclass(frozen=True)
class Row:
    uc_id: str
    title: str
    equipment: str
    equipment_models: str
    sourcetypes: str
    indexes: str
    macros: str
    uses_datamodel: bool
    app_names_cisco: bool
    category: str
    action: str
    detail: str


def _registry() -> dict[str, Any]:
    if str(_SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS_DIR))
    from equipment_lib import load_equipment  # noqa: WPS433

    return next(e for e in load_equipment() if e["id"] == VENDOR)


def _variant_spl(uc: dict[str, Any], compound: str) -> list[str]:
    return [
        str(v.get("q") or "") + " " + str(v.get("qs") or "")
        for v in uc.get("splVariants") or []
        if isinstance(v, dict) and v.get("model") == compound
    ]


def classify(uc: dict[str, Any], entry: dict[str, Any]) -> tuple[str, str]:
    """Return (category, detail) for one Cisco-tagged sidecar."""
    models_tagged = [m for m in uc.get("equipmentModels") or [] if m.startswith(VENDOR + "_")]
    ev = ev_mod.extract_spl_evidence(uc.get("spl"), uc.get("cimSpl"))
    vendor_block = ev_mod.evidence_block(entry)
    blocks = {f"{VENDOR}_{m['id']}": ev_mod.evidence_block(m) for m in entry.get("models") or []}
    app_lower = (uc.get("app") or "").replace("`", "").lower()
    all_tas = list(entry.get("tas") or []) + [
        p for m in entry.get("models") or [] for p in m.get("tas") or []
    ]
    app_cisco = any(ev_mod.token_contains(app_lower, p.lower()) for p in all_tas)

    if not models_tagged:
        return "F", ""

    def backed(compound: str) -> tuple[bool, bool]:
        block = blocks.get(compound)
        if block is None:
            return False, False
        variant_ev = ev_mod.extract_spl_evidence(*_variant_spl(uc, compound))
        st = ev_mod.matches_sourcetype(ev, block) or ev_mod.matches_sourcetype(variant_ev, block)
        any_ev = st or ev_mod.matches_evidence(ev, block) or ev_mod.matches_evidence(variant_ev, block)
        return any_ev, st

    results = {m: backed(m) for m in models_tagged}
    unbacked = sorted(m for m, (ok, _) in results.items() if not ok)
    extra = f"unbacked extra tags: {','.join(unbacked)}" if unbacked else ""
    if any(st for _, st in results.values()):
        return "A", extra
    if any(ok for ok, _ in results.values()):
        return "E1", "; ".join(x for x in ("backed by index/macro only", extra) if x)

    seen = sorted(c for c, b in blocks.items() if ev_mod.matches_evidence(ev, b))
    vendor_specific = ev_mod.SplEvidence(sourcetypes=ev.specific_sourcetypes)
    if seen or ev_mod.matches_evidence(vendor_specific, vendor_block):
        return "G", f"unbacked {','.join(unbacked)}; search reads {','.join(seen) or 'unmapped cisco data'}"

    specific = sorted(ev.specific_sourcetypes)
    if specific:
        peer = [s for s in specific if ev_mod.is_peer_vendor_token(s)]
        if app_cisco and peer:
            return "B", f"search reads {','.join(peer)}"
        return "C", f"search reads {','.join(specific)}"
    if ev.sourcetypes:
        return ("D", "generic sourcetypes only") if app_cisco else ("C", "no Cisco product in app")
    if ev.uses_datamodel:
        return "E4", "CIM data model"
    peer_idx = sorted(i for i in ev.indexes | ev.macros if ev_mod.is_peer_vendor_token(i))
    if peer_idx:
        return ("E2", f"reads {','.join(peer_idx)}") if app_cisco else ("C", "")
    if ev.indexes:
        return ("E3", "generic index") if app_cisco else ("C", "no Cisco product in app")
    return ("E5", "no index or sourcetype") if app_cisco else ("C", "no Cisco product in app")


def _load_override_ids() -> set[str]:
    path = REPO_ROOT / "data" / "equipment-tag-overrides.json"
    if not path.is_file():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    return {k.removeprefix("UC-") for k in data.get("overrides") or {}}


def _action(cat: str, uc: dict[str, Any], app_cisco: bool, entry: dict[str, Any], overrides: set[str]) -> str:
    if uc["id"] in overrides:
        return "keep via data/equipment-tag-overrides.json"
    if cat in ("E4", "F") and not app_cisco:
        ev = ev_mod.extract_spl_evidence(uc.get("spl"), uc.get("cimSpl"))
        if not ev_mod.matches_evidence(ev, ev_mod.evidence_block(entry)):
            return "remove-tag (Cisco named only in prose)"
    return ACTIONS[cat]


def build_rows() -> list[Row]:
    entry = _registry()
    overrides = _load_override_ids()
    rows: list[Row] = []
    for _path, uc in iter_uc_sidecars():
        eq = list(uc.get("equipment") or [])
        models = [m for m in uc.get("equipmentModels") or [] if m.startswith(VENDOR + "_")]
        if VENDOR not in eq and not models:
            continue
        cat, detail = classify(uc, entry)
        ev = ev_mod.extract_spl_evidence(uc.get("spl"), uc.get("cimSpl"))
        app_lower = (uc.get("app") or "").replace("`", "").lower()
        all_tas = list(entry.get("tas") or []) + [
            p for m in entry.get("models") or [] for p in m.get("tas") or []
        ]
        app_cisco = any(ev_mod.token_contains(app_lower, p.lower()) for p in all_tas)
        rows.append(
            Row(
                uc_id=f"UC-{uc['id']}",
                title=str(uc.get("title") or ""),
                equipment=";".join(eq),
                equipment_models=";".join(models),
                sourcetypes=";".join(sorted(ev.sourcetypes)),
                indexes=";".join(sorted(ev.indexes)),
                macros=";".join(sorted(ev.macros)),
                uses_datamodel=ev.uses_datamodel,
                app_names_cisco=app_cisco,
                category=cat,
                action=_action(cat, uc, app_cisco, entry, overrides),
                detail=detail,
            )
        )
    rows.sort(key=lambda r: [int(x) for x in r.uc_id[3:].split(".")])
    return rows


def write_csv(rows: list[Row], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(Row.__dataclass_fields__)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({f: getattr(r, f) for f in fields})


def summary(rows: list[Row]) -> Counter[str]:
    return Counter(r.category for r in rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--write-csv", type=Path, help="Write the per-use-case work list to this path.")
    parser.add_argument("--summary", action="store_true", help="Print counts per category.")
    args = parser.parse_args(argv)

    rows = build_rows()
    if args.write_csv:
        write_csv(rows, args.write_csv)
        print(f"Wrote {len(rows)} rows to {args.write_csv}")
    if args.summary or not args.write_csv:
        counts = summary(rows)
        print(f"Cisco-tagged use cases: {len(rows)}")
        for cat in CATEGORY_ORDER:
            print(f"  {cat:3} {counts.get(cat, 0):5}  {ACTIONS[cat]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
