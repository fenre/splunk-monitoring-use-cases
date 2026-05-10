#!/usr/bin/env python3
"""Propose ``splunkbaseApps[]`` arrays for UC sidecars (v9.0 migration).

Schema field ``splunkbaseApps[]`` was added in ``uc.schema.json`` v1.7.0
(see ``schemas/changelogs/uc.md``). The recommender app
(``splunk-uc-recommender``) consumes this array to render the per-card
"Required Splunkbase apps" section and to compute install-guidance status.
This script joins the existing UC fields (``app``, ``premiumApps``,
``equipment``, ``dataSources``) against ``data/splunkbase-catalog.json`` and
proposes a structured mapping for every UC, **always** flagging the proposed
entry with ``requiresSmeReview: true``. A human signs each entry off in a
separate review pass (see ``docs/sme-review-guide.md``); the audits in
``tools/audits/splunkbase_coverage.py`` track the open-review backlog.

Heuristics (in priority order, never overwrite a human-signed entry):

1. ``app`` (free-form string) — regex-extract Splunkbase ids from
   ``Splunkbase NNNN`` and from ``splunkbase.splunk.com/app/NNNN`` URL forms.
   Role: ``primary`` (the app the UC is built on).
2. ``premiumApps`` (canonical 11-item enum or object form) — direct lookup
   against a hand-curated alias table. Role: ``premium``.
3. ``equipment`` / ``equipmentModels`` — equipment slug → catalog entries
   whose ``displayName``, ``name``, or ``vendor`` field contains the slug or
   its label. Role: ``data-source``.
4. ``dataSources`` (free-form) — substring match against catalog
   ``displayName`` and ``name``. Role: ``data-source``.

Idempotency contract:

* If a UC already has a ``splunkbaseApps[]`` entry **without**
  ``requiresSmeReview: true`` (i.e. a human signed it off), this generator
  preserves it byte-for-byte.
* If every entry in the existing ``splunkbaseApps[]`` carries
  ``requiresSmeReview: true``, the generator may rewrite the array in full.
* If the proposed array is identical to the existing array, nothing is
  written (file mtime stays untouched, generator exit-code is 0).

CLI:

    python3 scripts/generate_splunkbase_mappings.py --check
    python3 scripts/generate_splunkbase_mappings.py --write
    python3 scripts/generate_splunkbase_mappings.py --write --uc UC-1.1.1
    python3 scripts/generate_splunkbase_mappings.py --write --cat 5

``--check`` (default) prints coverage statistics and exits 0; never writes.
``--write`` rewrites UC sidecars whose proposed array differs from disk.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from typing import Any

# P6 (scripts taxonomy, 2026-05-10) relocated this generator from
# scripts/generate_splunkbase_mappings.py to
# src/splunk_uc/generators/splunkbase_mappings.py. parents[3] resolves:
# splunkbase_mappings.py -> generators/ -> splunk_uc/ -> src/ -> repo root.
# The legacy shim at scripts/generate_splunkbase_mappings.py re-exports
# ``main`` so sibling-script docstring references (sync_splunkbase_catalog.py,
# review_splunkbase_mappings.py) and any direct CLI invocation still work.
REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
CONTENT_DIR = REPO_ROOT / "content"
CATALOG_PATH = REPO_ROOT / "data" / "splunkbase-catalog.json"
OVERRIDES_PATH = REPO_ROOT / "data" / "splunkbase-catalog-overrides.json"

UC_FILE_GLOB = "cat-*/UC-*.json"

# Canonical premium-app enum → Splunkbase numeric id.
# These are the apps named in schemas/uc.schema.json#/properties/premiumApps.
# Pulled from publicly visible Splunkbase URLs; the audit
# tools/audits/splunkbase_ids.py keeps these in sync with the live catalog.
PREMIUM_APP_IDS: dict[str, int] = {
    "splunk enterprise security": 263,
    "splunk itsi": 1841,
    "splunk it service intelligence": 1841,
    "splunk soar": 5613,
    "splunk user behavior analytics": 4796,
    "splunk uba": 4796,
    "splunk app for pci compliance": 2897,
    "splunk edge hub": 6135,
    "splunk machine learning toolkit": 2890,
    "splunk mltk": 2890,
}

ROLE_PRIMARY = "primary"
ROLE_DATA_SOURCE = "data-source"
ROLE_PREMIUM = "premium"
ROLE_OPTIONAL = "optional"

SPLUNKBASE_ID_RE = re.compile(
    r"(?:Splunkbase\s+|splunkbase\.splunk\.com/app/)(\d{2,6})", re.IGNORECASE
)


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return payload


def _write_json_preserving_style(path: pathlib.Path, body: dict[str, Any]) -> None:
    """Write a UC sidecar back with the project's house style (2-space indent,
    UTF-8, trailing newline). We deliberately do NOT sort keys — UC sidecars
    have a curated key order that the build pipeline relies on for diff
    readability.
    """
    payload = json.dumps(body, indent=2, ensure_ascii=False) + "\n"
    path.write_text(payload, encoding="utf-8")


def _load_catalog() -> dict[str, dict[str, Any]]:
    """Return the merged (catalog + overrides) ``apps`` map keyed by str id."""
    catalog = _read_json(CATALOG_PATH)
    overrides = _read_json(OVERRIDES_PATH)
    apps: dict[str, dict[str, Any]] = {}
    for key, entry in (catalog.get("apps") or {}).items():
        if isinstance(entry, dict):
            apps[str(key)] = dict(entry)
    for key, entry in (overrides.get("apps") or {}).items():
        if not isinstance(entry, dict):
            continue
        if str(key) in apps:
            apps[str(key)].update(entry)
        else:
            apps[str(key)] = dict(entry)
    return apps


# ---------------------------------------------------------------------------
# Heuristics
# ---------------------------------------------------------------------------


def _extract_premium_app_ids(uc: dict[str, Any]) -> list[tuple[int, str]]:
    """Return ``[(id, displayName_hint)]`` for every premium app referenced."""
    out: list[tuple[int, str]] = []
    for raw in uc.get("premiumApps") or []:
        name = raw if isinstance(raw, str) else (raw.get("name") if isinstance(raw, dict) else None)
        if not isinstance(name, str):
            continue
        key = name.strip().lower()
        if key in PREMIUM_APP_IDS:
            out.append((PREMIUM_APP_IDS[key], name.strip()))
    return out


def _extract_app_field_ids(uc: dict[str, Any]) -> list[int]:
    """Pull every numeric Splunkbase id mentioned in the free-form ``app`` field."""
    text = uc.get("app") or ""
    if not isinstance(text, str):
        return []
    seen: set[int] = set()
    out: list[int] = []
    for match in SPLUNKBASE_ID_RE.finditer(text):
        try:
            value = int(match.group(1))
        except ValueError:
            continue
        if value <= 0 or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _equipment_match(uc: dict[str, Any], catalog: dict[str, dict[str, Any]]) -> list[int]:
    """Match equipment slugs/labels against the catalog ``name``/``displayName``.

    We use a conservative substring match (case-insensitive). Only returns
    catalog ids that are not already returned by stronger signals.
    """

    out: set[int] = set()
    needles: set[str] = set()
    for slug in uc.get("equipment") or []:
        if isinstance(slug, str):
            normalised = slug.strip().lower()
            if len(normalised) >= 4:
                needles.add(normalised)
                # equipment slugs are kebab-case (e.g. cisco-meraki) so also
                # try the hyphen-stripped variant for substring matching.
                needles.add(normalised.replace("-", " "))
                needles.add(normalised.replace("-", "_"))
    for compound in uc.get("equipmentModels") or []:
        if isinstance(compound, str) and "_" in compound:
            slug = compound.split("_", 1)[0]
            if len(slug) >= 4:
                needles.add(slug.lower())

    if not needles:
        return []

    for app_id_str, entry in catalog.items():
        try:
            app_id = int(app_id_str)
        except ValueError:
            continue
        haystack = " ".join(
            str(entry.get(k) or "") for k in ("name", "displayName", "vendor")
        ).lower()
        if not haystack.strip():
            continue
        for needle in needles:
            if needle and needle in haystack:
                out.add(app_id)
                break
    return sorted(out)


def _data_source_match(uc: dict[str, Any], catalog: dict[str, dict[str, Any]]) -> list[int]:
    """Substring-match the free-form ``dataSources`` text against the catalog.

    We bias towards catalog ``name`` (often the TA stanza name like
    ``Splunk_TA_cisco-meraki``) because that string is most likely to appear
    verbatim in ``dataSources``; ``displayName`` is a softer match.
    """

    text = uc.get("dataSources") or ""
    if not isinstance(text, str) or len(text) < 8:
        return []
    haystack = text.lower()

    out: set[int] = set()
    for app_id_str, entry in catalog.items():
        try:
            app_id = int(app_id_str)
        except ValueError:
            continue
        for field in ("name", "displayName"):
            value = entry.get(field)
            if isinstance(value, str) and len(value) >= 8 and value.lower() in haystack:
                out.add(app_id)
                break
    return sorted(out)


def _build_proposal(
    uc: dict[str, Any],
    catalog: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Compose the proposed ``splunkbaseApps[]`` array for one UC.

    Roles are assigned by signal strength: ``primary`` (app field) outranks
    ``premium`` outranks ``data-source``. We emit at most one entry per id;
    if the same id is matched by multiple heuristics we keep the strongest
    role.
    """

    role_rank = {ROLE_PRIMARY: 3, ROLE_PREMIUM: 2, ROLE_DATA_SOURCE: 1, ROLE_OPTIONAL: 0}
    chosen: dict[int, tuple[str, dict[str, Any]]] = {}

    def _consider(app_id: int, role: str) -> None:
        if app_id <= 0:
            return
        catalog_entry = catalog.get(str(app_id))
        if not isinstance(catalog_entry, dict):
            return
        existing = chosen.get(app_id)
        if existing and role_rank[existing[0]] >= role_rank[role]:
            return
        chosen[app_id] = (role, catalog_entry)

    for app_id in _extract_app_field_ids(uc):
        _consider(app_id, ROLE_PRIMARY)
    for app_id, _hint in _extract_premium_app_ids(uc):
        _consider(app_id, ROLE_PREMIUM)
    for app_id in _equipment_match(uc, catalog):
        _consider(app_id, ROLE_DATA_SOURCE)
    for app_id in _data_source_match(uc, catalog):
        _consider(app_id, ROLE_DATA_SOURCE)

    proposal: list[dict[str, Any]] = []
    for app_id, (role, entry) in sorted(chosen.items()):
        item: dict[str, Any] = {
            "id": app_id,
            "name": (entry.get("displayName") or entry.get("name") or f"Splunkbase app {app_id}"),
            "url": entry.get("url") or f"https://splunkbase.splunk.com/app/{app_id}",
            "role": role,
            "requiresSmeReview": True,
        }
        if isinstance(entry.get("latestVersion"), str) and entry["latestVersion"]:
            # We do not pin a minVersion automatically — that's an SME call.
            # Leaving it out keeps the proposal honest: SMEs add minVersion
            # only when the UC's SPL or fields actually require a feature.
            pass
        proposal.append(item)
    return proposal


def _existing_human_signed(uc: dict[str, Any]) -> bool:
    """True iff the existing splunkbaseApps[] has any entry without
    requiresSmeReview: true (i.e. a human signed at least one entry off)."""
    existing = uc.get("splunkbaseApps")
    if not isinstance(existing, list) or not existing:
        return False
    for entry in existing:
        if not isinstance(entry, dict):
            continue
        if not entry.get("requiresSmeReview", False):
            return True
    return False


def _arrays_equal(a: Any, b: Any) -> bool:
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


# ---------------------------------------------------------------------------
# UC discovery and update
# ---------------------------------------------------------------------------


def _discover_ucs(filter_uc_id: str | None, filter_cat: str | None) -> list[pathlib.Path]:
    paths = sorted(CONTENT_DIR.glob(UC_FILE_GLOB))
    if filter_uc_id:
        prefix = filter_uc_id[:].removeprefix("UC-")
        paths = [p for p in paths if p.stem == f"UC-{prefix}"]
    if filter_cat:
        paths = [p for p in paths if p.parent.name.startswith(f"cat-{int(filter_cat):02d}-")]
    return paths


def _update_uc_in_place(uc: dict[str, Any], proposal: list[dict[str, Any]]) -> dict[str, Any]:
    """Return a new UC dict with ``splunkbaseApps`` replaced by ``proposal``.

    Insertion order: drop the existing key (if present), then append the new
    field at the same position the schema reads (``app`` is the closest
    sibling). Python dicts preserve insertion order so we rebuild minimally.
    """

    out: dict[str, Any] = {}
    inserted = False
    for key, value in uc.items():
        if key == "splunkbaseApps":
            continue
        out[key] = value
        if key == "app" and not inserted and proposal:
            out["splunkbaseApps"] = proposal
            inserted = True
    if proposal and not inserted:
        out["splunkbaseApps"] = proposal
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Dry-run (default).")
    mode.add_argument(
        "--write", action="store_true", help="Rewrite UC sidecars with proposed mappings."
    )
    parser.add_argument(
        "--uc",
        help="Limit to a single UC id (with or without 'UC-' prefix).",
    )
    parser.add_argument(
        "--cat",
        help="Limit to a single category number (e.g. '5' or '05').",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-UC stdout logging.",
    )
    args = parser.parse_args(argv)

    catalog = _load_catalog()
    if not catalog:
        print(
            "[generate_splunkbase_mappings] data/splunkbase-catalog.json is empty; "
            "run scripts/sync_splunkbase_catalog.py --sync first.",
            file=sys.stderr,
        )

    uc_paths = _discover_ucs(args.uc, args.cat)
    if not uc_paths:
        print("[generate_splunkbase_mappings] no UCs matched the filter.", file=sys.stderr)
        return 0

    total = len(uc_paths)
    proposed_total = 0
    rewrote = 0
    skipped_human_signed = 0
    no_match = 0

    for path in uc_paths:
        try:
            uc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as err:
            print(f"[generate_splunkbase_mappings] {path}: {err}", file=sys.stderr)
            continue

        if _existing_human_signed(uc):
            skipped_human_signed += 1
            continue

        proposal = _build_proposal(uc, catalog)
        if not proposal:
            no_match += 1
            continue

        proposed_total += len(proposal)
        existing = uc.get("splunkbaseApps") or []
        if _arrays_equal(existing, proposal):
            continue

        if args.write:
            new_uc = _update_uc_in_place(uc, proposal)
            _write_json_preserving_style(path, new_uc)
            rewrote += 1
            if not args.quiet:
                print(f"[generate_splunkbase_mappings] wrote {path.relative_to(REPO_ROOT)}")
        elif not args.quiet:
            print(
                f"[generate_splunkbase_mappings] would write {path.relative_to(REPO_ROOT)}: "
                f"{len(proposal)} entries (was {len(existing)})"
            )

    print(
        f"[generate_splunkbase_mappings] scanned={total} "
        f"rewrote={rewrote if args.write else 0} "
        f"would_write={(0 if args.write else proposed_total)} "
        f"skipped_human_signed={skipped_human_signed} "
        f"no_catalog_match={no_match} "
        f"catalog_size={len(catalog)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
