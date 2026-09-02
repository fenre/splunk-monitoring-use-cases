#!/usr/bin/env python3
"""Blast-radius guard for bulk UC identifier changes.

Fails CI when a PR changes more than ``--threshold`` UC identifiers (add,
remove, remap, or same-id fingerprint churn) unless a committed migration
manifest under ``data/uc-id-migrations/`` explicitly lists every change and
whether content identity is preserved.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from splunk_uc.id_ledger import content_fingerprint

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTENT = REPO_ROOT / "content"
MIGRATIONS_DIR = REPO_ROOT / "data" / "uc-id-migrations"

UC_SIDECAR_RE = re.compile(r"^content/cat-[^/]+/UC-(\d+\.\d+\.\d+)\.json$")
ID_PATTERN = re.compile(r"^(\d+\.\d+\.\d+)$")

DEFAULT_THRESHOLD = 10
DEFAULT_BASE = "origin/main"


@dataclass(frozen=True)
class IdentifierChange:
    kind: str  # add | remove | remap | fingerprint_change
    from_id: str | None
    to_id: str | None


def _run_git(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def resolve_base_ref(explicit: str | None) -> str:
    if explicit:
        return explicit
    env_base = os.environ.get("GITHUB_BASE_REF", "").strip()
    if env_base:
        candidate = f"origin/{env_base}"
        probe = _run_git(["git", "rev-parse", "--verify", candidate])
        if probe.returncode == 0:
            return candidate
    probe = _run_git(["git", "rev-parse", "--verify", DEFAULT_BASE])
    if probe.returncode == 0:
        return DEFAULT_BASE
    merge_base = _run_git(["git", "merge-base", "HEAD", "HEAD~1"])
    if merge_base.returncode == 0 and merge_base.stdout.strip():
        return merge_base.stdout.strip()
    return "HEAD~1"


def changed_sidecar_paths(base_ref: str) -> list[str]:
    """Return sidecar path changes from merge-base(base_ref, HEAD) through HEAD.

    Uses the three-dot diff form so the count spans the whole PR branch, not
    individual commits — chunking edits into commits of nine cannot bypass the
    threshold.
    """
    proc = _run_git(["git", "diff", "--name-status", f"{base_ref}...HEAD", "--", "content"])
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "git diff failed")
    return [line for line in proc.stdout.splitlines() if line.strip()]


def _read_payload_at_ref(path: str, ref: str) -> dict[str, Any] | None:
    show = _run_git(["git", "show", f"{ref}:{path}"])
    if show.returncode != 0:
        return None
    try:
        payload = json.loads(show.stdout)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _read_id_at_ref(path: str, ref: str) -> str | None:
    show = _run_git(["git", "show", f"{ref}:{path}"])
    if show.returncode != 0:
        return None
    try:
        payload = json.loads(show.stdout)
    except json.JSONDecodeError:
        return None
    uc_id = str(payload.get("id", "")).strip()
    return uc_id or None


def detect_identifier_changes(base_ref: str) -> list[IdentifierChange]:
    changes: list[IdentifierChange] = []
    for line in changed_sidecar_paths(base_ref):
        parts = line.split("\t")
        if not parts:
            continue
        status = parts[0]
        if status.startswith("R") and len(parts) >= 3:
            old_path, new_path = parts[1], parts[2]
            old_m = UC_SIDECAR_RE.match(old_path)
            new_m = UC_SIDECAR_RE.match(new_path)
            if old_m and new_m:
                old_id, new_id = old_m.group(1), new_m.group(1)
                if old_id == new_id:
                    continue
                changes.append(IdentifierChange("remap", old_id, new_id))
            continue
        if len(parts) < 2:
            continue
        path = parts[1]
        m = UC_SIDECAR_RE.match(path)
        if not m:
            continue
        file_id = m.group(1)
        if status == "A":
            changes.append(IdentifierChange("add", None, file_id))
        elif status == "D":
            changes.append(IdentifierChange("remove", file_id, None))
        elif status == "M":
            base_id = _read_id_at_ref(path, base_ref)
            head_id = _read_id_at_ref(path, "HEAD")
            if base_id and head_id and base_id != head_id:
                changes.append(IdentifierChange("remap", base_id, head_id))
            elif base_id and head_id and base_id == head_id:
                base_payload = _read_payload_at_ref(path, base_ref)
                head_payload = _read_payload_at_ref(path, "HEAD")
                if (
                    base_payload
                    and head_payload
                    and content_fingerprint(base_payload) != content_fingerprint(head_payload)
                ):
                    changes.append(IdentifierChange("fingerprint_change", base_id, base_id))
            elif base_id is None and head_id:
                changes.append(IdentifierChange("add", None, head_id))
            elif head_id is None and base_id:
                changes.append(IdentifierChange("remove", base_id, None))

    return changes


def load_migration_manifests(paths: list[Path]) -> list[dict[str, Any]]:
    manifests: list[dict[str, Any]] = []
    for path in sorted(paths):
        manifests.append(json.loads(path.read_text(encoding="utf-8")))
    return manifests


def manifest_change_keys(manifest: dict[str, Any]) -> set[tuple[str, str | None, str | None]]:
    keys: set[tuple[str, str | None, str | None]] = set()
    for row in manifest.get("changes", []):
        if not isinstance(row, dict):
            continue
        kind = str(row.get("kind", "")).strip()
        if kind == "bulk_fingerprint_change":
            for raw_id in row.get("identifiers", []):
                uc_id = str(raw_id).strip()
                if uc_id:
                    keys.add(("fingerprint_change", uc_id, uc_id))
            continue
        from_id = row.get("from")
        to_id = row.get("to")
        from_s = str(from_id).strip() if from_id else None
        to_s = str(to_id).strip() if to_id else None
        keys.add((kind, from_s, to_s))
    return keys


def change_key(change: IdentifierChange) -> tuple[str, str | None, str | None]:
    return (change.kind, change.from_id, change.to_id)


def validate_manifest_coverage(
    changes: list[IdentifierChange], manifest_paths: list[Path]
) -> list[str]:
    issues: list[str] = []
    if not manifest_paths:
        issues.append(
            "No migration manifest under data/uc-id-migrations/ — add a JSON file "
            "listing every identifier change and identityPreserved per row."
        )
        return issues

    declared: set[tuple[str, str | None, str | None]] = set()
    for manifest in load_migration_manifests(manifest_paths):
        declared |= manifest_change_keys(manifest)

    for change in changes:
        key = change_key(change)
        if key not in declared:
            issues.append(
                f"Manifest missing change: kind={change.kind!r} "
                f"from={change.from_id!r} to={change.to_id!r}"
            )
    return issues


def migration_files_in_diff(base_ref: str) -> list[Path]:
    proc = _run_git(
        ["git", "diff", "--name-only", f"{base_ref}...HEAD", "--", "data/uc-id-migrations/"]
    )
    if proc.returncode != 0:
        return []
    paths: list[Path] = []
    for line in proc.stdout.splitlines():
        rel = line.strip()
        if rel.endswith(".json") and rel.startswith("data/uc-id-migrations/"):
            paths.append(REPO_ROOT / rel)
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Guard against bulk UC identifier remaps.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 when blast-radius rules are violated (CI mode).",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=DEFAULT_THRESHOLD,
        help=f"Maximum identifier changes allowed without a manifest (default: {DEFAULT_THRESHOLD}).",
    )
    parser.add_argument(
        "--base",
        default=None,
        help=f"Git base ref for the diff (default: {DEFAULT_BASE} or GITHUB_BASE_REF).",
    )
    args = parser.parse_args(argv)

    base_ref = resolve_base_ref(args.base)
    changes = detect_identifier_changes(base_ref)
    unique_ids = {
        x
        for change in changes
        for x in (change.from_id, change.to_id)
        if x is not None
    }

    print(f"Base ref: {base_ref}")
    print(f"Identifier changes detected: {len(changes)} ({len(unique_ids)} distinct ids)")

    if len(changes) <= args.threshold:
        print(f"PASS: within threshold ({args.threshold})")
        return 0

    manifest_paths = migration_files_in_diff(base_ref)
    issues = validate_manifest_coverage(changes, manifest_paths)
    if issues:
        print("FAIL: bulk identifier change without adequate migration manifest:", file=sys.stderr)
        for issue in issues:
            print(f"  - {issue}", file=sys.stderr)
        return 1 if args.check else 0

    print(f"PASS: {len(changes)} changes covered by {len(manifest_paths)} manifest file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
