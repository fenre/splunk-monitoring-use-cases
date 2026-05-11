#!/usr/bin/env python3
"""Align cimModels with cimSpl datamodel=... references.

Two passes:
1. mismatch — cimSpl references datamodel(s) not declared in cimModels.
   Resolution: union the SPL datamodels into cimModels (SPL is source
   of truth — it's what executes against the indexer).
2. missing  — cimSpl is present but contains no datamodel=... reference.
   Resolution: remove the cimSpl field (it's not a valid CIM/tstats
   query). The non-CIM `spl` field is retained.

Pass --write to apply.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONTENT = REPO / "content"

DATAMODEL_RE = re.compile(r"datamodel=([A-Za-z_]+)(?:\.[A-Za-z_]+){0,2}")


def parent_model(token: str) -> str:
    # `Endpoint.Processes` → `Endpoint`; `Performance.All_Performance` → `Performance`
    return token.split(".")[0]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    mismatch_fixed = 0
    missing_fixed = 0
    file_changes: list[tuple[str, list[str]]] = []

    for p in sorted(CONTENT.glob("cat-*/UC-*.json")):
        try:
            d = json.load(p.open())
        except Exception:
            continue
        spl = d.get("cimSpl")
        if not isinstance(spl, str):
            continue
        models_decl = list(d.get("cimModels") or [])
        decl_set = {m for m in models_decl if isinstance(m, str)}
        decl_parents = {parent_model(m) for m in decl_set}

        spl_models = set(DATAMODEL_RE.findall(spl))
        changes: list[str] = []

        if not spl_models:
            # cimSpl has no datamodel= → remove cimSpl (and dataModelAcceleration
            # if it's now meaningless).
            d.pop("cimSpl", None)
            changes.append("removed cimSpl (no datamodel= reference)")
            missing_fixed += 1
        else:
            # union into cimModels (parent and dotted forms)
            new_models = list(models_decl)
            added: list[str] = []
            for m in sorted(spl_models):
                if m not in decl_parents and m not in decl_set:
                    new_models.append(m)
                    added.append(m)
            if added:
                d["cimModels"] = new_models
                changes.append(
                    f"added cimModels {added} to align with cimSpl datamodel= refs"
                )
                mismatch_fixed += 1

        if changes:
            file_changes.append((p.name, changes))
            if args.write:
                p.write_text(
                    json.dumps(d, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )

    print(f"mismatch (cimModels expanded): {mismatch_fixed}")
    print(f"missing  (cimSpl removed):     {missing_fixed}")
    print(f"\nSample changes:")
    for name, ch in file_changes[:8]:
        print(f"  [{name}] " + "; ".join(ch))
    if not args.write:
        print("\nDRY RUN — pass --write to apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
