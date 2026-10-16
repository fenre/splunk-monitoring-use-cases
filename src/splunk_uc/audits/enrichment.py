#!/usr/bin/env python3
"""Fail enrichment that is not a registry id with evidence from the use case.

Narrative fields are not modified. A sidecar with no enrichment lists passes.
``--check`` exits 1 when any sidecar breaks the contract in
``docs/enrichment-contract.md``.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from splunk_uc.fabric.mine import _norm_industry

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTENT = REPO_ROOT / "content"
REGISTRIES = REPO_ROOT / "registries"

FIELDS = (
    "businessOutcomes",
    "businessAreas",
    "personas",
    "industries",
    "sourcetypes",
    "vendorProducts",
)
CAPS = {"businessOutcomes": 3, "businessAreas": 2, "personas": 4}
ASSIGNMENT_KEYS = ("id", "source", "confidence", "evidence", "model", "version")
SKIP_KEYS = frozenset({"owner", "enrichment", *FIELDS})

_SOURCETYPE_EQ = re.compile(
    r"""sourcetype\s*=\s*(?:\*\*)?\s*[`'"]?([A-Za-z0-9_.:*-]+)""",
    re.IGNORECASE,
)
_QUOTED = re.compile(r"""[`'"]([A-Za-z0-9_.:*-]+)[`'"]""")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} is not a JSON object")
    return payload


class RegistryIndex:
    """Ids and sourcetype spellings the enrichment lists are allowed to use."""

    def __init__(self, root: Path) -> None:
        self.ids: dict[str, set[str]] = {}
        self.sourcetype_spellings: dict[str, set[str]] = {}
        self.sourcetype_by_spelling: dict[str, str] = {}
        self.industry_by_norm: dict[str, str] = {}
        mapping = {
            "businessOutcomes": "business-outcomes.json",
            "businessAreas": "business-areas.json",
            "personas": "personas.json",
            "industries": "industries.json",
            "sourcetypes": "sourcetypes.json",
            "vendorProducts": "vendor-products.json",
        }
        for field, filename in mapping.items():
            entries = _load(root / filename)["entries"]
            self.ids[field] = {str(row["id"]) for row in entries}
            if field == "sourcetypes":
                for row in entries:
                    spellings = {str(row["canonical"])}
                    spellings.update(str(alias) for alias in row.get("aliases") or [])
                    self.sourcetype_spellings[str(row["id"])] = spellings
                    for spelling in spellings:
                        self.sourcetype_by_spelling.setdefault(spelling.casefold(), str(row["id"]))
            if field == "industries":
                for row in entries:
                    for text in [row.get("name") or "", *(row.get("aliases") or [])]:
                        key = _norm_industry(str(text))
                        if key:
                            self.industry_by_norm.setdefault(key, str(row["id"]))


def _strings(node: Any, key: str, out: list[str], data_sources: list[str]) -> None:
    if key in SKIP_KEYS:
        return
    if isinstance(node, str):
        out.append(node)
        if key == "dataSources":
            data_sources.append(node)
        return
    if isinstance(node, dict):
        for child_key, child in node.items():
            _strings(child, child_key, out, data_sources)
        return
    if isinstance(node, list):
        for child in node:
            _strings(child, key, out, data_sources)


def _narrative(uc: dict[str, Any]) -> tuple[str, list[str]]:
    parts: list[str] = []
    data_sources: list[str] = []
    for key, value in uc.items():
        _strings(value, key, parts, data_sources)
    return "\n".join(parts), data_sources


_FILENAME_SUFFIX = re.compile(r"\.(?:sh|csv|conf|log|py|md|xml|json|html|txt)$", re.IGNORECASE)


def _explicit_sourcetypes(narrative: str, data_sources: list[str]) -> set[str]:
    """Sourcetype spellings stated as ``sourcetype=`` or a quoted dataSources token.

    A quoted token counts only when it contains a colon, or the word
    sourcetype sits immediately in front of it. Field names (``Device``)
    and script names (``iostat.sh``) are not sourcetypes.
    """
    found = {match.group(1).casefold() for match in _SOURCETYPE_EQ.finditer(narrative)}
    for text in data_sources:
        folded = text.casefold()
        for match in _QUOTED.finditer(text):
            token = match.group(1)
            if _FILENAME_SUFFIX.search(token):
                continue
            if ":" in token:
                found.add(token.casefold())
                continue
            start = match.start()
            window = folded[max(0, start - 24) : start]
            if "sourcetype" in window:
                found.add(token.casefold())
    return found


def _as_ids(value: Any) -> list[str] | None:
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        return None
    return value


def _issues_for(path: Path, uc: dict[str, Any], registries: RegistryIndex) -> list[str]:
    present = [field for field in FIELDS if field in uc]
    enrichment = uc.get("enrichment")
    if not present and enrichment is None:
        return []
    label = f"UC-{uc.get('id') or path.stem}"
    issues: list[str] = []
    if enrichment is None:
        enrichment = {}
    if not isinstance(enrichment, dict):
        return [f"{label}: enrichment must be an object"]
    for key in enrichment:
        if key not in FIELDS and key != "proposedValues":
            issues.append(f"{label}: unknown enrichment key {key}")
    narrative, data_sources = _narrative(uc)
    explicit = _explicit_sourcetypes(narrative, data_sources)
    owner = str(uc.get("owner") or "").strip()

    raw_industry = str(uc.get("industry") or "").strip()
    industry_key = _norm_industry(raw_industry) if raw_industry else None
    industry_id = registries.industry_by_norm.get(industry_key) if industry_key else None

    for field in FIELDS:
        ids = _as_ids(uc.get(field)) if field in uc else []
        if ids is None:
            issues.append(f"{label}: {field} must be a list of registry ids")
            ids = []
        cap = CAPS.get(field)
        if cap is not None and len(ids) > cap:
            issues.append(f"{label}: {field} has {len(ids)} ids; the cap is {cap}")
        if len(ids) != len(set(ids)):
            issues.append(f"{label}: {field} repeats an id")
        raw_assignments = enrichment.get(field, [])
        if raw_assignments is None:
            raw_assignments = []
        if not isinstance(raw_assignments, list):
            issues.append(f"{label}: enrichment.{field} must be a list")
            raw_assignments = []
        if cap is not None and len(raw_assignments) > cap:
            issues.append(f"{label}: enrichment.{field} has {len(raw_assignments)} assignments; the cap is {cap}")
        by_id: dict[str, dict[str, Any]] = {}
        for item in raw_assignments:
            if not isinstance(item, dict):
                issues.append(f"{label}: enrichment.{field} assignment must be an object")
                continue
            missing = [key for key in ASSIGNMENT_KEYS if key not in item or item[key] in ("", None)]
            assignment_id = str(item.get("id") or "")
            if missing:
                issues.append(
                    f"{label}: {field} {assignment_id or '?'}: missing {', '.join(missing)}"
                )
            if assignment_id:
                if assignment_id in by_id:
                    issues.append(f"{label}: {field} repeats assignment {assignment_id}")
                by_id[assignment_id] = item
        listed = set(ids)
        assigned = set(by_id)
        for extra in sorted(assigned - listed):
            issues.append(f"{label}: {field} assignment {extra} is not in the id list")
        for entity_id in ids:
            if entity_id not in registries.ids[field]:
                issues.append(f"{label}: {field}: unknown id {entity_id}")
                continue
            if field == "industries" and raw_industry and entity_id != industry_id:
                issues.append(
                    f"{label}: industries {entity_id} does not match the industry field"
                )
            item = by_id.get(entity_id)
            if item is None:
                issues.append(f"{label}: {field} {entity_id}: missing evidence")
                continue
            if "evidence" not in item or not str(item.get("evidence") or "").strip():
                continue
            evidence = str(item["evidence"])
            source = str(item.get("source") or "")
            if source not in ("authored", "inferred"):
                issues.append(f"{label}: {field} {entity_id}: source must be authored or inferred")
            else:
                raw_confidence = item.get("confidence")
                try:
                    confidence = float(raw_confidence) if isinstance(raw_confidence, (int, float, str)) else -1.0
                except (TypeError, ValueError):
                    confidence = -1.0
                if source == "authored" and confidence != 1.0:
                    issues.append(f"{label}: {field} {entity_id}: authored confidence must be 1")
                if source == "inferred" and not (0 < confidence < 1):
                    issues.append(f"{label}: {field} {entity_id}: inferred confidence must be below 1")
            if field == "personas" and owner and evidence.strip().casefold() == owner.casefold():
                issues.append(f"{label}: personas {entity_id}: owner copied into personas")
                continue
            if evidence not in narrative:
                issues.append(f"{label}: {field} {entity_id}: evidence does not appear in the use case")
                continue
            if field == "sourcetypes":
                spellings = registries.sourcetype_spellings.get(entity_id, set())
                quoted = any(spelling.casefold() in explicit for spelling in spellings)
                in_evidence = any(spelling in evidence for spelling in spellings)
                if not quoted or not in_evidence:
                    issues.append(
                        f"{label}: sourcetypes {entity_id}: evidence is not an explicit sourcetype"
                    )

    proposed = enrichment.get("proposedValues", [])
    if proposed is None:
        proposed = []
    if not isinstance(proposed, list):
        issues.append(f"{label}: proposedValues must be a list")
    else:
        for item in proposed:
            if not isinstance(item, dict):
                issues.append(f"{label}: proposedValue must be an object")
                continue
            if item.get("field") not in FIELDS or not str(item.get("value") or "").strip():
                issues.append(f"{label}: proposedValue needs a field and a value")
            if not str(item.get("note") or "").strip():
                issues.append(f"{label}: proposedValue {item.get('value')!r} needs a note")
    return issues


def audit_tree(
    content: Path | None = None,
    registries: Path | None = None,
) -> list[str]:
    """Return one string per contract break under ``content``."""
    index = RegistryIndex(registries or REGISTRIES)
    root = content or CONTENT
    issues: list[str] = []
    for path in sorted(root.glob("cat-*/UC-*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            issues.append(f"{path.name}: failed to parse ({exc})")
            continue
        if not isinstance(payload, dict):
            issues.append(f"{path.name}: sidecar is not an object")
            continue
        issues.extend(_issues_for(path, payload, index))
    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 when an enrichment id or its evidence breaks the contract.",
    )
    parser.add_argument("--content", type=Path, default=None)
    parser.add_argument("--registries", type=Path, default=None)
    args = parser.parse_args(argv)
    issues = audit_tree(args.content, args.registries)
    if not issues:
        print("enrichment: OK")
        return 0
    for issue in issues[:50]:
        print(issue, file=sys.stderr)
    if len(issues) > 50:
        print(f"... {len(issues) - 50} more", file=sys.stderr)
    print(f"enrichment: {len(issues)} issue(s)", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
