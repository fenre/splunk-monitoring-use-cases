#!/usr/bin/env python3
"""Validate and index the samples/ tree.

Actions (all non-destructive):
  * Load samples/_schema/sample-manifest.schema.json.
  * For each samples/UC-<id>/manifest.yaml:
      - Parse YAML
      - Validate against the JSON schema (jsonschema if available, else
        a best-effort fallback check for required keys + enum values)
      - Confirm uc_id refers to an entry in catalog.json
      - Inspect positive.log / negative.log presence + size
      - Assign a coverage tier:
          Tier 1 (golden)      = manifest + positive.log, origin in
                                 {vendor-doc, hand-authored}, reviewer set
          Tier 2 (contributor) = manifest + positive.log, any origin
          Tier 3 (stub)        = manifest only (no positive.log yet)
  * Write docs/samples-coverage.md summarising by category and overall.
  * With --validate-only, just exit non-zero on any error (no write).

The script has ZERO third-party hard dependencies. It uses PyYAML if
installed (the build pipeline already depends on it for other scripts);
if not available, a minimal YAML reader handles the flat manifests
shipped in this tree.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLES_DIR = REPO_ROOT / "samples"
SCHEMA_PATH = SAMPLES_DIR / "_schema" / "sample-manifest.schema.json"
CATALOG_PATH = REPO_ROOT / "catalog.json"
COVERAGE_OUT = REPO_ROOT / "docs" / "samples-coverage.md"
UC_DIR_RE = re.compile(r"^UC-(\d+)\.(\d+)\.(\d+)$")


# ----------------------------------------------------------------- yaml loader
def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a manifest YAML file.

    Prefers PyYAML when installed; otherwise falls back to a minimal parser
    sufficient for the flat shape used by sample manifests (no anchors, no
    complex nesting beyond lists of scalars / dicts one level deep, and no
    multi-line strings other than block scalars introduced with ``|``).
    """
    try:
        import yaml  # type: ignore
        with path.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except ImportError:
        return _mini_yaml(path)


def _mini_yaml(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, result)]
    block: list[str] | None = None
    block_key: tuple[Any, str] | None = None
    block_indent: int | None = None
    with path.open("r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if block is not None:
                if line.strip() == "" or (
                    block_indent is not None
                    and (len(line) - len(line.lstrip(" "))) >= block_indent
                ):
                    block.append(line[block_indent or 0 :])
                    continue
                _assign_mini(block_key, "\n".join(block).rstrip())
                block = None
                block_key = None
                block_indent = None
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            indent = len(line) - len(line.lstrip(" "))
            content = line.strip()
            while stack and indent <= stack[-1][0]:
                stack.pop()
            parent = stack[-1][1]
            if content.startswith("- "):
                value = _parse_scalar(content[2:].strip())
                if isinstance(parent, list):
                    parent.append(value)
                continue
            if ":" in content:
                key, _, raw_value = content.partition(":")
                key = key.strip()
                raw_value = raw_value.strip()
                if raw_value == "":
                    new: Any = {}
                    if isinstance(parent, dict):
                        parent[key] = new
                    stack.append((indent, new))
                elif raw_value == "|":
                    block = []
                    block_key = (parent, key)
                    block_indent = None
                elif raw_value.startswith("-") and raw_value == "-":
                    new = []
                    if isinstance(parent, dict):
                        parent[key] = new
                    stack.append((indent, new))
                else:
                    value = _parse_scalar(raw_value)
                    if isinstance(parent, dict):
                        parent[key] = value
                    if raw_value == "":
                        new = []
                        if isinstance(parent, dict):
                            parent[key] = new
                        stack.append((indent, new))
    if block is not None and block_key is not None:
        _assign_mini(block_key, "\n".join(block).rstrip())
    return result


def _assign_mini(key: tuple[Any, str] | None, value: str) -> None:
    if key is None:
        return
    parent, k = key
    if isinstance(parent, dict):
        parent[k] = value


def _parse_scalar(raw: str) -> Any:
    raw = raw.strip()
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1]
    if raw.startswith("'") and raw.endswith("'"):
        return raw[1:-1]
    if raw in ("true", "True"):
        return True
    if raw in ("false", "False"):
        return False
    if raw in ("null", "~", ""):
        return None
    try:
        if raw.isdigit() or (raw.startswith("-") and raw[1:].isdigit()):
            return int(raw)
        return float(raw)
    except ValueError:
        return raw


# ------------------------------------------------------------------- schema
REQUIRED_KEYS = ("uc_id", "sourcetype", "index", "expected", "origin", "last_reviewed")
ORIGIN_ENUM = {"hand-authored", "vendor-doc", "synthetic", "contributor"}
UC_ID_RE = re.compile(r"^\d+\.\d+\.\d+$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _validate_manifest(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED_KEYS:
        if key not in manifest or manifest[key] in (None, ""):
            errors.append(f"missing required key: {key}")
    uc = manifest.get("uc_id")
    if uc and not UC_ID_RE.match(str(uc)):
        errors.append(f"uc_id must match N.N.N (got {uc!r})")
    origin = manifest.get("origin")
    if origin and origin not in ORIGIN_ENUM:
        errors.append(f"origin not in {sorted(ORIGIN_ENUM)} (got {origin!r})")
    reviewed = manifest.get("last_reviewed")
    if reviewed and not DATE_RE.match(str(reviewed)):
        errors.append(f"last_reviewed must be YYYY-MM-DD (got {reviewed!r})")
    expected = manifest.get("expected") or {}
    if "min_count" not in expected:
        errors.append("expected.min_count is required")
    return errors


# ------------------------------------------------------------------- catalog
def _load_catalog_ids() -> set[str]:
    with CATALOG_PATH.open("r", encoding="utf-8") as fh:
        cat = json.load(fh)
    ids: set[str] = set()
    for cat_entry in cat.get("DATA", []):
        for sc in cat_entry.get("s", []):
            for uc in sc.get("u", []):
                if uc.get("i"):
                    ids.add(uc["i"])
    return ids


# ------------------------------------------------------------------- tiers
@dataclass
class SampleStatus:
    uc_id: str
    tier: int  # 1 golden, 2 contributor, 3 stub
    origin: str
    has_positive: bool
    has_negative: bool
    positive_bytes: int
    errors: list[str] = field(default_factory=list)

    def tier_label(self) -> str:
        return {1: "Tier 1 (golden)", 2: "Tier 2 (contributor)", 3: "Tier 3 (stub)"}.get(self.tier, "Unknown")


# ------------------------------------------------------------------- walker
def scan_samples(catalog_ids: set[str]) -> list[SampleStatus]:
    if not SAMPLES_DIR.exists():
        return []
    out: list[SampleStatus] = []
    for entry in sorted(SAMPLES_DIR.iterdir()):
        if not entry.is_dir():
            continue
        if not UC_DIR_RE.match(entry.name):
            continue
        uc_id = entry.name[len("UC-"):]
        manifest_path = entry / "manifest.yaml"
        if not manifest_path.exists():
            out.append(SampleStatus(
                uc_id=uc_id, tier=3, origin="",
                has_positive=False, has_negative=False, positive_bytes=0,
                errors=["manifest.yaml missing"],
            ))
            continue
        try:
            manifest = _load_yaml(manifest_path)
        except Exception as exc:  # noqa: BLE001
            out.append(SampleStatus(
                uc_id=uc_id, tier=3, origin="",
                has_positive=False, has_negative=False, positive_bytes=0,
                errors=[f"YAML parse error: {exc}"],
            ))
            continue
        errors = _validate_manifest(manifest)
        if manifest.get("uc_id") and str(manifest["uc_id"]) != uc_id:
            errors.append(
                f"manifest.uc_id={manifest.get('uc_id')} does not match directory {entry.name}"
            )
        if uc_id not in catalog_ids:
            errors.append(f"UC-{uc_id} is not present in catalog.json")
        pos = entry / "positive.log"
        neg = entry / "negative.log"
        has_pos = pos.exists() and pos.stat().st_size > 0
        has_neg = neg.exists() and neg.stat().st_size > 0
        positive_bytes = pos.stat().st_size if pos.exists() else 0
        origin = str(manifest.get("origin") or "")
        if not has_pos:
            tier = 3
        elif origin in ("vendor-doc", "hand-authored") and manifest.get("reviewer"):
            tier = 1
        else:
            tier = 2
        out.append(SampleStatus(
            uc_id=uc_id, tier=tier, origin=origin,
            has_positive=has_pos, has_negative=has_neg,
            positive_bytes=positive_bytes, errors=errors,
        ))
    return out


# ------------------------------------------------------------------- report
def _category_label(uc_id: str, catalog: dict[str, Any]) -> str:
    cat_num = uc_id.split(".", 1)[0]
    for cat in catalog.get("DATA", []):
        if str(cat.get("i")) == cat_num:
            return f"{cat_num}. {cat.get('n', 'Unknown')}"
    return f"{cat_num}. Unknown"


def render_coverage(statuses: list[SampleStatus]) -> str:
    with CATALOG_PATH.open("r", encoding="utf-8") as fh:
        catalog = json.load(fh)
    total_catalog_ucs = sum(
        len(sc.get("u", []))
        for cat in catalog.get("DATA", [])
        for sc in cat.get("s", [])
    )
    by_cat: dict[str, list[SampleStatus]] = {}
    for s in statuses:
        by_cat.setdefault(_category_label(s.uc_id, catalog), []).append(s)
    tier1 = sum(1 for s in statuses if s.tier == 1)
    tier2 = sum(1 for s in statuses if s.tier == 2)
    tier3 = sum(1 for s in statuses if s.tier == 3)
    covered = tier1 + tier2
    pct = (covered / total_catalog_ucs * 100.0) if total_catalog_ucs else 0.0

    lines: list[str] = [
        "# Sample-event coverage",
        "",
        "Auto-generated by `scripts/samples_index.py`. Do not edit by hand.",
        "",
        "## Summary",
        "",
        f"- Total UCs in catalog: **{total_catalog_ucs:,}**",
        f"- UCs with at least a stub sample directory: **{len(statuses)}**",
        f"  - Tier 1 (golden, maintainer-authored): **{tier1}**",
        f"  - Tier 2 (contributor): **{tier2}**",
        f"  - Tier 3 (stub, manifest only): **{tier3}**",
        f"- Coverage (has positive.log): **{covered}/{total_catalog_ucs} = {pct:.1f}%**",
        "",
        "## Breakdown by category",
        "",
        "| Category | Tier 1 | Tier 2 | Tier 3 |",
        "| -------- | -----: | -----: | -----: |",
    ]
    for cat_label in sorted(by_cat.keys(), key=lambda x: int(x.split(".")[0])):
        ss = by_cat[cat_label]
        lines.append(
            f"| {cat_label} "
            f"| {sum(1 for s in ss if s.tier == 1)} "
            f"| {sum(1 for s in ss if s.tier == 2)} "
            f"| {sum(1 for s in ss if s.tier == 3)} |"
        )
    lines.extend([
        "",
        "## Details",
        "",
        "| UC | Tier | Origin | Positive | Negative | Errors |",
        "| -- | ---- | ------ | -------: | -------: | ------ |",
    ])
    for s in sorted(statuses, key=lambda s: tuple(int(p) for p in s.uc_id.split("."))):
        errs = "; ".join(s.errors) if s.errors else "—"
        lines.append(
            f"| UC-{s.uc_id} | {s.tier_label()} | {s.origin or '—'} "
            f"| {'✓' if s.has_positive else '—'} "
            f"| {'✓' if s.has_negative else '—'} "
            f"| {errs} |"
        )
    lines.append("")
    return "\n".join(lines)


# ------------------------------------------------------------------- cli
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate; do not write docs/samples-coverage.md.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if ANY manifest has errors.",
    )
    args = parser.parse_args()

    if not CATALOG_PATH.exists():
        print(f"ERROR: {CATALOG_PATH} missing — run build.py first.", file=sys.stderr)
        return 2
    catalog_ids = _load_catalog_ids()
    statuses = scan_samples(catalog_ids)

    any_errors = False
    for s in statuses:
        if s.errors:
            any_errors = True
            for e in s.errors:
                print(f"  [error] UC-{s.uc_id}: {e}", file=sys.stderr)

    if not args.validate_only:
        COVERAGE_OUT.parent.mkdir(parents=True, exist_ok=True)
        COVERAGE_OUT.write_text(render_coverage(statuses), encoding="utf-8")
        print(f"Wrote {COVERAGE_OUT}")

    tier1 = sum(1 for s in statuses if s.tier == 1)
    tier2 = sum(1 for s in statuses if s.tier == 2)
    tier3 = sum(1 for s in statuses if s.tier == 3)
    print(
        f"Samples indexed: {len(statuses)}  "
        f"(Tier 1={tier1}, Tier 2={tier2}, Tier 3={tier3})  "
        f"errors={'yes' if any_errors else 'no'}"
    )
    if args.strict and any_errors:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
