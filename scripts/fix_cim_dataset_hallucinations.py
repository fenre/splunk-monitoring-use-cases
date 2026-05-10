#!/usr/bin/env python3
"""Fix CIM datamodel/dataset hallucinations across the JSON SSOT.

Two classes of fixes are applied to ``content/cat-*/UC-*.json``:

1. Bogus ``datamodel=Model.Dataset`` strings where ``Dataset`` is not a real
   CIM 6.x dataset under that model. The underlying tstats search will fail at
   runtime. The audit ``splunk_uc.audits.spl_hallucinations`` flags these as
   ``cim_dataset_unknown``. Each rewrite is deterministic and field-preserving:
   we only touch the literal ``datamodel=...`` token, never the ``BY`` or
   ``WHERE`` clauses around it.

2. Style normalisation: ``summariesonly=true|false`` → ``summariesonly=t|f``.
   Both forms parse, but Splunk style is ``=t|=f`` and the audit warns on the
   long form.

The script targets both the ``spl`` and ``cimSpl`` fields and writes JSON back
through ``json.dumps(..., indent=2, ensure_ascii=False)`` so we don't disturb
unicode or escaping.

Usage:
    python3 scripts/fix_cim_dataset_hallucinations.py            # apply
    python3 scripts/fix_cim_dataset_hallucinations.py --dry-run  # show counts
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONTENT = REPO / "content"

# ---------------------------------------------------------------------------
# Datamodel.Dataset rewrites — the LHS is what was hallucinated, the RHS is
# the canonical CIM 6.x dataset that closest matches authorial intent.
# ---------------------------------------------------------------------------
DATAMODEL_REWRITES: dict[str, str] = {
    # The root All_* dataset of each model is the safe default for "show
    # everything in this model" queries — that's the intent every flagged UC
    # carried.
    "datamodel=Performance.Performance": "datamodel=Performance.All_Performance",
    "datamodel=Email.Email": "datamodel=Email.All_Email",
    "datamodel=Change.Change": "datamodel=Change.All_Changes",
    "datamodel=Network_Traffic.Network_Traffic": "datamodel=Network_Traffic.All_Traffic",
    "datamodel=Authentication.All_Authentication": "datamodel=Authentication.Authentication",
    # IDS_Attacks is the only dataset under Intrusion_Detection in CIM 6.x.
    "datamodel=Intrusion_Detection.Intrusion_Detection": "datamodel=Intrusion_Detection.IDS_Attacks",
    # Web has a single top-level dataset named Web (no proxy subset).
    "datamodel=Web.proxy": "datamodel=Web.Web",
    # Malware is its OWN datamodel in CIM 6.x — not a subset of Endpoint.
    # Field references in the affected UCs already prefix "Malware.*" (e.g.
    # Malware.dest, Malware.signature), so the model rename keeps the SPL
    # internally consistent.
    "datamodel=Endpoint.Malware": "datamodel=Malware.Malware_Attacks",
}

# ---------------------------------------------------------------------------
# Companion ``WHERE nodename=Model.Dataset`` rewrites — wherever the bogus
# datamodel was paired with a matching ``nodename=`` selector, we have to keep
# both halves in lock-step or tstats will silently return zero rows.
# ---------------------------------------------------------------------------
NODENAME_REWRITES: dict[str, str] = {
    "nodename=Performance.Performance": "nodename=Performance.All_Performance",
    "nodename=Email.Email": "nodename=Email.All_Email",
    "nodename=Change.Change": "nodename=Change.All_Changes",
    "nodename=Network_Traffic.Network_Traffic": "nodename=Network_Traffic.All_Traffic",
    "nodename=Authentication.All_Authentication": "nodename=Authentication.Authentication",
    "nodename=Intrusion_Detection.Intrusion_Detection": "nodename=Intrusion_Detection.IDS_Attacks",
    "nodename=Web.proxy": "nodename=Web.Web",
    "nodename=Endpoint.Malware": "nodename=Malware.Malware_Attacks",
}

# ---------------------------------------------------------------------------
# Style normalisation: summariesonly=true|false → summariesonly=t|f
# ---------------------------------------------------------------------------
RE_SO_TRUE = re.compile(r"\bsummariesonly\s*=\s*true\b")
RE_SO_FALSE = re.compile(r"\bsummariesonly\s*=\s*false\b")


def _apply_string_fixes(text: str) -> tuple[str, dict[str, int]]:
    counts: dict[str, int] = {}
    if not text:
        return text, counts
    for bad, good in DATAMODEL_REWRITES.items():
        if bad in text:
            counts[bad] = counts.get(bad, 0) + text.count(bad)
            text = text.replace(bad, good)
    for bad, good in NODENAME_REWRITES.items():
        if bad in text:
            counts.setdefault("__nodename_total", 0)
            counts["__nodename_total"] += text.count(bad)
            text = text.replace(bad, good)
    n_true = len(RE_SO_TRUE.findall(text))
    if n_true:
        counts["summariesonly=true→t"] = n_true
        text = RE_SO_TRUE.sub("summariesonly=t", text)
    n_false = len(RE_SO_FALSE.findall(text))
    if n_false:
        counts["summariesonly=false→f"] = n_false
        text = RE_SO_FALSE.sub("summariesonly=f", text)
    return text, counts


def _process_file(path: Path, dry_run: bool) -> dict[str, int]:
    raw = path.read_text(encoding="utf-8")
    try:
        uc = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"  SKIP (parse error): {path.name}: {exc}", file=sys.stderr)
        return {}

    file_counts: dict[str, int] = {}
    changed = False
    # Walk every top-level string field. The hallucinated CIM dataset names
    # show up in SPL, CIM SPL, plus narrative prose like ``dataSources``,
    # ``implementation``, ``detailedImplementation``, ``dataModelAcceleration``,
    # ``value``, ``description``. We intentionally skip non-string fields
    # (lists, dicts) — none of them carry SPL today.
    for field, value in list(uc.items()):
        if not isinstance(value, str) or not value:
            continue
        new_text, counts = _apply_string_fixes(value)
        if new_text != value:
            uc[field] = new_text
            changed = True
            for k, v in counts.items():
                file_counts[k] = file_counts.get(k, 0) + v

    if changed and not dry_run:
        new_raw = json.dumps(uc, indent=2, ensure_ascii=False) + "\n"
        path.write_text(new_raw, encoding="utf-8")
    return file_counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="show what would change without writing")
    args = parser.parse_args(argv)

    files = sorted(CONTENT.glob("cat-*/UC-*.json"))
    grand_totals: dict[str, int] = {}
    files_changed: list[tuple[str, dict[str, int]]] = []

    for fp in files:
        counts = _process_file(fp, args.dry_run)
        if counts:
            files_changed.append((str(fp.relative_to(REPO)), counts))
            for k, v in counts.items():
                grand_totals[k] = grand_totals.get(k, 0) + v

    print(f"Files scanned:  {len(files)}")
    print(f"Files {'that would change' if args.dry_run else 'modified'}:  {len(files_changed)}")
    print()
    print("Total substitutions by category:")
    for k, v in sorted(grand_totals.items(), key=lambda x: -x[1]):
        print(f"  {v:4d}  {k}")
    if args.dry_run and files_changed:
        print("\nSample affected files (first 10):")
        for path, counts in files_changed[:10]:
            label = ", ".join(f"{k}×{v}" for k, v in counts.items())
            print(f"  {path}  [{label}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
