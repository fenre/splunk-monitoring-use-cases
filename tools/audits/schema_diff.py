#!/usr/bin/env python3
"""tools.audits.schema_diff — detect breaking changes to JSON Schemas.

Walks every ``schemas/**/*.schema.json``, loads the matching baseline
copy from a git tag, and classifies each change as

* ``additive``   (new optional property, new enum value, new ``$defs`` entry, ...)
* ``breaking``   (remove/rename/narrow type, shrink enum, tighten constraint, ...)
* ``metadata``   (description, examples, ``title``)

Cross-checks the change class against the schema's ``version`` bump per
docs/schema-versioning.md.

Usage
-----
    python3 tools/audits/schema_diff.py --baseline-tag v7.0.0
    python3 tools/audits/schema_diff.py --baseline-tag v7.0.0 --schemas schemas

Exit codes
----------
0 — no breaking changes, or every breaking change ships under a fresh ``$id``
1 — at least one ``stable`` schema breaks without a major bump + new $id
2 — invocation error
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="schema_diff")
    parser.add_argument("--baseline-tag", required=True, help="git tag for the baseline.")
    parser.add_argument("--schemas", default="schemas", help="Schemas root.")
    args = parser.parse_args(argv)

    root = Path(args.schemas).resolve()
    if not root.exists():
        sys.stderr.write(f"[schema_diff] missing schemas dir: {root}\n")
        return 2

    fail = False
    total = 0
    for path in sorted(root.rglob("*.schema.json")):
        total += 1
        rel = path.relative_to(Path.cwd().resolve()).as_posix() \
            if path.is_relative_to(Path.cwd().resolve()) else str(path)
        baseline = _load_baseline(args.baseline_tag, rel)
        head = _safe_load(path)
        if baseline is None or head is None:
            continue

        changes = _classify(baseline, head)
        if not changes["breaking"] and not changes["additive"]:
            continue

        head_stability = head.get("x-stability", "preview")
        head_version = head.get("version", "0.0.0")
        baseline_version = baseline.get("version", "0.0.0")
        bump = _bump_kind(baseline_version, head_version)
        head_id = head.get("$id", "")
        baseline_id = baseline.get("$id", "")

        problems: list[str] = []
        if changes["breaking"]:
            if head_stability == "stable":
                if bump != "major":
                    problems.append(
                        f"breaking change without major bump (was {baseline_version}, now {head_version})"
                    )
                if head_id == baseline_id:
                    problems.append(
                        f"breaking change without fresh $id "
                        f"(both schemas share {head_id!r}; bump the major in the URL)"
                    )
        if changes["additive"] and bump == "patch":
            problems.append(
                f"additive change with patch bump only (was {baseline_version}, now {head_version}); minor required"
            )

        prefix = "[schema_diff]"
        if problems:
            fail = True
            sys.stderr.write(f"{prefix} FAIL {rel}\n")
            for p in problems:
                sys.stderr.write(f"           - {p}\n")
            for c in changes["breaking"][:5]:
                sys.stderr.write(f"           ! breaking: {c}\n")
            for c in changes["additive"][:5]:
                sys.stderr.write(f"           + additive: {c}\n")
        else:
            sys.stdout.write(
                f"{prefix} OK   {rel} ({len(changes['breaking'])} breaking, "
                f"{len(changes['additive'])} additive — version {baseline_version} -> {head_version})\n"
            )

    if fail:
        sys.stderr.write(
            "\nSee docs/schema-versioning.md for the full contract.\n"
        )
        return 1
    sys.stdout.write(f"[schema_diff] {total} schema(s) checked. OK.\n")
    return 0


# ---------------------------------------------------------------------------
# Baseline loader
# ---------------------------------------------------------------------------

def _load_baseline(tag: str, path: str) -> dict | None:
    try:
        out = subprocess.check_output(
            ["git", "show", f"{tag}:{path}"],
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return None


def _safe_load(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


# ---------------------------------------------------------------------------
# Change classifier (intentionally conservative)
# ---------------------------------------------------------------------------

def _classify(baseline: dict, head: dict) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {"breaking": [], "additive": []}
    _walk("$", baseline, head, out)
    return out


def _walk(path: str, b: Any, h: Any, out: dict[str, list[str]]) -> None:
    if isinstance(b, dict) and isinstance(h, dict):
        bp = b.get("properties", {}) or {}
        hp = h.get("properties", {}) or {}
        for k in sorted(set(bp) | set(hp)):
            sub = f"{path}.properties.{k}"
            if k in bp and k not in hp:
                out["breaking"].append(f"removed property {sub}")
            elif k not in bp and k in hp:
                out["additive"].append(f"added property {sub}")
            else:
                _walk(sub, bp[k], hp[k], out)

        b_required = set(b.get("required", []) or [])
        h_required = set(h.get("required", []) or [])
        for k in sorted(b_required - h_required):
            out["breaking"].append(f"property {path}.{k} dropped from required")
        for k in sorted(h_required - b_required):
            out["breaking"].append(f"property {path}.{k} newly required")

        b_enum = b.get("enum")
        h_enum = h.get("enum")
        if b_enum and h_enum:
            removed = [v for v in b_enum if v not in h_enum]
            added = [v for v in h_enum if v not in b_enum]
            for v in removed:
                out["breaking"].append(f"enum {path} removed value {v!r}")
            for v in added:
                out["additive"].append(f"enum {path} added value {v!r}")

        for k in ("type", "$ref"):
            if k in b and k in h and b[k] != h[k]:
                out["breaking"].append(f"{path}.{k} changed: {b[k]!r} -> {h[k]!r}")

        for k, narrow in (("minLength", "tighten"), ("maxLength", "loosen")):
            if k in b and k in h and b[k] != h[k]:
                if (k == "minLength" and h[k] > b[k]) or (k == "maxLength" and h[k] < b[k]):
                    out["breaking"].append(f"{path}.{k} narrowed: {b[k]} -> {h[k]}")

        if "pattern" in b and "pattern" in h and b["pattern"] != h["pattern"]:
            out["breaking"].append(f"{path}.pattern changed")


def _bump_kind(old: str, new: str) -> str:
    o = _semver_parts(old)
    n = _semver_parts(new)
    if not o or not n:
        return "unknown"
    if n[0] > o[0]:
        return "major"
    if n[1] > o[1]:
        return "minor"
    if n[2] > o[2]:
        return "patch"
    return "none"


def _semver_parts(s: str) -> tuple[int, int, int] | None:
    try:
        parts = s.split("-")[0].split(".")
        return (int(parts[0]), int(parts[1]) if len(parts) > 1 else 0, int(parts[2]) if len(parts) > 2 else 0)
    except (ValueError, IndexError):
        return None


if __name__ == "__main__":
    sys.exit(main())
