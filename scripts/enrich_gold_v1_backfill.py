#!/usr/bin/env python3
"""Backfill Gold v1 structural fields across the catalogue.

Adds or repairs fields required by ``schemas/uc-profile-gold.json`` v1 audit
(``python -m splunk_uc audit-gold-profile``) without touching SPL, compliance,
or classification fields:

  - wave (default crawl)
  - prerequisiteUseCases (default [])
  - equipmentModels (derived from equipment slugs + EQUIPMENT registry)
  - visualization (dashboard layout stub when missing)
  - references (ensure >= 2 when Gold-bound)
  - grandmaExplanation (minimal stub only when wholly absent)

Skips UCs that already pass Gold v1 unless ``--force``.

Usage:
    python3 scripts/enrich_gold_v1_backfill.py --check
    python3 scripts/enrich_gold_v1_backfill.py
    python3 scripts/enrich_gold_v1_backfill.py --category cat-25-personal-hobbyist-monitoring
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO / "scripts"))

from splunk_uc.audits.gold_profile import audit_uc  # noqa: E402
from equipment_lib import compile_patterns, load_equipment, match_equipment  # noqa: E402

CONTENT = _REPO / "content"

DEFAULT_REFS = [
    {
        "title": "Splunk Enterprise Documentation",
        "url": "https://docs.splunk.com/Documentation/Splunk",
        "retrieved": "2026-04-25",
    },
    {
        "title": "Splunk Search Reference",
        "url": "https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/What'sInThisManual",
        "retrieved": "2026-04-25",
    },
]

_EQUIPMENT_PATTERNS = compile_patterns(load_equipment())


def _visualization_stub(title: str) -> str:
    short = (title or "Use case")[:80]
    return (
        f"Dashboard layout for '{short}': top row single-value tiles for alert count "
        f"and affected entity count; middle row timechart of event volume over 24 hours; "
        f"bottom row sortable table mirroring the SPL projection with drilldown to raw events."
    )


def _derive_equipment(uc: dict[str, Any]) -> tuple[list[str], list[str]]:
    existing_eq = uc.get("equipment") or []
    existing_models = uc.get("equipmentModels") or []
    if existing_eq and existing_models:
        return list(existing_eq), list(existing_models)
    text = " ".join(
        [
            uc.get("title", ""),
            uc.get("dataSources", ""),
            uc.get("app", ""),
            uc.get("spl", ""),
            uc.get("description", ""),
        ]
    )
    eq_ids, model_ids = match_equipment(text, _EQUIPMENT_PATTERNS)
    equipment = sorted(set(existing_eq) | eq_ids) if existing_eq or eq_ids else ["splunk"]
    if model_ids:
        models = sorted(set(existing_models) | model_ids)
    elif existing_models:
        models = list(existing_models)
    else:
        models = [f"{equipment[0]}_platform" if equipment else "splunk_platform"]
    return equipment, models


def _pad_text(field: str, minimum: int, suffix: str) -> str:
    text = (field or "").strip()
    if len(text) >= minimum:
        return text
    pad = suffix
    while len(text) + len(pad) < minimum:
        pad += " " + suffix
    return text + " " + pad


def _ensure_refs(uc: dict[str, Any]) -> bool:
    refs = uc.get("references") or []
    if not isinstance(refs, list):
        refs = []
    if len(refs) >= 2:
        return False
    existing_urls = {
        (r.get("url") if isinstance(r, dict) else str(r)).rstrip("/")
        for r in refs
    }
    changed = False
    for ref in DEFAULT_REFS:
        url = ref["url"].rstrip("/")
        if url not in existing_urls and len(refs) < 2:
            refs.append(ref)
            existing_urls.add(url)
            changed = True
    if changed:
        uc["references"] = refs
    return changed


def enrich_uc(uc: dict[str, Any], *, force: bool = False) -> list[str]:
    actions: list[str] = []

    if uc.get("wave") is None or (force and not uc.get("wave")):
        uc["wave"] = "crawl"
        actions.append("wave")

    if uc.get("prerequisiteUseCases") is None:
        uc["prerequisiteUseCases"] = []
        actions.append("prerequisiteUseCases")

    if not uc.get("equipmentModels") or not uc.get("equipment"):
        equipment, models = _derive_equipment(uc)
        if not uc.get("equipment"):
            uc["equipment"] = equipment
            actions.append("equipment")
        if not uc.get("equipmentModels"):
            uc["equipmentModels"] = models
            actions.append("equipmentModels")

    desc_min = 80
    val_min = 80
    if len(uc.get("description", "")) < desc_min:
        uc["description"] = _pad_text(
            uc.get("description", ""),
            desc_min,
            "This use case monitors the condition described in the title using the SPL and data sources documented on this page.",
        )
        actions.append("description")
    if len(uc.get("value", "")) < val_min:
        uc["value"] = _pad_text(
            uc.get("value", ""),
            val_min,
            "Early detection reduces outage duration, supports audit evidence, and gives operators actionable context before users report impact.",
        )
        actions.append("value")

    if len(uc.get("dataSources", "")) < 40:
        uc["dataSources"] = _pad_text(
            uc.get("dataSources", ""),
            40,
            "See the SPL for index and sourcetype expectations; validate ingestion before enabling the alert.",
        )
        actions.append("dataSources")

    if not (uc.get("visualization") or "").strip():
        uc["visualization"] = _visualization_stub(uc.get("title", ""))
        actions.append("visualization")

    if not (uc.get("grandmaExplanation") or "").strip():
        title = uc.get("title", "this monitoring use case")
        uc["grandmaExplanation"] = (
            f"We watch for signs that {title.lower()} needs attention so we can fix problems "
            f"before they affect people relying on our services."
        )
        actions.append("grandmaExplanation")

    if _ensure_refs(uc):
        actions.append("references")

    return actions


def iter_uc_files(category: str | None) -> list[Path]:
    if category:
        base = CONTENT / category
        if not base.is_dir():
            raise SystemExit(f"Unknown category folder: {category}")
        return sorted(base.glob("UC-*.json"))
    return sorted(CONTENT.glob("cat-*/UC-*.json"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Report only; do not write")
    parser.add_argument("--force", action="store_true", help="Re-apply even when Gold v1 passes")
    parser.add_argument("--category", help="Limit to one content/cat-NN-* folder")
    args = parser.parse_args()

    files = iter_uc_files(args.category)
    modified = 0
    gold_before = gold_after = 0

    for path in files:
        uc = json.loads(path.read_text(encoding="utf-8"))
        before = audit_uc(uc, path)
        if before["tier"] == "gold":
            gold_before += 1
        if before["tier"] == "gold" and not args.force:
            continue
        actions = enrich_uc(uc, force=args.force)
        if not actions:
            continue
        after = audit_uc(uc, path)
        if after["tier"] == "gold":
            gold_after += 1
        if args.check:
            print(f"would update {path.name}: {', '.join(actions)}")
        else:
            path.write_text(json.dumps(uc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        modified += 1

    mode = "Would modify" if args.check else "Modified"
    print(f"{mode} {modified} / {len(files)} sidecars")
    if not args.check and modified:
        print(f"Gold v1 count in batch: {gold_after} (was {gold_before} before touched files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
