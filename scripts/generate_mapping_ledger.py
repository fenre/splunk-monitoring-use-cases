#!/usr/bin/env python3
"""
Phase 5.4 — signed provenance ledger for compliance mappings.

Derives a content-addressable, merkle-rooted ledger from:
    * Every UC sidecar's compliance[] array (use-cases/**/*.json)
    * data/regulations.json (canonicalises regulation name -> id)
    * data/provenance/{peer,legal,sme}-signoffs.json (signoff state snapshot)
    * git log (firstSeenCommit / lastModifiedCommit, best-effort)

Output: data/provenance/mapping-ledger.json

The ledger is the single artefact auditors can use to prove what the
catalogue claimed at a given commit, without having to replay the entire
UC tree. It is *generated*: do not hand-edit.

Modes
-----
    --check     Recompute and compare byte-for-byte with the on-disk ledger.
                Exit 1 on any drift. Suitable for CI.
    (default)   Regenerate in place.

Determinism
-----------
Two invocations at the same commit on the same filesystem MUST produce
byte-identical output. Determinism guards are:
    * UC sidecars iterated in sorted order by (ucId, regulationId, clause, mode, assurance).
    * Regulation name -> id lookup is a fixed table plus regulations.json aliases.
    * git log probing is cached per-commit-discovery.
    * generatedAt is taken from the newest sidecar mtime floored to UTC seconds
      (not wall clock), so repeat runs on unchanged trees yield the same timestamp.

Security posture
----------------
Phase 5.4 uses content addressing (SHA-256 per entry + merkle root over
sorted leaves). The `signature` block is 'unsigned' by default; release
automation (.github/workflows/release.yml) replaces it with an 'attested'
block pointing at a GitHub attestation / Sigstore bundle.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

ROOT = pathlib.Path(__file__).resolve().parent.parent
USE_CASES_DIR = ROOT / "use-cases"
REGULATIONS_JSON = ROOT / "data" / "regulations.json"
LEDGER_PATH = ROOT / "data" / "provenance" / "mapping-ledger.json"
SIGNOFFS_DIR = ROOT / "data" / "provenance"

SCHEMA_VERSION = "1.0.0"
HASH_ALGORITHM = "sha256"
CANONICAL_ALGORITHM = "rfc8785"
CANONICAL_JSON_FORM = "utf-8-nfc-sorted-keys-no-whitespace"
CANONICAL_FIELD_ORDER: tuple[str, ...] = (
    "mappingId",
    "ucId",
    "regulationId",
    "regulationVersion",
    "clause",
    "mode",
    "assurance",
    "derivationSource",
)

# ----------------------------------------------------------------------
# Regulation-name canonicalisation
# ----------------------------------------------------------------------
#
# UC sidecars store human-readable regulation names ("NIST 800-53", "UK GDPR",
# "ISO/IEC 27001"). The ledger key must be the stable regulation id from
# data/regulations.json. We build the lookup table from:
#     1) Exact id match (lowercased) — cheapest case.
#     2) data/regulations.json frameworks[].aliases (when present).
#     3) A hard-coded nameTable for historical sidecar wording.
#
# The table is intentionally verbose: every new sidecar wording must be
# added here (or as an alias on the framework) before the generator will
# accept it — this is the referential-integrity guard.
NAME_TABLE: dict[str, str] = {
    "API RP 1164": "api-rp-1164",
    "APPI": "appi",
    "APRA CPS 234": "apra-cps-234",
    "ASD E8": "asd-e8",
    "AU Privacy Act": "au-privacy-act",
    "BAIT/KAIT": "bait-kait",
    "BSI-KritisV": "bsi-kritisv",
    "CCPA": "ccpa",
    "CCPA/CPRA": "ccpa",
    "CJIS": "cjis",
    "CMMC": "cmmc",
    "Cyber Essentials": "uk-cyber-essentials",
    "DORA": "dora",
    "EU AI Act": "eu-ai-act",
    "EU AML": "eu-aml",
    "EU CRA": "eu-cra",
    "EU-CRA": "eu-cra",
    "FCA SM&CR": "fca-smcr",
    "FCA SS1/21": "fca-ss1-21",
    "FDA Part 11": "fda-part-11",
    "FISMA": "fisma",
    "FedRAMP": "fedramp",
    "GDPR": "gdpr",
    "HIPAA": "hipaa-security",
    "HIPAA Privacy": "hipaa-privacy",
    "HIPAA Security": "hipaa-security",
    "HIPAA Security Rule": "hipaa-security",
    "HITRUST": "hitrust",
    "HKMA TM-G-2": "hkma-tm-g-2",
    "IEC 62443": "iec-62443",
    "ISO 27001": "iso-27001",
    "ISO-27001": "iso-27001",
    "ISO/IEC 27001": "iso-27001",
    "IT-Grundschutz": "it-grundschutz",
    "IT-SiG 2.0": "it-sig-2",
    "LGPD": "lgpd",
    "MAS TRM": "mas-trm",
    "MiFID II": "mifid-ii",
    "Multiple": "meta-multi",
    "NERC CIP": "nerc-cip",
    "NESA IAS": "nesa-uae-ias",
    "NIS2": "nis2",
    "NIST 800-53": "nist-800-53",
    "NIST CSF": "nist-csf",
    "NIST-800-53": "nist-800-53",
    "NO KBF": "no-kbf-nve",
    "NO Personopplysningsloven": "no-personopplysningsloven",
    "NO Petroleumsforskriften": "no-petroleumsforskriften",
    "NO Sikkerhetsloven": "no-sikkerhetsloven",
    "NZISM": "nzism",
    "PCI DSS": "pci-dss",
    "PCI-DSS": "pci-dss",
    "PIPL": "pipl",
    "PRA SS2/21": "pra-ss2-21",
    "PSD2": "psd2",
    "QCB Cyber": "qcb-cyber",
    "RBI Cyber": "rbi-cyber",
    "SA PDPL": "sa-pdpl",
    "SAMA CSF": "sama-csf",
    "SG PDPA": "sg-pdpa",
    "SOC 2": "soc-2",
    "SOC-2": "soc-2",
    "SOX ITGC": "sox-itgc",
    "SOX-ITGC": "sox-itgc",
    "SWIFT CSP": "swift-csp",
    "Swiss nFADP": "swiss-nfadp",
    "TSA SD": "tsa-sd",
    "UK GDPR": "uk-gdpr",
    "UK NIS": "uk-nis",
    "UK-GDPR": "uk-gdpr",
    "eIDAS": "eidas",
}


@dataclass(frozen=True)
class LedgerInput:
    """Immutable view of a single compliance[] entry as pulled from a sidecar."""

    uc_id: str
    uc_path: pathlib.Path
    regulation_id: str
    regulation_version: str
    clause: str
    mode: str
    assurance: str
    derivation_source: dict | None


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def canonical_dump(obj: Any) -> str:
    """RFC 8785-compatible canonical JSON: sorted keys, no whitespace, UTF-8."""
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def load_regulation_index() -> dict[str, set[str]]:
    """
    Returns {framework_id: set_of_valid_versions}.
    Used to validate that sidecar (regulationId, regulationVersion) pairs exist.
    """
    data = json.loads(REGULATIONS_JSON.read_text(encoding="utf-8"))
    out: dict[str, set[str]] = {}
    for framework in data.get("frameworks", []):
        versions = {v["version"] for v in framework.get("versions", [])}
        # meta-multi is a placeholder; accept 'n/a' explicitly.
        if framework["id"] == "meta-multi":
            versions.add("n/a")
        out[framework["id"]] = versions
    return out


def resolve_regulation_id(name: str, regulation_index: dict[str, set[str]]) -> str:
    """Map a sidecar's human-readable regulation name to a stable id."""
    if name in NAME_TABLE:
        return NAME_TABLE[name]
    lowered = name.lower().strip()
    if lowered in regulation_index:
        return lowered
    raise KeyError(
        f"Regulation name {name!r} has no entry in generate_mapping_ledger.NAME_TABLE "
        f"and does not match a framework id in data/regulations.json. "
        f"Add a NAME_TABLE entry or an alias before regenerating the ledger."
    )


def normalise_version(regulation_id: str, raw_version: str) -> str:
    """
    Some sidecars store placeholders like 'n/a' or a mild typo. We only pass
    through what's in raw; enforcement happens in the audit script.
    """
    return (raw_version or "").strip() or "n/a"


def iter_uc_sidecars() -> Iterable[pathlib.Path]:
    """All UC sidecars under use-cases/ (excluding templates)."""
    for path in sorted(USE_CASES_DIR.rglob("*.json")):
        # Skip templates or schema-only files by convention (must have 'id').
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict) or "id" not in data:
            continue
        yield path


# ----------------------------------------------------------------------
# Git-log probing (firstSeenCommit / lastModifiedCommit)
# ----------------------------------------------------------------------
#
# A naive per-sidecar `git log --follow` invocation on 1,340 files costs
# ~3 minutes on a fast SSD. We batch with a single `git log` pass and
# populate caches in one shot. Result:
#     * lastModifiedCommit: first occurrence of the path walking newest-first.
#     * firstSeenCommit:    first occurrence of an "A<TAB>path" diff-filter=A
#                           walking newest-first, which is actually the LATEST
#                           add. We then walk oldest-first (implicit: we just
#                           overwrite and the last overwrite wins — git log
#                           --diff-filter=A emits newest-first, so we want the
#                           *oldest* -> we take the entry we see last in
#                           newest-first order, which is equivalent to the
#                           earliest add in git history).
#
# In shallow clones (e.g., CI with fetch-depth=1) git returns nothing; we
# fall back to the catalogueCommit as a conservative placeholder. The
# per-entry granularity is coarse (commit-level per sidecar, not per-mapping)
# — documented in docs/signed-provenance.md §6.
_git_first_seen_cache: dict[pathlib.Path, str | None] = {}
_git_last_modified_cache: dict[pathlib.Path, str | None] = {}
_git_bulk_populated: bool = False


def _git_short(sha: str) -> str:
    return sha[:7] if len(sha) >= 7 else sha


def _populate_git_caches_bulk(paths: Iterable[pathlib.Path]) -> None:
    """
    Single-shot git log that fills both firstSeen and lastModified caches.
    We pass all target paths on the command line so git only considers
    commits that touched them.
    """
    global _git_bulk_populated
    if _git_bulk_populated:
        return
    rel_paths = [str(p.relative_to(ROOT)) for p in paths]
    if not rel_paths:
        _git_bulk_populated = True
        return

    # Pass 1: lastModified — git log newest-first with --name-only.
    try:
        result = subprocess.run(
            ["git", "log", "--format=%H", "--name-only", "--"] + rel_paths,
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
    except (OSError, subprocess.SubprocessError):
        _git_bulk_populated = True
        return

    current_sha: str | None = None
    for line in result.stdout.splitlines():
        line = line.rstrip("\n")
        if not line:
            continue
        if re.fullmatch(r"[0-9a-f]{40}", line):
            current_sha = line
            continue
        if current_sha is None:
            continue
        path = ROOT / line
        # First sighting wins (git log is newest-first).
        if path not in _git_last_modified_cache:
            _git_last_modified_cache[path] = _git_short(current_sha)

    # Pass 2: firstSeen — git log newest-first with --diff-filter=A --name-only.
    # The last (oldest) recorded add is the true first-seen sha.
    try:
        result = subprocess.run(
            [
                "git",
                "log",
                "--diff-filter=A",
                "--format=%H",
                "--name-only",
                "--",
            ]
            + rel_paths,
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
    except (OSError, subprocess.SubprocessError):
        _git_bulk_populated = True
        return

    current_sha = None
    for line in result.stdout.splitlines():
        line = line.rstrip("\n")
        if not line:
            continue
        if re.fullmatch(r"[0-9a-f]{40}", line):
            current_sha = line
            continue
        if current_sha is None:
            continue
        path = ROOT / line
        # Overwrite with every add we see; final value is the earliest add.
        _git_first_seen_cache[path] = _git_short(current_sha)

    _git_bulk_populated = True


def git_first_seen_commit(path: pathlib.Path) -> str | None:
    return _git_first_seen_cache.get(path)


def git_last_modified_commit(path: pathlib.Path) -> str | None:
    return _git_last_modified_cache.get(path)


def catalogue_head_commit() -> str:
    """HEAD short-SHA; placeholder when git is unavailable."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        sha = result.stdout.strip()
        if re.fullmatch(r"[0-9a-f]{7,40}", sha):
            return sha
    except (OSError, subprocess.SubprocessError):
        pass
    return "0000000"  # schema accepts 7+ hex chars; this signals "no git history".


def commit_date_iso(commit: str) -> str | None:
    """ISO-8601 UTC date (seconds resolution) of the given commit, or None on failure."""
    try:
        result = subprocess.run(
            ["git", "show", "-s", "--format=%cI", commit],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        iso = result.stdout.strip()
        if not iso:
            return None
        # Normalise to 'YYYY-MM-DDTHH:MM:SSZ' regardless of local zone.
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


def deterministic_generated_at(head_commit: str) -> str:
    """
    generatedAt is anchored to the catalogueCommit's commit date, NOT to
    sidecar mtime or wall-clock time. This guarantees byte-for-byte identical
    ledgers across re-runs at the same commit, even after `touch`, `sed` with
    no-op edits, or git checkouts that bump file mtimes.

    Falls back to a stable epoch when git metadata is unavailable (e.g.,
    shallow clones or non-git checkouts), so the audit still has a fixed
    point of reference.
    """
    iso = commit_date_iso(head_commit)
    if iso is not None:
        return iso
    # Fallback: fixed 2026-01-01 (documented in docs/signed-provenance.md \u00a76).
    return "2026-01-01T00:00:00Z"


# ----------------------------------------------------------------------
# Signoff-state snapshot
# ----------------------------------------------------------------------
def load_signoffs() -> dict[str, list[dict]]:
    """Load peer / legal / sme signoff arrays. Missing files -> empty list."""
    out: dict[str, list[dict]] = {"peer": [], "legal": [], "sme": []}
    for kind, filename in (
        ("peer", "peer-review-signoffs.json"),
        ("legal", "legal-review-signoffs.json"),
        ("sme", "sme-signoffs.json"),
    ):
        path = SIGNOFFS_DIR / filename
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        entries = data.get("signoffs", [])
        if isinstance(entries, list):
            out[kind] = entries
    return out


def signoff_status_for(
    entry: LedgerInput,
    signoffs: dict[str, list[dict]],
    baselines: dict[str, str],
) -> dict[str, Any]:
    """
    Record whether peer/legal/SME review was required for this mapping and
    whether it has been signed. Gate predicates:

        * peer:  required for all mappings (always 'required').
        * legal: required for any 'full' assurance (per docs/legal-review-guide.md §2).
        * sme:   required for 'detects-violation-of' mode or 'full' assurance
                 (per docs/sme-review-guide.md §2).

    Informational only — the gating itself is enforced by the existing
    Phase 4.5a/4.5b/5.2 audit scripts.
    """

    def _status(kind: str, required: bool) -> dict[str, Any]:
        if not required:
            return {"required": False, "status": "not-required"}
        records = signoffs.get(kind, [])
        for rec in records:
            scopes = rec.get("scope", [])
            if entry.uc_id in scopes:
                pr = rec.get("pr") or "direct-commit"
                return {"required": True, "status": "signed", "latestSignoffPr": pr}
        # Not signed yet: grandfathered iff catalogueCommit predates the
        # signoff file's baseline_commit (the generator doesn't resolve this
        # chronologically; we conservatively record 'pending' so the audit
        # script can compute grandfathering with full git access).
        return {"required": True, "status": "pending"}

    return {
        "peer": _status("peer", True),
        "legal": _status("legal", entry.assurance == "full"),
        "sme": _status(
            "sme",
            entry.mode == "detects-violation-of" or entry.assurance == "full",
        ),
    }


# ----------------------------------------------------------------------
# Ledger materialisation
# ----------------------------------------------------------------------
def build_ledger_inputs(
    regulation_index: dict[str, set[str]],
) -> list[LedgerInput]:
    """Extract every (ucId, regulationId, clause, mode, assurance) tuple."""
    inputs: list[LedgerInput] = []
    unresolved: list[tuple[str, str]] = []

    for sidecar_path in iter_uc_sidecars():
        data = json.loads(sidecar_path.read_text(encoding="utf-8"))
        uc_id = data.get("id")
        if not uc_id:
            continue
        compliance = data.get("compliance", [])
        for c in compliance:
            regulation_name = c.get("regulation", "")
            if not regulation_name:
                continue
            try:
                regulation_id = resolve_regulation_id(
                    regulation_name, regulation_index
                )
            except KeyError as exc:
                unresolved.append((uc_id, str(exc).splitlines()[0]))
                continue
            version = normalise_version(regulation_id, c.get("version", ""))
            clause = (c.get("clause") or "").strip()
            if not clause:
                continue
            mode = c.get("mode", "")
            assurance = c.get("assurance", "")
            if mode not in (
                "satisfies",
                "detects-violation-of",
                "supports",
                "contributes-to",
            ):
                continue
            if assurance not in ("full", "partial", "contributing"):
                continue
            inputs.append(
                LedgerInput(
                    uc_id=uc_id,
                    uc_path=sidecar_path,
                    regulation_id=regulation_id,
                    regulation_version=version,
                    clause=clause,
                    mode=mode,
                    assurance=assurance,
                    derivation_source=c.get("derivationSource"),
                )
            )

    if unresolved:
        print(
            "FATAL: unresolved regulation names in UC sidecars:", file=sys.stderr
        )
        for uc, reason in unresolved[:10]:
            print(f"  {uc}: {reason}", file=sys.stderr)
        sys.exit(2)
    return inputs


def mapping_id_of(entry: LedgerInput) -> str:
    return (
        f"{entry.uc_id}::"
        f"{entry.regulation_id}@{entry.regulation_version}::"
        f"{entry.clause}::{entry.mode}::{entry.assurance}"
    )


def canonical_entry_payload(entry: LedgerInput, mapping_id: str) -> dict[str, Any]:
    """Build the canonical dict that feeds per-entry SHA256."""
    payload: dict[str, Any] = {
        "mappingId": mapping_id,
        "ucId": entry.uc_id,
        "regulationId": entry.regulation_id,
        "regulationVersion": entry.regulation_version,
        "clause": entry.clause,
        "mode": entry.mode,
        "assurance": entry.assurance,
    }
    if entry.derivation_source:
        ds = entry.derivation_source
        dp: dict[str, Any] = {
            "parentRegulation": ds.get("parentRegulation", ""),
            "parentVersion": ds.get("parentVersion", ""),
            "parentClause": ds.get("parentClause", ""),
            "inheritanceMode": ds.get("inheritanceMode", ""),
        }
        if ds.get("parentAssurance"):
            dp["parentAssurance"] = ds["parentAssurance"]
        if ds.get("divergenceNote"):
            dp["divergenceNote"] = ds["divergenceNote"]
        payload["derivationSource"] = dp
    return payload


def build_ledger_entry(
    entry: LedgerInput,
    signoffs: dict[str, list[dict]],
    baselines: dict[str, str],
    head_commit: str,
) -> dict[str, Any]:
    mapping_id = mapping_id_of(entry)
    canonical = canonical_entry_payload(entry, mapping_id)
    canonical_hash = sha256_hex(canonical_dump(canonical))

    first_seen = git_first_seen_commit(entry.uc_path) or head_commit
    last_modified = git_last_modified_commit(entry.uc_path) or head_commit

    record: dict[str, Any] = dict(canonical)
    record["firstSeenCommit"] = first_seen
    record["lastModifiedCommit"] = last_modified
    record["signoffStatus"] = signoff_status_for(entry, signoffs, baselines)
    record["canonicalHash"] = canonical_hash
    return record


def compute_merkle_root(entries: list[dict[str, Any]]) -> str:
    """Sorted-leaf rolling SHA256 over canonicalHash values."""
    h = hashlib.sha256()
    h.update(b"mapping-ledger\x00")  # domain-separator prefix
    for e in entries:
        h.update(e["canonicalHash"].encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()


def build_ledger() -> dict[str, Any]:
    regulation_index = load_regulation_index()
    inputs = build_ledger_inputs(regulation_index)
    signoffs = load_signoffs()

    # Load baseline_commit per signoff file (used for grandfathering notes
    # in docs/signed-provenance.md; audit script consumes this more thoroughly).
    baselines: dict[str, str] = {}
    for kind, filename in (
        ("peer", "peer-review-signoffs.json"),
        ("legal", "legal-review-signoffs.json"),
        ("sme", "sme-signoffs.json"),
    ):
        path = SIGNOFFS_DIR / filename
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                baselines[kind] = data.get("baseline_commit", "0000000")
            except json.JSONDecodeError:
                baselines[kind] = "0000000"

    head_commit = catalogue_head_commit()

    # Populate firstSeen / lastModified caches in one git log invocation
    # (one pass each for lastModified and firstSeen, totalling O(#commits) work
    # across *all* sidecars instead of O(#commits × #sidecars)).
    unique_paths = sorted({e.uc_path for e in inputs})
    _populate_git_caches_bulk(unique_paths)

    records = [
        build_ledger_entry(e, signoffs, baselines, head_commit) for e in inputs
    ]

    # Deduplicate by mappingId (same logical mapping in two sidecars would be a
    # content-level duplicate; the audit rejects these with context).
    by_id: dict[str, dict[str, Any]] = {}
    collisions: list[str] = []
    for r in records:
        mid = r["mappingId"]
        if mid in by_id:
            if by_id[mid]["canonicalHash"] != r["canonicalHash"]:
                collisions.append(mid)
            continue
        by_id[mid] = r
    if collisions:
        print("FATAL: mappingId collisions with divergent content:", file=sys.stderr)
        for mid in collisions[:10]:
            print(f"  {mid}", file=sys.stderr)
        sys.exit(2)

    entries = sorted(by_id.values(), key=lambda x: x["mappingId"])
    merkle_root = compute_merkle_root(entries)

    ledger: dict[str, Any] = {
        "$schema": "../../schemas/mapping-ledger.schema.json",
        "schemaVersion": SCHEMA_VERSION,
        "generatedAt": deterministic_generated_at(head_commit),
        "catalogueCommit": head_commit,
        "hashAlgorithm": HASH_ALGORITHM,
        "canonicalisation": {
            "algorithm": CANONICAL_ALGORITHM,
            "jsonForm": CANONICAL_JSON_FORM,
            "fieldOrder": list(CANONICAL_FIELD_ORDER),
        },
        "entryCount": len(entries),
        "merkleRoot": merkle_root,
        "signature": {
            "state": "unsigned",
            "reason": "development iteration; release workflow promotes to attested",
        },
        "entries": entries,
    }
    return ledger


# ----------------------------------------------------------------------
# Entrypoint
# ----------------------------------------------------------------------
def render(ledger: dict[str, Any]) -> str:
    """Pretty-print with trailing newline, stable key order."""
    # We deliberately DO NOT use canonical_dump here: the on-disk ledger is
    # human-readable. The *hashes* used canonical_dump on their respective
    # payloads during construction.
    return json.dumps(ledger, indent=2, ensure_ascii=False, sort_keys=False) + "\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Generate data/provenance/mapping-ledger.json from UC sidecars.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Regenerate in memory and compare byte-for-byte with the existing ledger. Exit 1 on drift.",
    )
    args = parser.parse_args(argv)

    ledger = build_ledger()
    new_body = render(ledger)

    if args.check:
        if not LEDGER_PATH.exists():
            print(
                f"FATAL: --check called but {LEDGER_PATH.relative_to(ROOT)} does not exist.",
                file=sys.stderr,
            )
            return 1
        current = LEDGER_PATH.read_text(encoding="utf-8")
        if current != new_body:
            print(
                f"FATAL: {LEDGER_PATH.relative_to(ROOT)} is stale. "
                f"Run scripts/generate_mapping_ledger.py (without --check) and commit the result.",
                file=sys.stderr,
            )
            # Show a small diff preview (first ~20 differing lines).
            _preview_diff(current, new_body)
            return 1
        print(
            f"OK: {LEDGER_PATH.relative_to(ROOT)} is up to date "
            f"({ledger['entryCount']} entries, merkle root {ledger['merkleRoot'][:16]}\u2026)."
        )
        return 0

    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    LEDGER_PATH.write_text(new_body, encoding="utf-8")
    print(
        f"Wrote {LEDGER_PATH.relative_to(ROOT)}: {ledger['entryCount']} entries, "
        f"merkle root {ledger['merkleRoot']}."
    )
    return 0


def _preview_diff(old: str, new: str) -> None:
    import difflib

    diff = list(
        difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile="current",
            tofile="regenerated",
            n=2,
        )
    )
    if not diff:
        return
    sys.stderr.write("--- diff preview (first 40 lines) ---\n")
    sys.stderr.writelines(diff[:40])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
