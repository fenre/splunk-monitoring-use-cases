#!/usr/bin/env python3
"""Starter-pack audit (guided onboarding Phase 1).

Validates every ``data/starter-packs/*.json`` file against
``schemas/starter-pack.schema.json`` and enforces the pack contract:

Errors (always fail ``--check``):

* schema violations, or ``id`` that does not match the file name;
* unknown ``ucId``, duplicate steps, or ``order`` that is not 1..n;
* ``pairId`` that is unknown, not reciprocal, or has the same ``goal``;
* the same ``ucId`` in both packs of a pair;
* a step that comes before one of its in-pack ``prerequisiteUseCases``;
* a step whose data is not covered by the pack ``requiredData``
  (sourcetypes / internal indexes, equipment, Splunkbase apps);
* unknown or self-referencing ``nextPacks``;
* unknown equipment slugs or Splunkbase apps (or deprecated apps);
* a ``published`` pack containing a cat-25 UC, or carrying any warning.

Warnings (block ``status: published`` only):

* step UC is not ``status: verified``;
* step UC is below Silver depth (``gold_profile`` tier);
* step UC carries ``requires_sme_review`` on a compliance row;
* step UC lists a prerequisite that is in neither the pack nor its pair.

The audit also validates ``data/sourcetype-aliases.json`` (no sourcetype
in two groups).

Run::

    PYTHONPATH=src python3 -m splunk_uc audit-starter-packs
    PYTHONPATH=src python3 -m splunk_uc audit-starter-packs --check
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
PACKS_DIR = REPO_ROOT / "data" / "starter-packs"
SCHEMA_PATH = REPO_ROOT / "schemas" / "starter-pack.schema.json"
ALIASES_PATH = REPO_ROOT / "data" / "sourcetype-aliases.json"
CATALOG_PATH = REPO_ROOT / "data" / "splunkbase-catalog.json"
CONTENT_DIR = REPO_ROOT / "content"
_SCRIPTS_DIR = REPO_ROOT / "scripts"
_TOOLS_DIR = REPO_ROOT / "tools"

_SB_REQUIRED_ROLES = frozenset({"primary", "data-source", "required"})
_SILVER_OR_BETTER = frozenset({"silver", "gold"})


@dataclass(frozen=True)
class Finding:
    pack_id: str
    level: str  # "error" | "warning"
    code: str
    message: str

    def render(self) -> str:
        return f"{self.pack_id}: [{self.code}] {self.message}"


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------


def _load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def load_packs(packs_dir: Path = PACKS_DIR) -> dict[str, tuple[Path, dict[str, Any]]]:
    """Return ``file stem -> (path, pack)`` for every pack file."""
    out: dict[str, tuple[Path, dict[str, Any]]] = {}
    if not packs_dir.is_dir():
        return out
    for path in sorted(packs_dir.glob("*.json")):
        out[path.stem] = (path, _load_json(path))
    return out


def load_uc_index(content_dir: Path = CONTENT_DIR) -> dict[str, tuple[Path, dict[str, Any]]]:
    """Return ``UC-X.Y.Z -> (path, sidecar)`` for every UC sidecar."""
    out: dict[str, tuple[Path, dict[str, Any]]] = {}
    for path in sorted(content_dir.glob("cat-*/UC-*.json")):
        try:
            payload = _load_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict) and payload.get("id"):
            out[f"UC-{payload['id']}"] = (path, payload)
    return out


def load_alias_groups(path: Path = ALIASES_PATH) -> list[list[str]]:
    """Return alias groups as lowercase lists, canonical first."""
    if not path.is_file():
        return []
    doc = _load_json(path)
    groups: list[list[str]] = []
    for group in doc.get("groups") or []:
        names = [str(group.get("canonical", ""))] + [str(a) for a in group.get("aliases") or []]
        groups.append([n.strip().lower() for n in names if n and n.strip()])
    return groups


def alias_map(groups: Iterable[list[str]]) -> dict[str, str]:
    """Map every lowercase sourcetype in a group to the group's canonical name."""
    out: dict[str, str] = {}
    for group in groups:
        if not group:
            continue
        for name in group:
            out[name] = group[0]
    return out


def normalise_sourcetype(name: str, aliases: Mapping[str, str]) -> str:
    key = name.strip().lower()
    return aliases.get(key, key)


def _load_catalog_apps() -> dict[str, dict[str, Any]]:
    catalog = _load_json(CATALOG_PATH)
    return {str(k): v for k, v in (catalog.get("apps") or {}).items() if isinstance(v, dict)}


def _load_equipment_ids() -> set[str]:
    """Registry slugs plus compound ``<slug>_<model>`` ids."""
    for directory in (_SCRIPTS_DIR, _TOOLS_DIR):
        if directory.is_dir() and str(directory) not in sys.path:
            sys.path.insert(0, str(directory))
    from equipment_lib import load_equipment

    ids: set[str] = set()
    for entry in load_equipment():
        slug = str(entry["id"])
        ids.add(slug)
        for model in entry.get("models") or []:
            if isinstance(model, dict) and model.get("id"):
                ids.add(f"{slug}_{model['id']}")
    return ids


# ---------------------------------------------------------------------------
# UC data helpers (shared with the generator)
# ---------------------------------------------------------------------------


def uc_sourcetypes(sidecar: Mapping[str, Any]) -> list[str]:
    """Lowercase sourcetypes referenced by a sidecar (same extractor as sourcetype-index)."""
    from splunk_uc.generators.api_surface import _recommender_sourcetypes

    return _recommender_sourcetypes(
        {"q": sidecar.get("spl", "") or "", "d": sidecar.get("dataSources", "") or ""}
    )


def _uc_text(sidecar: Mapping[str, Any]) -> str:
    return " ".join(str(sidecar.get(k, "") or "") for k in ("spl", "dataSources")).lower()


def step_data_keys(
    sidecar: Mapping[str, Any],
    pack: Mapping[str, Any],
    aliases: Mapping[str, str],
) -> tuple[list[str], list[str]]:
    """Return the pack sourcetypes and internal indexes a step actually searches.

    Matches extracted sourcetypes (alias-normalised, with ``vendor:prefix:``
    tokens from ``sourcetype=vendor:prefix:*`` treated as prefixes), then
    literal mentions of a pack sourcetype in the SPL / dataSources text,
    then ``index=<internal>`` mentions for the pack's internal indexes.
    """
    required = pack.get("requiredData") or {}
    pack_sts = {
        normalise_sourcetype(st, aliases): st.strip().lower()
        for st in required.get("sourcetypes") or []
    }
    found: set[str] = set()
    for token in uc_sourcetypes(sidecar):
        norm = normalise_sourcetype(token, aliases)
        if norm in pack_sts:
            found.add(norm)
        elif token.endswith(":"):
            found.update(st for st in pack_sts if st.startswith(token))
    text = _uc_text(sidecar)
    for norm, raw in pack_sts.items():
        if norm in found:
            continue
        if re.search(r"(?<![a-z0-9_:\-])" + re.escape(raw) + r"(?![a-z0-9_\-])", text):
            found.add(norm)
    indexes = [
        idx
        for idx in required.get("indexes") or []
        if re.search(r"index\s*=\s*\"?" + re.escape(idx.lower()) + r"(?![a-z0-9_])", text)
    ]
    return sorted(found), sorted(indexes)


def uc_tier(path: Path, sidecar: Mapping[str, Any]) -> str:
    from splunk_uc.audits import gold_profile

    return str(gold_profile.audit_uc(dict(sidecar), path.resolve())["tier"])


def uc_requires_sme_review(sidecar: Mapping[str, Any]) -> bool:
    for row in sidecar.get("compliance") or []:
        if isinstance(row, dict) and (
            row.get("requires_sme_review") or row.get("requiresSmeReview")
        ):
            return True
    return False


def _uc_category(uc_id: str) -> int:
    try:
        return int(uc_id.removeprefix("UC-").split(".", 1)[0])
    except ValueError:
        return -1


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------


def _validate_schema(pack: Mapping[str, Any]) -> list[str]:
    from jsonschema import Draft202012Validator

    validator = Draft202012Validator(_load_json(SCHEMA_PATH))
    return [
        f"{'/'.join(str(p) for p in err.absolute_path) or '<root>'}: {err.message}"
        for err in sorted(validator.iter_errors(pack), key=lambda e: list(e.absolute_path))
    ]


def audit_alias_groups(groups: list[list[str]]) -> list[Finding]:
    findings: list[Finding] = []
    seen: dict[str, int] = {}
    for idx, group in enumerate(groups):
        for name in group:
            if name in seen and seen[name] != idx:
                findings.append(
                    Finding(
                        "sourcetype-aliases",
                        "error",
                        "alias-duplicate",
                        f"{name!r} appears in more than one alias group",
                    )
                )
            seen[name] = idx
    return findings


def audit_packs(
    packs: Mapping[str, tuple[Path, Mapping[str, Any]]],
    ucs: Mapping[str, tuple[Path, Mapping[str, Any]]],
    *,
    catalog_apps: Mapping[str, Mapping[str, Any]],
    equipment_ids: set[str],
    aliases: Mapping[str, str],
    validate_schema: bool = True,
) -> list[Finding]:
    findings: list[Finding] = []

    def err(pid: str, code: str, msg: str) -> None:
        findings.append(Finding(pid, "error", code, msg))

    def warn(pid: str, code: str, msg: str) -> None:
        findings.append(Finding(pid, "warning", code, msg))

    valid: dict[str, Mapping[str, Any]] = {}
    for stem, (_path, pack) in sorted(packs.items()):
        if validate_schema:
            schema_errors = _validate_schema(pack)
            if schema_errors:
                for msg in schema_errors:
                    err(stem, "schema", msg)
                continue
        if pack.get("id") != stem:
            err(stem, "id-mismatch", f"id {pack.get('id')!r} does not match file name {stem!r}")
            continue
        valid[stem] = pack

    tier_cache: dict[str, str] = {}

    for pid, pack in sorted(valid.items()):
        steps = list(pack.get("steps") or [])
        step_ids = [str(s.get("ucId")) for s in steps]
        orders = sorted(int(s.get("order", 0)) for s in steps)
        if orders != list(range(1, len(steps) + 1)):
            err(pid, "step-order", f"step order values must be 1..{len(steps)}, got {orders}")
        for dup in sorted({u for u in step_ids if step_ids.count(u) > 1}):
            err(pid, "duplicate-step", f"{dup} appears more than once")

        order_of = {str(s.get("ucId")): int(s.get("order", 0)) for s in steps}

        pair_id = pack.get("pairId")
        pair_steps: set[str] = set()
        if pair_id is not None:
            sibling = valid.get(pair_id)
            if sibling is None:
                err(pid, "pair-unknown", f"pairId {pair_id!r} is not a known pack")
            else:
                if sibling.get("pairId") != pid:
                    err(
                        pid,
                        "pair-not-reciprocal",
                        f"{pair_id!r} has pairId {sibling.get('pairId')!r}, expected {pid!r}",
                    )
                if sibling.get("goal") == pack.get("goal"):
                    err(
                        pid,
                        "pair-same-goal",
                        f"pair {pair_id!r} has the same goal {pack.get('goal')!r}",
                    )
                pair_steps = {str(s.get("ucId")) for s in sibling.get("steps") or []}
                if pid < pair_id:
                    for shared in sorted(set(step_ids) & pair_steps):
                        err(pid, "pair-overlap", f"{shared} is in both {pid!r} and {pair_id!r}")

        for nxt in pack.get("nextPacks") or []:
            if nxt == pid:
                err(pid, "next-self", "nextPacks lists the pack itself")
            elif nxt not in valid:
                err(pid, "next-unknown", f"nextPacks entry {nxt!r} is not a known pack")

        for slug in pack.get("equipment") or []:
            if slug not in equipment_ids:
                err(
                    pid,
                    "unknown-equipment",
                    f"equipment {slug!r} is not an EQUIPMENT slug or model id",
                )

        required = pack.get("requiredData") or {}
        pack_app_ids = set()
        for app in required.get("splunkbaseApps") or []:
            app_id = str(app.get("id"))
            pack_app_ids.add(app_id)
            entry = catalog_apps.get(app_id)
            if entry is None:
                err(
                    pid,
                    "unknown-app",
                    f"Splunkbase app {app_id} is not in data/splunkbase-catalog.json",
                )
                continue
            name = str(entry.get("displayName") or "")
            if name != app.get("displayName"):
                err(
                    pid,
                    "app-name",
                    f"app {app_id} displayName {app.get('displayName')!r} != catalog {name!r}",
                )
            if "deprecated" in name.lower() or "archived" in name.lower():
                err(pid, "deprecated-app", f"app {app_id} ({name}) is deprecated or archived")

        pack_equipment = set(pack.get("equipment") or [])
        is_published = pack.get("status") == "published"

        for uc_id in step_ids:
            uc_entry = ucs.get(uc_id)
            if uc_entry is None:
                err(pid, "unknown-uc", f"{uc_id} does not exist under content/")
                continue
            path, sidecar = uc_entry

            if is_published and _uc_category(uc_id) == 25:
                err(
                    pid,
                    "published-cat25",
                    f"{uc_id} is in cat-25; published packs may not include it",
                )

            for pre in sidecar.get("prerequisiteUseCases") or []:
                pre = str(pre)
                if pre in order_of:
                    if order_of[pre] >= order_of[uc_id]:
                        err(
                            pid,
                            "prereq-order",
                            f"{uc_id} (step {order_of[uc_id]}) depends on {pre} (step {order_of[pre]})",
                        )
                elif pre not in pair_steps:
                    warn(
                        pid,
                        "prereq-outside",
                        f"{uc_id} depends on {pre}, which is in neither this pack nor its pair",
                    )

            uc_equipment = set(sidecar.get("equipment") or []) | set(
                sidecar.get("equipmentModels") or []
            )
            if pack_equipment and not (pack_equipment & uc_equipment):
                err(
                    pid,
                    "equipment-coverage",
                    f"{uc_id} equipment {sorted(uc_equipment)} does not overlap pack equipment {sorted(pack_equipment)}",
                )

            sts, idxs = step_data_keys(sidecar, pack, aliases)
            if not sts and not idxs:
                err(
                    pid,
                    "data-coverage",
                    f"{uc_id} searches none of the pack sourcetypes or internal indexes "
                    f"(UC sourcetypes: {uc_sourcetypes(sidecar)})",
                )

            for sb in sidecar.get("splunkbaseApps") or []:
                if not isinstance(sb, dict):
                    continue
                if (
                    str(sb.get("role", "")) in _SB_REQUIRED_ROLES
                    and str(sb.get("id")) not in pack_app_ids
                ):
                    err(
                        pid,
                        "app-coverage",
                        f"{uc_id} needs Splunkbase app {sb.get('id')} ({sb.get('name')}), not in requiredData",
                    )

            status = sidecar.get("status")
            if status != "verified":
                warn(pid, "uc-not-verified", f"{uc_id} has status {status!r} (needs 'verified')")
            if uc_id not in tier_cache:
                tier_cache[uc_id] = uc_tier(path, sidecar)
            if tier_cache[uc_id] not in _SILVER_OR_BETTER:
                warn(
                    pid,
                    "uc-depth",
                    f"{uc_id} is {tier_cache[uc_id]!r} depth (needs silver or gold)",
                )
            if uc_requires_sme_review(sidecar):
                warn(
                    pid, "uc-sme-review", f"{uc_id} has compliance rows tagged requires_sme_review"
                )

        if is_published:
            pack_warnings = [f for f in findings if f.pack_id == pid and f.level == "warning"]
            if pack_warnings:
                err(
                    pid,
                    "published-with-warnings",
                    f"published pack has {len(pack_warnings)} warning(s); resolve them or set status to draft",
                )

    return findings


def run_audit() -> tuple[dict[str, tuple[Path, dict[str, Any]]], list[Finding]]:
    packs = load_packs()
    groups = load_alias_groups()
    findings = audit_alias_groups(groups)
    findings.extend(
        audit_packs(
            packs,
            load_uc_index(),
            catalog_apps=_load_catalog_apps(),
            equipment_ids=_load_equipment_ids(),
            aliases=alias_map(groups),
        )
    )
    return packs, findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit data/starter-packs/*.json (guided onboarding)."
    )
    parser.add_argument("--check", action="store_true", help="CI mode: exit non-zero on errors.")
    parser.add_argument("--json", action="store_true", help="Emit findings as JSON.")
    args = parser.parse_args(argv)

    try:
        packs, findings = run_audit()
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"[starter-packs] ERROR: {exc}", file=sys.stderr)
        return 2

    errors = [f for f in findings if f.level == "error"]
    warnings = [f for f in findings if f.level == "warning"]

    if args.json:
        print(
            json.dumps(
                {
                    "packs": len(packs),
                    "errors": [f.__dict__ for f in errors],
                    "warnings": [f.__dict__ for f in warnings],
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print("=" * 72)
        print("Starter-pack audit (data/starter-packs/*.json)")
        print("=" * 72)
        statuses = {pid: pack.get("status") for pid, (_p, pack) in packs.items()}
        print(
            f"Packs: {len(packs)} "
            f"(published: {sum(1 for s in statuses.values() if s == 'published')}, "
            f"draft: {sum(1 for s in statuses.values() if s == 'draft')})"
        )
        print(f"Errors: {len(errors)}  Warnings (block publish): {len(warnings)}")
        if errors:
            print("\nERRORS:")
            for f in errors:
                print(f"  - {f.render()}")
        if warnings:
            print("\nWARNINGS:")
            for f in warnings:
                print(f"  - {f.render()}")
        if not errors:
            print("\nPASS")

    if errors and args.check:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
