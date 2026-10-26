#!/usr/bin/env python3
"""Generate ``api/v1/starter-packs/`` from ``data/starter-packs/*.json``.

Guided onboarding Phase 1. Sibling of ``generate-api-surface``: the
``starter-packs`` sub-tree is listed in ``api_surface._EXTERNAL_SUBTREES``
so the api-surface rmtree / drift check leaves it alone.

Outputs (deterministic, no timestamps):

* ``api/v1/starter-packs/index.json`` — every pack (draft and published),
  each step resolved against its UC sidecar (title, criticality, authored
  difficulty, wave, status) plus the data keys the step searches, the
  pack's audit readiness, and the sourcetype alias groups. One fetch is
  enough for the wizard, the paste matcher, and the MCP planner.
* ``api/v1/starter-packs/{id}.json`` — the same record for one pack.
* ``api/v1/starter-packs/index.html`` — the same list as a readable page.
  The markup is static; the page fetches ``index.json``.

Consumers filter ``status == "published"`` by default; drafts are kept in
the payload so curators can preview them.

Inputs are the pack files, UC sidecars, ``data/sourcetype-aliases.json``,
and ``VERSION`` only, so ``--check`` is hermetic.

Usage::

    python3 -m splunk_uc generate-starter-packs
    python3 -m splunk_uc generate-starter-packs --check
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from splunk_uc.audits import starter_packs as audit

REPO_ROOT = Path(__file__).resolve().parents[3]
API_OUT_DIR = REPO_ROOT / "api" / "v1" / "starter-packs"
VERSION_PATH = REPO_ROOT / "VERSION"
BROWSER_PAGE = Path(__file__).resolve().parent / "starter_pack_browser.html"
API_VERSION = "v1"


def _read_version() -> str:
    if VERSION_PATH.is_file():
        return VERSION_PATH.read_text(encoding="utf-8").strip()
    return "0.0.0"


def _resolve_step(
    step: Mapping[str, Any],
    pack: Mapping[str, Any],
    ucs: Mapping[str, tuple[Path, Mapping[str, Any]]],
    aliases: Mapping[str, str],
) -> dict[str, Any]:
    uc_id = str(step["ucId"])
    record: dict[str, Any] = {"order": int(step["order"]), "ucId": uc_id}
    entry = ucs.get(uc_id)
    if entry is None:
        return record
    _path, sidecar = entry
    sourcetypes, indexes = audit.step_data_keys(sidecar, pack, aliases)
    record.update(
        {
            "title": str(sidecar.get("title", "")),
            "criticality": str(sidecar.get("criticality", "") or ""),
            "difficulty": str(sidecar.get("difficulty", "") or ""),
            "wave": str(sidecar.get("wave", "") or ""),
            "status": str(sidecar.get("status", "") or "unreviewed"),
            "prerequisiteUseCases": sorted(
                str(p) for p in sidecar.get("prerequisiteUseCases") or []
            ),
            "sourcetypes": sourcetypes,
            "indexes": indexes,
            "url": f"/uc/{uc_id}/",
            "json": f"/uc/{uc_id}/index.json",
            "markdown": f"/uc/{uc_id}/uc.md",
        }
    )
    return record


def build_payloads(
    packs: Mapping[str, tuple[Path, Mapping[str, Any]]],
    ucs: Mapping[str, tuple[Path, Mapping[str, Any]]],
    findings: list[audit.Finding],
    alias_groups: list[list[str]],
    version: str,
) -> dict[str, dict[str, Any]]:
    """Return ``relative file name -> JSON payload``."""
    aliases = audit.alias_map(alias_groups)
    records: list[dict[str, Any]] = []
    for pid, (_path, pack) in sorted(packs.items()):
        pack_findings = [f for f in findings if f.pack_id == pid]
        warnings = [
            {"code": f.code, "message": f.message} for f in pack_findings if f.level == "warning"
        ]
        errors = [
            {"code": f.code, "message": f.message} for f in pack_findings if f.level == "error"
        ]
        steps = sorted(pack.get("steps") or [], key=lambda s: int(s.get("order", 0)))
        record = {k: v for k, v in pack.items() if k != "$schema"}
        record["steps"] = [_resolve_step(s, pack, ucs, aliases) for s in steps]
        record["stepCount"] = len(steps)
        record["readiness"] = {
            "publishable": not warnings and not errors,
            "warnings": warnings,
            "errors": errors,
        }
        record["url"] = f"/api/{API_VERSION}/starter-packs/{pid}.json"
        records.append(record)

    out: dict[str, dict[str, Any]] = {}
    for record in records:
        out[f"{record['id']}.json"] = {
            "apiVersion": API_VERSION,
            "catalogueVersion": version,
            "schema": "/schemas/starter-pack.schema.json",
            "pack": record,
        }
    out["index.json"] = {
        "apiVersion": API_VERSION,
        "catalogueVersion": version,
        "schema": "/schemas/starter-pack.schema.json",
        "description": (
            "Guided-onboarding starter packs: ordered use cases per data source "
            "and goal (security or operations). Show only status=published "
            "packs to end users; drafts are included for curators."
        ),
        "packCount": len(records),
        "publishedCount": sum(1 for r in records if r.get("status") == "published"),
        "sourcetypeAliases": [list(g) for g in alias_groups],
        "packs": records,
    }
    return out


def render(out_dir: Path) -> list[Path]:
    packs = audit.load_packs()
    ucs = audit.load_uc_index()
    groups = audit.load_alias_groups()
    findings = audit.audit_packs(
        packs,
        ucs,
        catalog_apps=audit._load_catalog_apps(),
        equipment_ids=audit._load_equipment_ids(),
        aliases=audit.alias_map(groups),
    )
    payloads = build_payloads(packs, ucs, findings, groups, _read_version())
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, payload in sorted(payloads.items()):
        path = out_dir / name
        path.write_text(
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        written.append(path)
    page = out_dir / "index.html"
    page.write_bytes(BROWSER_PAGE.read_bytes())
    written.append(page)
    return written


def _surface_names(directory: Path) -> set[str]:
    return {p.name for p in directory.iterdir() if p.is_file() and p.suffix in {".json", ".html"}}


def _diff(fresh: Path, on_disk: Path) -> list[str]:
    fresh_files = _surface_names(fresh)
    disk_files = _surface_names(on_disk)
    diffs: list[str] = []
    for name in sorted(fresh_files | disk_files):
        if name not in disk_files:
            diffs.append(f"+ {name}  (missing on disk)")
        elif name not in fresh_files:
            diffs.append(f"- {name}  (stale on disk)")
        elif (fresh / name).read_bytes() != (on_disk / name).read_bytes():
            diffs.append(f"~ {name}")
    return diffs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate api/v1/starter-packs/ (guided onboarding)."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "Render into a temp dir and diff against api/v1/starter-packs/. "
            "The api/ tree is gitignored, so when it has not been generated "
            "yet the check only proves the render succeeds."
        ),
    )
    parser.add_argument("--out", type=Path, default=API_OUT_DIR)
    args = parser.parse_args(argv)

    if args.check:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            written = render(tmp_path)
            if not args.out.is_dir():
                print(
                    f"Rendered {len(written)} starter-pack files (no {args.out} on disk to diff)."
                )
                return 0
            diffs = _diff(tmp_path, args.out)
            if diffs:
                print(
                    "Starter-pack API is stale. Run `python -m splunk_uc generate-starter-packs`.",
                    file=sys.stderr,
                )
                for line in diffs:
                    print(f"  {line}", file=sys.stderr)
                return 1
            print("Starter-pack API is up to date.")
            return 0

    if args.out.is_dir():
        for stale in args.out.glob("*.json"):
            stale.unlink()
    written = render(args.out)
    try:
        shown = args.out.relative_to(REPO_ROOT)
    except ValueError:
        shown = args.out
    print(f"Wrote {len(written)} files under {shown}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
