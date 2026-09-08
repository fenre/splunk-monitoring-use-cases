#!/usr/bin/env python3
"""Audit equipment slugs and model compounds against the SSOT registry.

Checks performed:

1. ``unresolved-equipment-slug`` — every ``equipment[]`` slug resolves to a
   registry id (directly or via ``EQUIPMENT_ALIASES``).
2. ``unknown-equipment-model`` — every ``equipmentModels[]`` compound exists in
   the registry model table.
3. ``generic-suffix-model`` — no ``equipmentModels[]`` compounds or registry
   model ids end with the ``_generic`` suffix.
4. ``equipment-missing-from-groups`` — every registry entry with
   ``kind=equipment`` appears in ``tools/data-sizing/mapping.js``
   ``EQUIPMENT_GROUPS``.
5. ``vendor-spelling-inconsistent`` — registry entries sharing the same
   normalized vendor name use one canonical spelling.

Run::

    PYTHONPATH=src python3 -m splunk_uc audit-equipment-models
    PYTHONPATH=src python3 -m splunk_uc audit-equipment-models --check
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from splunk_uc.audits._uc_walk import get_list_field, iter_uc_sidecars, uc_label

REPO_ROOT = Path(__file__).resolve().parents[3]
MAPPING_JS = REPO_ROOT / "tools" / "data-sizing" / "mapping.js"
_SCRIPTS_DIR = REPO_ROOT / "scripts"
_TOOLS_DIR = REPO_ROOT / "tools"

_GROUP_IDS_RE = re.compile(r"ids:\s*\[([^\]]*)\]")
_GENERIC_SUFFIX = "_generic"


@dataclass(frozen=True)
class Finding:
    kind: str
    message: str
    context: str = ""


def _ensure_equipment_lib_importable() -> None:
    for directory in (_SCRIPTS_DIR, _TOOLS_DIR):
        if directory.is_dir() and str(directory) not in sys.path:
            sys.path.insert(0, str(directory))


def _load_registry() -> tuple[set[str], set[str], list[dict[str, Any]]]:
    _ensure_equipment_lib_importable()
    from equipment_lib import load_equipment  # noqa: WPS433

    equipment_ids: set[str] = set()
    compounds: set[str] = set()
    entries: list[dict[str, Any]] = []
    for entry in load_equipment():
        entries.append(entry)
        equipment_ids.add(str(entry["id"]))
        for model in entry.get("models") or []:
            if isinstance(model, dict) and model.get("id"):
                compounds.add(f"{entry['id']}_{model['id']}")
    return equipment_ids, compounds, entries


def parse_equipment_group_ids(mapping_text: str) -> set[str]:
    """Extract equipment ids referenced by ``window.EQUIPMENT_GROUPS``."""
    marker = "window.EQUIPMENT_GROUPS = ["
    start = mapping_text.index(marker)
    end = mapping_text.index("window.DSA_EQUIPMENT_MAP", start)
    block = mapping_text[start:end]
    ids: set[str] = set()
    for match in _GROUP_IDS_RE.finditer(block):
        ids.update(re.findall(r"'([^']+)'", match.group(1)))
    return ids


def _normalize_vendor(vendor: str) -> str:
    return re.sub(r"\s+", " ", vendor.casefold().strip())


def audit_registry(entries: list[dict[str, Any]], group_ids: set[str]) -> list[Finding]:
    findings: list[Finding] = []
    vendor_spellings: dict[str, set[str]] = defaultdict(set)

    for entry in entries:
        eq_id = str(entry["id"])
        kind = str(entry.get("kind") or "equipment")
        vendor = str(entry.get("vendor") or "")
        if kind == "equipment" and eq_id not in group_ids:
            findings.append(
                Finding(
                    kind="equipment-missing-from-groups",
                    message=(
                        f"registry entry {eq_id!r} has kind=equipment but is absent "
                        f"from tools/data-sizing/mapping.js EQUIPMENT_GROUPS"
                    ),
                )
            )
        if vendor:
            vendor_spellings[_normalize_vendor(vendor)].add(vendor)
        for model in entry.get("models") or []:
            if not isinstance(model, dict):
                continue
            model_id = str(model.get("id") or "")
            if model_id.endswith(_GENERIC_SUFFIX):
                findings.append(
                    Finding(
                        kind="generic-suffix-model",
                        message=(
                            f"registry model {eq_id}_{model_id!r} uses forbidden "
                            f"{_GENERIC_SUFFIX!r} suffix"
                        ),
                    )
                )

    for normalized, spellings in sorted(vendor_spellings.items()):
        if len(spellings) <= 1:
            continue
        findings.append(
            Finding(
                kind="vendor-spelling-inconsistent",
                message=(
                    f"vendor {normalized!r} appears with inconsistent spellings: "
                    f"{sorted(spellings)!r}"
                ),
            )
        )
    return findings


def audit_sidecars(
    equipment_ids: set[str],
    compounds: set[str],
) -> list[Finding]:
    _ensure_equipment_lib_importable()
    from equipment_lib import resolve_equipment_slug  # noqa: WPS433

    findings: list[Finding] = []
    for path, payload in iter_uc_sidecars():
        label = uc_label(path, payload)
        for slug in get_list_field(payload, "equipment"):
            if not isinstance(slug, str) or not slug.strip():
                continue
            canonical = resolve_equipment_slug(slug.strip())
            if canonical not in equipment_ids:
                findings.append(
                    Finding(
                        kind="unresolved-equipment-slug",
                        message=(
                            f"{label}: equipment slug {slug!r} resolves to "
                            f"{canonical!r}, which is not in the registry"
                        ),
                        context=slug,
                    )
                )
        for compound in get_list_field(payload, "equipmentModels"):
            if not isinstance(compound, str) or not compound.strip():
                continue
            model = compound.strip()
            if model.endswith(_GENERIC_SUFFIX):
                findings.append(
                    Finding(
                        kind="generic-suffix-model",
                        message=(
                            f"{label}: equipmentModels entry {model!r} uses forbidden "
                            f"{_GENERIC_SUFFIX!r} suffix"
                        ),
                        context=model,
                    )
                )
                continue
            if model not in compounds:
                findings.append(
                    Finding(
                        kind="unknown-equipment-model",
                        message=(
                            f"{label}: equipmentModels entry {model!r} is not a "
                            f"registered compound id"
                        ),
                        context=model,
                    )
                )
    return findings


def run_audit() -> list[Finding]:
    equipment_ids, compounds, entries = _load_registry()
    mapping_text = MAPPING_JS.read_text(encoding="utf-8")
    group_ids = parse_equipment_group_ids(mapping_text)
    findings = audit_registry(entries, group_ids)
    findings.extend(audit_sidecars(equipment_ids, compounds))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit equipment[] / equipmentModels[] against the SSOT registry.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="CI mode: exit non-zero when any finding is reported.",
    )
    args = parser.parse_args(argv)

    findings = run_audit()
    by_kind = Counter(f.kind for f in findings)

    print("=" * 72)
    print("Equipment models audit (registry + content/cat-*/UC-*.json)")
    print("=" * 72)
    print(f"Findings: {len(findings)}")
    if by_kind:
        print("\nFindings by category:")
        for kind, count in sorted(by_kind.items(), key=lambda kv: (-kv[1], kv[0])):
            print(f"  {count:4d}  {kind}")

    if findings:
        print("\nFINDINGS:")
        print("-" * 72)
        for finding in sorted(findings, key=lambda f: (f.kind, f.message)):
            print(f"[{finding.kind}] {finding.message}")

    if args.check and findings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
