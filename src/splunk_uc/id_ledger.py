"""UC identifier ledger — permanent ID contract and content fingerprints.

An identifier, once published, permanently refers to one use case. The
append-only ledger records every identifier ever issued, its status, and a
stable content fingerprint (title + primary SPL) so CI can detect silent
reuse without renumbering the catalogue.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTENT = REPO_ROOT / "content"
LEDGER_PATH = REPO_ROOT / "data" / "id-ledger.json"
COLLISIONS_PATH = REPO_ROOT / "data" / "id-ledger-collisions.json"
MIGRATIONS_DIR = REPO_ROOT / "data" / "uc-id-migrations"
VERSION_PATH = REPO_ROOT / "VERSION"
CAT25_REMAP_PATH = REPO_ROOT / "data" / "cat25_id_remap.json"

UC_FILENAME_RE = re.compile(r"^UC-(\d+\.\d+\.\d+)\.json$")
ID_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")

# Catalogue version from which the permanent-identity guarantee is enforced in CI.
IDENTITY_GUARANTEE_SINCE = "8.25.0"
IDENTITY_POLICY_STATEMENT = (
    "An identifier, once published, permanently refers to one use case. "
    "It is never reused and never reassigned to different content. "
    "Gaps are expected and correct."
)
UNKNOWN_FINGERPRINT = "738e208be61f7e63270a458ad721fcb56be8dd4aad9f1a144c6fde10323603e9"


@dataclass(frozen=True)
class CatalogueUC:
    uc_id: str
    path: Path
    payload: dict[str, Any]


def read_catalogue_version() -> str:
    if VERSION_PATH.is_file():
        return VERSION_PATH.read_text(encoding="utf-8").strip()
    return IDENTITY_GUARANTEE_SINCE


def content_fingerprint(payload: dict[str, Any]) -> str:
    """Stable SHA-256 over title + primary SPL (the reuse-detection surface)."""
    title = str(payload.get("title", "")).strip()
    spl = str(payload.get("spl", "")).strip()
    canonical = json.dumps(
        {"spl": spl, "title": title},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def iter_catalogue_ucs(content_dir: Path | None = None) -> Iterator[CatalogueUC]:
    root = content_dir or CONTENT
    for cat_dir in sorted(root.iterdir()):
        if not cat_dir.is_dir() or not cat_dir.name.startswith("cat-"):
            continue
        for uc_path in sorted(cat_dir.glob("UC-*.json")):
            payload = json.loads(uc_path.read_text(encoding="utf-8"))
            uc_id = str(payload.get("id", "")).strip()
            if not uc_id:
                continue
            yield CatalogueUC(uc_id=uc_id, path=uc_path, payload=payload)


def catalogue_index(content_dir: Path | None = None) -> dict[str, CatalogueUC]:
    return {uc.uc_id: uc for uc in iter_catalogue_ucs(content_dir)}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_ledger(path: Path | None = None) -> dict[str, Any]:
    return load_json(path or LEDGER_PATH)


def load_collisions(path: Path | None = None) -> dict[str, Any]:
    target = path or COLLISIONS_PATH
    if not target.is_file():
        return {"collisions": []}
    return load_json(target)


def identity_guarantee_metadata() -> dict[str, str]:
    """Machine-readable identity contract for catalog.json and API manifests."""
    return {
        "identityGuaranteeSince": IDENTITY_GUARANTEE_SINCE,
        "identityPolicy": IDENTITY_POLICY_STATEMENT,
        "identityPolicyDoc": "/docs/adr/0016-permanent-uc-identifiers.md",
        "identityLedgerPath": "/data/id-ledger.json",
    }


def _revision_record(
    fingerprint: str,
    catalogue_version: str,
    catalogue_commit: str | None = None,
) -> dict[str, Any]:
    revision: dict[str, Any] = {
        "contentFingerprint": fingerprint,
        "catalogueVersion": catalogue_version,
    }
    if catalogue_commit:
        revision["catalogueCommit"] = catalogue_commit
    return revision


def entry_fingerprint_revisions(entry: dict[str, Any]) -> list[dict[str, Any]]:
    """Return persisted revisions, migrating legacy single-fingerprint rows."""
    revisions = entry.get("fingerprintRevisions")
    if isinstance(revisions, list) and revisions:
        return [r for r in revisions if isinstance(r, dict)]
    legacy = str(entry.get("contentFingerprint", "")).strip()
    if legacy:
        version = str(entry.get("firstSeenVersion") or "unknown")
        return [_revision_record(legacy, version)]
    return []


def latest_fingerprint(entry: dict[str, Any]) -> str:
    revisions = entry_fingerprint_revisions(entry)
    if revisions:
        return str(revisions[-1].get("contentFingerprint", "")).strip()
    return str(entry.get("contentFingerprint", "")).strip()


def merge_fingerprint_revisions(
    prior_entry: dict[str, Any],
    current_fp: str,
    catalogue_version: str,
    catalogue_commit: str,
) -> list[dict[str, Any]]:
    """Append a revision when content changes; never shorten the list."""
    revisions = list(entry_fingerprint_revisions(prior_entry))
    if not revisions:
        return [_revision_record(current_fp, catalogue_version, catalogue_commit)]
    latest = str(revisions[-1].get("contentFingerprint", "")).strip()
    if latest != current_fp:
        revisions.append(_revision_record(current_fp, catalogue_version, catalogue_commit))
    return revisions


def validate_ledger_revision_monotonicity(
    previous: dict[str, Any] | None,
    new_doc: dict[str, Any],
) -> list[str]:
    """Fail when regeneration shortens any identifier's revision history."""
    if not previous:
        return []
    prev_by_id = ledger_entries_by_id(previous)
    new_by_id = ledger_entries_by_id(new_doc)
    issues: list[str] = []
    for uc_id, prior in prev_by_id.items():
        old_count = len(entry_fingerprint_revisions(prior))
        if old_count == 0:
            continue
        new_entry = new_by_id.get(uc_id)
        if new_entry is None:
            continue
        new_count = len(entry_fingerprint_revisions(new_entry))
        if new_count < old_count:
            issues.append(
                f"Fingerprint revision history shortened for {uc_id!r}: "
                f"{old_count} -> {new_count} revisions "
                "(regenerate-id-ledger must append only)"
            )
    return issues


def ledger_entries_by_id(ledger: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries = ledger.get("entries", [])
    out: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        uc_id = str(entry.get("id", "")).strip()
        if uc_id:
            out[uc_id] = entry
    return out


def _git_short_head() -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode == 0:
        return proc.stdout.strip()
    return "unknown"


def _git_last_payload(uc_id: str) -> dict[str, Any] | None:
    """Best-effort last committed payload for a removed identifier."""
    matches = list(CONTENT.glob(f"cat-*/UC-{uc_id}.json"))
    if matches:
        return json.loads(matches[0].read_text(encoding="utf-8"))
    proc = subprocess.run(
        [
            "git",
            "log",
            "-1",
            "--diff-filter=D",
            "--format=%H",
            "--",
            f"content/**/UC-{uc_id}.json",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    commit = proc.stdout.strip().splitlines()[0]
    show = subprocess.run(
        ["git", "show", f"{commit}^:content/", "--name-only"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    # Locate the deleted path in that commit's parent tree.
    list_proc = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", f"{commit}^", "content"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if list_proc.returncode != 0:
        return None
    rel_path = None
    suffix = f"/UC-{uc_id}.json"
    for line in list_proc.stdout.splitlines():
        if line.endswith(suffix):
            rel_path = line
            break
    if not rel_path:
        return None
    blob = subprocess.run(
        ["git", "show", f"{commit}^:{rel_path}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if blob.returncode != 0:
        return None
    try:
        return json.loads(blob.stdout)
    except json.JSONDecodeError:
        return None


def discover_removed_ids(catalogue: dict[str, CatalogueUC]) -> set[str]:
    """Identifiers that were published but are absent from the live catalogue."""
    removed: set[str] = set()

    if CAT25_REMAP_PATH.is_file():
        remap = load_json(CAT25_REMAP_PATH).get("id_map", {})
        if isinstance(remap, dict):
            for old_id, new_id in remap.items():
                if str(old_id) != str(new_id) and str(old_id) not in catalogue:
                    removed.add(str(old_id))

    proc = subprocess.run(
        [
            "git",
            "log",
            "--diff-filter=D",
            "--name-only",
            "--format=",
            "--",
            "content/**/UC-*.json",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode == 0:
        for line in proc.stdout.splitlines():
            name = Path(line).name
            m = UC_FILENAME_RE.match(name)
            if m and m.group(1) not in catalogue:
                removed.add(m.group(1))

    # Relocations that left permanent gaps (empirically verified).
    for gap_id in ("1.2.14", "5.9.56", "5.9.57", "5.9.58", "5.9.59"):
        if gap_id not in catalogue:
            removed.add(gap_id)

    return removed


def _catalogue_generated_at(catalogue: dict[str, CatalogueUC]) -> str:
    """Deterministic timestamp from newest sidecar mtime (not wall clock)."""
    latest = 0.0
    for uc in catalogue.values():
        try:
            latest = max(latest, uc.path.stat().st_mtime)
        except OSError:
            continue
    if latest <= 0:
        latest = 0.0
    return datetime.fromtimestamp(latest, tz=UTC).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def build_ledger_document(
    *,
    catalogue: dict[str, CatalogueUC] | None = None,
    previous: dict[str, Any] | None = None,
) -> dict[str, Any]:
    catalogue = catalogue or catalogue_index()
    previous_entries = ledger_entries_by_id(previous) if previous else {}
    removed_ids = discover_removed_ids(catalogue)
    version = read_catalogue_version()
    now = _catalogue_generated_at(catalogue)
    commit = _git_short_head()

    entries: list[dict[str, Any]] = []

    for uc_id in sorted(catalogue.keys(), key=lambda x: tuple(map(int, x.split(".")))):
        uc = catalogue[uc_id]
        fp = content_fingerprint(uc.payload)
        prior = previous_entries.get(uc_id, {})
        revisions = merge_fingerprint_revisions(prior, fp, version, commit)
        entry: dict[str, Any] = {
            "id": uc_id,
            "status": "active",
            "contentFingerprint": fp,
            "fingerprintRevisions": revisions,
            "firstSeenVersion": prior.get("firstSeenVersion") or version,
        }
        if not prior.get("firstSeenVersion"):
            entry["firstSeenVersionSource"] = "catalogue-seed"
            entry["firstSeenVersionNote"] = (
                "Bulk-seeded when the identity ledger was introduced; "
                "per-ID first-publication version was not reconstructed."
            )
        entries.append(entry)

    for uc_id in sorted(removed_ids, key=lambda x: tuple(map(int, x.split(".")))):
        if uc_id in catalogue:
            continue
        prior = previous_entries.get(uc_id, {})
        payload = _git_last_payload(uc_id)
        fp = content_fingerprint(payload) if payload else latest_fingerprint(prior)
        if not fp:
            fp = UNKNOWN_FINGERPRINT
        revisions = merge_fingerprint_revisions(prior, fp, version, commit)
        entry: dict[str, Any] = {
            "id": uc_id,
            "status": "removed",
            "contentFingerprint": fp,
            "fingerprintRevisions": revisions,
            "firstSeenVersion": prior.get("firstSeenVersion") or "unknown",
            "removedInVersion": prior.get("removedInVersion") or version,
        }
        if not prior.get("firstSeenVersion"):
            entry["firstSeenVersionSource"] = "git-reconstruction"
            entry["firstSeenVersionNote"] = (
                "Removal inferred from git history and/or cat-25 remap; "
                "exact first-publication version may be ambiguous."
            )
        if fp == UNKNOWN_FINGERPRINT and not payload and not latest_fingerprint(prior):
            entry["contentFingerprintNote"] = (
                "Fingerprint unavailable — git history did not yield a parseable sidecar; "
                "sentinel hash of empty title+spl recorded."
            )
        entries.append(entry)

    return {
        "$schema": "../schemas/id-ledger.schema.json",
        "schemaVersion": "1.1.0",
        "generatedAt": now,
        "catalogueCommit": commit,
        "catalogueVersion": version,
        "identityGuaranteeSince": IDENTITY_GUARANTEE_SINCE,
        "hashAlgorithm": "sha256",
        "fingerprintFields": ["title", "spl"],
        "seedPolicy": {
            "activeFirstSeenVersion": "bulk-seed",
            "note": (
                "Active entries inherit firstSeenVersion from catalogue seed at ledger "
                "introduction unless a prior ledger row existed. Removed entries are "
                "reconstructed from git and remap manifests where possible."
            ),
        },
        "entryCount": len(entries),
        "entries": entries,
    }


def validate_catalogue_against_ledger(
    ledger: dict[str, Any] | None = None,
    catalogue: dict[str, CatalogueUC] | None = None,
) -> list[str]:
    """Return human-readable audit failures for catalogue ↔ ledger drift."""
    ledger = ledger or load_ledger()
    catalogue = catalogue or catalogue_index()
    by_id = ledger_entries_by_id(ledger)
    issues: list[str] = []

    for uc_id, uc in sorted(catalogue.items(), key=lambda kv: kv[0]):
        entry = by_id.get(uc_id)
        if entry is None:
            issues.append(f"Catalogue id {uc_id!r} is missing from data/id-ledger.json")
            continue
        status = str(entry.get("status", "")).strip()
        if status == "removed":
            issues.append(
                f"Reuse of removed identifier {uc_id!r} (ledger status=removed)"
            )
            continue
        if status != "active":
            issues.append(f"Catalogue id {uc_id!r} has unexpected ledger status {status!r}")
            continue
        expected = content_fingerprint(uc.payload)
        recorded = latest_fingerprint(entry)
        if recorded and recorded != expected:
            issues.append(
                f"Fingerprint mismatch for {uc_id!r}: ledger has {recorded[:12]}… "
                f"but catalogue computes {expected[:12]}… "
                "(run python -m splunk_uc generate-id-ledger to refresh, or record an explicit migration)"
            )

    active_ids = set(catalogue.keys())
    for uc_id, entry in sorted(by_id.items()):
        if str(entry.get("status")) == "active" and uc_id not in active_ids:
            issues.append(
                f"Ledger marks {uc_id!r} active but no sidecar exists in content/ "
                "(run python -m splunk_uc generate-id-ledger to mark removed)"
            )

    return issues
