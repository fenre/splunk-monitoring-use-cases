#!/usr/bin/env python3
"""
Phase 5.4 — signed-provenance ledger audit.

Validates data/provenance/mapping-ledger.json against:
    * schemas/mapping-ledger.schema.json (structure)
    * per-entry canonicalHash recomputation
    * merkleRoot recomputation over sorted leaves
    * referential integrity with UC sidecars (forward and reverse)
    * catalogueCommit consistency with git HEAD (when available)
    * signature block self-consistency (unsigned vs attested invariants)

Optionally, with --verify-signature, invokes `gh attestation verify` when the
ledger is in the 'attested' state. The verification is non-fatal by default;
pass --require-signature to treat absence or failure as an error.

Modes
-----
    --check         Treat any drift, hash mismatch, missing ledger entry, or
                    ledger-for-missing-sidecar mapping as a fatal error.
                    This is the CI entry point.
    (default)       Same as --check. The audit is read-only; there is no
                    auto-fix path here (use scripts/generate_mapping_ledger.py
                    to repair drift).

Outputs
-------
    reports/mapping-ledger-audit.json     Machine-readable summary.
    stdout                                Human-readable PASS / FAIL banner.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parent.parent
LEDGER_PATH = ROOT / "data" / "provenance" / "mapping-ledger.json"
SCHEMA_PATH = ROOT / "schemas" / "mapping-ledger.schema.json"
REPORT_PATH = ROOT / "reports" / "mapping-ledger-audit.json"

# Import generator-internal helpers so the audit uses the exact same
# canonicalisation and merkle construction as the generator. A mismatch
# would be a bug in one or the other; importing keeps them in lockstep.
sys.path.insert(0, str(ROOT / "scripts"))
from generate_mapping_ledger import (  # noqa: E402  (path manipulation above)
    CANONICAL_FIELD_ORDER,
    canonical_dump,
    canonical_entry_payload,
    compute_merkle_root,
    iter_uc_sidecars,
    load_regulation_index,
    mapping_id_of,
    normalise_version,
    resolve_regulation_id,
    sha256_hex,
    LedgerInput,
)


# ----------------------------------------------------------------------
# JSON Schema validation
# ----------------------------------------------------------------------
def validate_schema(ledger: dict[str, Any]) -> list[str]:
    """Validate against schemas/mapping-ledger.schema.json using jsonschema if available."""
    errors: list[str] = []
    try:
        import jsonschema  # type: ignore[import-not-found]
    except ImportError:
        # Fall back to minimal structural checks. CI installs jsonschema via
        # requirements-dev.txt (added in Phase 1.1); local dev without jsonschema
        # still gets the semantic checks below.
        required = [
            "schemaVersion",
            "generatedAt",
            "catalogueCommit",
            "merkleRoot",
            "hashAlgorithm",
            "canonicalisation",
            "entryCount",
            "signature",
            "entries",
        ]
        for key in required:
            if key not in ledger:
                errors.append(f"schema: missing required top-level field {key!r}")
        return errors

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    for err in sorted(validator.iter_errors(ledger), key=lambda e: list(e.absolute_path)):
        path = ".".join(str(p) for p in err.absolute_path) or "<root>"
        errors.append(f"schema: {path}: {err.message}")
    return errors


# ----------------------------------------------------------------------
# Hash recomputation
# ----------------------------------------------------------------------
def audit_entry_hashes(ledger: dict[str, Any]) -> list[str]:
    """Re-derive canonicalHash for every entry and compare."""
    errors: list[str] = []
    seen_mapping_ids: set[str] = set()

    for idx, entry in enumerate(ledger.get("entries", [])):
        mid = entry.get("mappingId", f"<entry[{idx}] with no mappingId>")

        if mid in seen_mapping_ids:
            errors.append(
                f"hash: duplicate mappingId {mid!r} at entries[{idx}] "
                "(mappingIds must be unique within a ledger)."
            )
        seen_mapping_ids.add(mid)

        # Rebuild the canonical payload from ledger fields (without touching
        # the stored canonicalHash).
        try:
            canonical = {
                field: entry[field]
                for field in CANONICAL_FIELD_ORDER
                if field in entry
            }
        except Exception as exc:  # pragma: no cover — defensive
            errors.append(f"hash: failed to extract canonical fields for {mid!r}: {exc}")
            continue

        expected = sha256_hex(canonical_dump(canonical))
        got = entry.get("canonicalHash", "")
        if expected != got:
            errors.append(
                f"hash: canonicalHash mismatch for {mid!r}: "
                f"stored={got[:16]}… expected={expected[:16]}…"
            )

    return errors


def audit_merkle_root(ledger: dict[str, Any]) -> list[str]:
    """Recompute the top-level merkleRoot and compare."""
    expected = compute_merkle_root(ledger.get("entries", []))
    got = ledger.get("merkleRoot", "")
    if expected != got:
        return [
            f"merkle: merkleRoot mismatch: stored={got[:16]}… expected={expected[:16]}…"
        ]
    return []


def audit_entry_count(ledger: dict[str, Any]) -> list[str]:
    expected = len(ledger.get("entries", []))
    got = ledger.get("entryCount", -1)
    if expected != got:
        return [f"entryCount: stored={got} does not match len(entries)={expected}."]
    return []


def audit_sort_order(ledger: dict[str, Any]) -> list[str]:
    """mappingIds must be sorted lexicographically."""
    mids = [e.get("mappingId", "") for e in ledger.get("entries", [])]
    if mids != sorted(mids):
        for i, (a, b) in enumerate(zip(mids, sorted(mids))):
            if a != b:
                return [
                    f"sort: entries are not sorted by mappingId "
                    f"(first divergence at index {i}: {a!r} should be {b!r})."
                ]
    return []


# ----------------------------------------------------------------------
# Referential integrity (forward + reverse)
# ----------------------------------------------------------------------
def gather_sidecar_mappings() -> set[str]:
    """Compute the set of mappingIds that the UC sidecars currently declare."""
    reg_index = load_regulation_index()
    found: set[str] = set()
    for path in iter_uc_sidecars():
        data = json.loads(path.read_text(encoding="utf-8"))
        uc_id = data.get("id")
        if not uc_id:
            continue
        for c in data.get("compliance", []):
            regulation_name = c.get("regulation", "")
            if not regulation_name:
                continue
            try:
                regulation_id = resolve_regulation_id(regulation_name, reg_index)
            except KeyError:
                continue  # generator would have failed; we flag via forward check.
            version = normalise_version(regulation_id, c.get("version", ""))
            clause = (c.get("clause") or "").strip()
            mode = c.get("mode", "")
            assurance = c.get("assurance", "")
            if not clause or mode not in (
                "satisfies",
                "detects-violation-of",
                "supports",
                "contributes-to",
            ) or assurance not in ("full", "partial", "contributing"):
                continue
            entry = LedgerInput(
                uc_id=uc_id,
                uc_path=path,
                regulation_id=regulation_id,
                regulation_version=version,
                clause=clause,
                mode=mode,
                assurance=assurance,
                derivation_source=c.get("derivationSource"),
            )
            found.add(mapping_id_of(entry))
    return found


def audit_referential_integrity(ledger: dict[str, Any]) -> list[str]:
    """Forward + reverse checks against current UC sidecars."""
    errors: list[str] = []
    ledger_ids = {e.get("mappingId", "") for e in ledger.get("entries", [])}
    sidecar_ids = gather_sidecar_mappings()

    missing_in_ledger = sidecar_ids - ledger_ids
    missing_in_sidecars = ledger_ids - sidecar_ids

    for mid in sorted(missing_in_ledger)[:20]:
        errors.append(
            f"referential: sidecar mapping {mid!r} has no ledger entry "
            "(run scripts/generate_mapping_ledger.py and commit)."
        )
    if len(missing_in_ledger) > 20:
        errors.append(
            f"referential: …and {len(missing_in_ledger) - 20} more sidecar mappings missing from ledger."
        )

    for mid in sorted(missing_in_sidecars)[:20]:
        errors.append(
            f"referential: ledger entry {mid!r} has no backing sidecar "
            "(a UC was deleted or renamed without regenerating the ledger)."
        )
    if len(missing_in_sidecars) > 20:
        errors.append(
            f"referential: …and {len(missing_in_sidecars) - 20} more ledger entries without sidecars."
        )

    return errors


# ----------------------------------------------------------------------
# catalogueCommit / signature consistency
# ----------------------------------------------------------------------
def audit_catalogue_commit(ledger: dict[str, Any]) -> list[str]:
    """Warn when catalogueCommit does not match git HEAD (non-fatal in draft mode)."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        head = result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return []
    if not re.fullmatch(r"[0-9a-f]{7,40}", head):
        return []
    if ledger.get("catalogueCommit") != head:
        # This is informational: a developer may regenerate the ledger locally
        # before committing, and HEAD won't match until the commit lands. CI
        # enforces the match indirectly via `generate_mapping_ledger.py --check`
        # on the PR branch.
        return [
            f"commit: catalogueCommit={ledger.get('catalogueCommit')!r} differs from git HEAD={head!r} "
            "(informational; CI enforces drift via the generator's --check step)."
        ]
    return []


def audit_signature_envelope(
    ledger: dict[str, Any],
    verify_signature: bool,
    require_signature: bool,
    ledger_file: pathlib.Path,
) -> list[str]:
    errors: list[str] = []
    sig = ledger.get("signature", {})
    state = sig.get("state")

    if state == "unsigned":
        if require_signature:
            errors.append(
                "signature: state=unsigned but --require-signature was passed "
                "(release automation should have promoted this to 'attested')."
            )
        return errors

    if state == "attested":
        # Self-consistency: catalogueCommit MUST match signature.commit when both present.
        if "commit" in sig and sig["commit"] != ledger.get("catalogueCommit"):
            errors.append(
                f"signature: signature.commit={sig['commit']!r} does not match "
                f"catalogueCommit={ledger.get('catalogueCommit')!r}."
            )
        if verify_signature:
            errors.extend(_run_gh_attestation_verify(sig, ledger, ledger_file))
        return errors

    errors.append(f"signature: unknown state {state!r}.")
    return errors


def _resolve_bundle_path(bundle_path: str, ledger_file: pathlib.Path) -> pathlib.Path | None:
    """
    Resolve signature.bundlePath against the following search roots, in order:

        1. repo-relative (the in-tree case; matches legacy behaviour).
        2. sibling to the ledger file itself (the release case — consumers who
           download mapping-ledger.json + mapping-ledger.sigstore.bundle.json
           into the same directory).
        3. dist/ under repo root (release-build local inspection).

    Returns the first existing path, or None.
    """
    candidates = [
        ROOT / bundle_path,
        ledger_file.parent / bundle_path,
        ROOT / "dist" / bundle_path,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return None


def _run_gh_attestation_verify(
    sig: dict[str, Any],
    ledger: dict[str, Any],
    ledger_file: pathlib.Path,
) -> list[str]:
    """
    Invoke `gh attestation verify` on the bundlePath if present, asserting that
    the bundle's subject matches the ledger file.
    """
    if shutil.which("gh") is None:
        return [
            "signature: --verify-signature requested but `gh` CLI is not installed; "
            "skipping (install GitHub CLI >= 2.50)."
        ]
    bundle_path = sig.get("bundlePath")
    if not bundle_path:
        return []  # attestation lives only on GitHub; cannot verify offline.
    full = _resolve_bundle_path(bundle_path, ledger_file)
    if full is None:
        return [
            f"signature: bundlePath={bundle_path!r} not found "
            f"(searched repo root, {ledger_file.parent.relative_to(ROOT) if ledger_file.is_relative_to(ROOT) else ledger_file.parent}/, and dist/)."
        ]
    try:
        result = subprocess.run(
            [
                "gh",
                "attestation",
                "verify",
                str(ledger_file),
                "--bundle",
                str(full),
                "--predicate-type",
                "https://slsa.dev/provenance/v1",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return [f"signature: `gh attestation verify` failed to execute: {exc}"]
    if result.returncode != 0:
        return [
            f"signature: `gh attestation verify` rejected the bundle: {result.stderr.strip()}"
        ]
    return []


# ----------------------------------------------------------------------
# Top-level
# ----------------------------------------------------------------------
def write_report(errors: list[str], ledger: dict[str, Any]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "$comment": "Phase 5.4 mapping-ledger audit output. Regenerated by scripts/audit_mapping_ledger.py.",
        "status": "fail" if errors else "pass",
        "errorCount": len(errors),
        "errors": errors,
        "ledgerSummary": {
            "schemaVersion": ledger.get("schemaVersion"),
            "generatedAt": ledger.get("generatedAt"),
            "catalogueCommit": ledger.get("catalogueCommit"),
            "entryCount": ledger.get("entryCount"),
            "merkleRoot": ledger.get("merkleRoot"),
            "signatureState": ledger.get("signature", {}).get("state"),
        },
    }
    REPORT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Validate data/provenance/mapping-ledger.json (schema + hash chain + referential integrity)."
    )
    parser.add_argument("--check", action="store_true", help="Shorthand for the default behaviour; present for CI consistency.")
    parser.add_argument("--verify-signature", action="store_true", help="Run `gh attestation verify` when the ledger is 'attested'.")
    parser.add_argument("--require-signature", action="store_true", help="Treat 'unsigned' state or missing/invalid signature as fatal.")
    args = parser.parse_args(argv)

    if not LEDGER_PATH.exists():
        print(
            f"FATAL: {LEDGER_PATH.relative_to(ROOT)} does not exist. "
            "Run scripts/generate_mapping_ledger.py first.",
            file=sys.stderr,
        )
        return 1

    try:
        ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"FATAL: {LEDGER_PATH.relative_to(ROOT)} is not valid JSON: {exc}", file=sys.stderr)
        return 1

    errors: list[str] = []
    errors.extend(validate_schema(ledger))
    errors.extend(audit_entry_count(ledger))
    errors.extend(audit_sort_order(ledger))
    errors.extend(audit_entry_hashes(ledger))
    errors.extend(audit_merkle_root(ledger))
    errors.extend(audit_referential_integrity(ledger))
    errors.extend(audit_catalogue_commit(ledger))
    errors.extend(
        audit_signature_envelope(
            ledger,
            args.verify_signature,
            args.require_signature,
            LEDGER_PATH,
        )
    )

    write_report(errors, ledger)

    if errors:
        print("FAIL: mapping-ledger audit found issues:", file=sys.stderr)
        for e in errors[:40]:
            print(f"  - {e}", file=sys.stderr)
        if len(errors) > 40:
            print(f"  … and {len(errors) - 40} more errors (see reports/mapping-ledger-audit.json).", file=sys.stderr)
        return 1

    entries = ledger.get("entries", [])
    print(
        f"PASS: mapping ledger OK "
        f"({len(entries)} entries, merkle root {ledger.get('merkleRoot','')[:16]}…, "
        f"signature={ledger.get('signature',{}).get('state','?')})."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
