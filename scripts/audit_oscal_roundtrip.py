#!/usr/bin/env python3
"""audit_oscal_roundtrip.py — Phase 4.5e OSCAL round-trip gate.

Validates every OSCAL component-definition document we ship under
``api/v1/oscal/component-definitions/*.json`` (except ``index.json``)
against two invariants:

1. **NIST OSCAL 1.1.1 schema compliance.** The document must validate
   against the official NIST component-definition schema we ingest
   to ``schemas/oscal/v1.1.1/oscal_component_schema.json``.  The
   ingest-manifest tracks the schema's SHA-256 so CI can detect any
   local tampering of the reference document.

2. **Canonical byte-equality round-trip.** The file as committed must
   equal ``json.dumps(payload, indent=2, sort_keys=True,
   ensure_ascii=False) + "\\n"`` — i.e., the exact canonicalisation
   used by ``scripts/generate_api_surface.py``.  Any drift means the
   file was edited by hand (or an older, non-canonical serialiser)
   and must be regenerated before it can be trusted as a machine
   input.

Additional sanity checks (hard-failing):

* ``metadata.oscal-version`` must be ``"1.1.1"`` — we do not ship
  mixed OSCAL versions.
* A corresponding crosswalk source must exist at
  ``data/crosswalks/oscal/component-definition-<uc>.json`` (or the
  legacy ``component-definition-uc-<uc>.json`` shape) so every public
  OSCAL endpoint is traceable back to the authoring pipeline.
* The recorded SHA-256 of the NIST schema in
  ``data/provenance/ingest-manifest.json`` must match the on-disk
  bytes of the schema we actually validated against.

Soft checks (warnings, never hard failures):

* UUIDs on ``components[]`` and ``implemented-requirements[]`` should
  be RFC-4122 v1-5 strings.  Violations are surfaced but do not block
  CI so we can investigate without blocking unrelated releases.

Why two different dimensions?  Schema compliance protects the shape of
what we publish; round-trip equality protects the byte integrity of
what consumers cache (OSCAL tools, AI agents, and the Splunk app
generator all hash the JSON and expect the hash to be stable).  A
schema-valid file that does not round-trip is still a regression
because it breaks any downstream cache-key or signature.

Output
------

A deterministic report at ``reports/oscal-roundtrip.json`` with:

* per-file records (schema errors, round-trip drift flag, metadata
  sanity checks, crosswalk source path);
* summary counts per status bucket;
* the schema's expected SHA-256 from the ingest-manifest and the
  observed SHA-256 on disk (so auditors can cross-check reproducibility
  without rerunning the script).

Exit codes
----------

    0   No hard failures.
    1   At least one hard failure, or ``--check`` requested and the
        committed report differs from the freshly-generated one.

Usage
-----

    python3 scripts/audit_oscal_roundtrip.py
    python3 scripts/audit_oscal_roundtrip.py --check   # drift-check only
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator

REPO = Path(__file__).resolve().parent.parent
API_CDEF_DIR = REPO / "api" / "v1" / "oscal" / "component-definitions"
CROSSWALK_DIR = REPO / "data" / "crosswalks" / "oscal"
SCHEMA_PATH = REPO / "schemas" / "oscal" / "v1.1.1" / "oscal_component_schema.json"
MANIFEST_PATH = REPO / "data" / "provenance" / "ingest-manifest.json"
REPORT_PATH = REPO / "reports" / "oscal-roundtrip.json"

EXPECTED_OSCAL_VERSION = "1.1.1"
SCHEMA_SOURCE_ID = "nist-oscal-component-definition-schema-v1.1.1"

_FILENAME_RE = re.compile(r"^(\d+\.\d+\.\d+)\.json$")
_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-"
    r"[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
)

# Status buckets.  "ok" is the only non-failing status; everything
# else is a CI hard failure.
STATUS_OK = "ok"
STATUS_BAD_FILENAME = "bad-filename"
STATUS_BAD_JSON = "bad-json"
STATUS_SCHEMA_VIOLATION = "schema-violation"
STATUS_ROUNDTRIP_DRIFT = "roundtrip-drift"
STATUS_WRONG_OSCAL_VERSION = "wrong-oscal-version"
STATUS_MISSING_SOURCE = "missing-source"


def _load_schema() -> dict[str, Any]:
    """Load and lightly pre-process the NIST OSCAL schema.

    NIST's authoritative component-definition schema uses Unicode
    property escapes ``\\p{L}`` / ``\\p{N}`` in the TokenDatatype
    pattern, which Python's ``re`` module does not understand.  Every
    OSCAL token we ship is pure ASCII (control IDs like
    ``gdpr-art-321b``, prop names like ``assurance``), so we
    substitute the two escapes with ``[A-Za-z]`` / ``[0-9]`` character
    classes.  This keeps the validator strict for our content without
    pulling in the third-party ``regex`` library.  Any future need for
    non-ASCII OSCAL tokens would require revisiting this choice and
    depending on ``regex`` (or switching to an ajv-based validator).
    """
    raw = SCHEMA_PATH.read_text(encoding="utf-8")
    patched = raw.replace(r"\\p{L}", "[A-Za-z]").replace(r"\\p{N}", "[0-9]")
    schema = json.loads(patched)
    return schema


def _schema_sha256_on_disk() -> str:
    return hashlib.sha256(SCHEMA_PATH.read_bytes()).hexdigest()


def _schema_sha256_from_manifest() -> tuple[str | None, str | None]:
    """Return ``(expected_sha256, local_path)`` from the ingest-manifest."""
    if not MANIFEST_PATH.is_file():
        return None, None
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    for entry in manifest.get("provenance", []):
        if entry.get("source_id") == SCHEMA_SOURCE_ID:
            return entry.get("sha256"), entry.get("local")
    return None, None


def _canonical_serialise(payload: Any) -> str:
    """Match ``scripts/generate_api_surface.py._write_json`` exactly."""
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _extract_uc_id(path: Path) -> str | None:
    m = _FILENAME_RE.match(path.name)
    return m.group(1) if m else None


def _find_crosswalk_source(uc_id: str) -> Path | None:
    if not CROSSWALK_DIR.is_dir():
        return None
    for name in (
        f"component-definition-{uc_id}.json",
        f"component-definition-uc-{uc_id}.json",
    ):
        candidate = CROSSWALK_DIR / name
        if candidate.is_file():
            return candidate
    return None


def _audit_file(validator: Draft7Validator, path: Path) -> dict[str, Any]:
    rel = str(path.relative_to(REPO))
    record: dict[str, Any] = {
        "file": rel,
        "uc_id": None,
        "status": STATUS_OK,
        "issues": [],
        "warnings": [],
        "schema_errors": [],
        "roundtrip_drift": False,
        "oscal_version": None,
        "crosswalk_source": None,
        "crosswalk_source_missing": False,
    }

    uc_id = _extract_uc_id(path)
    record["uc_id"] = uc_id
    if uc_id is None:
        record["status"] = STATUS_BAD_FILENAME
        record["issues"].append(
            "filename does not match the expected <uc-id>.json grammar"
        )
        return record

    original_text = path.read_text(encoding="utf-8")

    try:
        payload = json.loads(original_text)
    except json.JSONDecodeError as err:
        record["status"] = STATUS_BAD_JSON
        record["issues"].append(f"JSONDecodeError: {err}")
        return record

    # NIST schema validation.  We keep only the first 100 errors so a
    # badly-broken file does not balloon the report.
    errors = sorted(
        validator.iter_errors(payload),
        key=lambda e: (tuple(str(p) for p in e.absolute_path), e.message),
    )
    if errors:
        record["status"] = STATUS_SCHEMA_VIOLATION
        for err in errors[:100]:
            record["schema_errors"].append(
                {
                    "path": "/".join(str(p) for p in err.absolute_path),
                    "message": err.message,
                    "validator": err.validator,
                }
            )
        record["issues"].append(
            f"{len(errors)} schema violation(s) "
            f"(first 100 recorded in schema_errors)"
            if len(errors) > 100
            else f"{len(errors)} schema violation(s)"
        )

    # Canonical round-trip.
    canonical = _canonical_serialise(payload)
    if canonical != original_text:
        record["roundtrip_drift"] = True
        record["issues"].append(
            "byte-equality round-trip failed — regenerate with "
            "scripts/generate_api_surface.py"
        )
        if record["status"] == STATUS_OK:
            record["status"] = STATUS_ROUNDTRIP_DRIFT

    # Metadata sanity checks.
    cdef = payload.get("component-definition") if isinstance(payload, dict) else None
    if isinstance(cdef, dict):
        meta = cdef.get("metadata") if isinstance(cdef, dict) else None
        oscal_version = meta.get("oscal-version") if isinstance(meta, dict) else None
        record["oscal_version"] = oscal_version
        if oscal_version != EXPECTED_OSCAL_VERSION:
            record["issues"].append(
                f"metadata.oscal-version is {oscal_version!r}, "
                f"expected '{EXPECTED_OSCAL_VERSION}'"
            )
            if record["status"] == STATUS_OK:
                record["status"] = STATUS_WRONG_OSCAL_VERSION

        # UUID warnings (never hard-fail).
        for comp in cdef.get("components", []) or []:
            if isinstance(comp, dict):
                uuid = comp.get("uuid")
                if uuid and not _UUID_RE.match(uuid):
                    record["warnings"].append(
                        f"component uuid not RFC-4122: {uuid}"
                    )
                for ci in comp.get("control-implementations") or []:
                    if not isinstance(ci, dict):
                        continue
                    for ir in ci.get("implemented-requirements") or []:
                        if not isinstance(ir, dict):
                            continue
                        uuid = ir.get("uuid")
                        if uuid and not _UUID_RE.match(uuid):
                            record["warnings"].append(
                                f"implemented-requirement uuid not RFC-4122: {uuid}"
                            )
    else:
        # No component-definition key at all — the schema validation
        # above will have already caught this; flag it explicitly for
        # the human-readable summary.
        record["issues"].append(
            "payload has no top-level 'component-definition' object"
        )
        if record["status"] == STATUS_OK:
            record["status"] = STATUS_SCHEMA_VIOLATION

    # Crosswalk provenance.
    source = _find_crosswalk_source(uc_id)
    if source is None:
        record["crosswalk_source_missing"] = True
        record["issues"].append(
            f"no crosswalk source under {CROSSWALK_DIR.relative_to(REPO)} "
            f"for UC-{uc_id}"
        )
        if record["status"] == STATUS_OK:
            record["status"] = STATUS_MISSING_SOURCE
    else:
        record["crosswalk_source"] = str(source.relative_to(REPO))

    return record


def _collect_records(
    validator: Draft7Validator,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if API_CDEF_DIR.is_dir():
        for path in sorted(API_CDEF_DIR.glob("*.json")):
            if path.name == "index.json":
                continue
            records.append(_audit_file(validator, path))

    summary: dict[str, Any] = {
        "total_files_examined": len(records),
        "statuses": {},
        "hard_failures": 0,
        "warning_count": 0,
        "roundtrip_drift_count": 0,
        "schema_violation_count": 0,
    }
    for rec in records:
        status = rec["status"]
        summary["statuses"][status] = summary["statuses"].get(status, 0) + 1
        if status != STATUS_OK:
            summary["hard_failures"] += 1
        if rec["roundtrip_drift"]:
            summary["roundtrip_drift_count"] += 1
        if rec["schema_errors"]:
            summary["schema_violation_count"] += 1
        summary["warning_count"] += len(rec["warnings"])

    records.sort(key=lambda r: (r["uc_id"] or "", r["file"]))
    return records, summary


def _render_report(
    records: list[dict[str, Any]],
    summary: dict[str, Any],
    schema_meta: dict[str, Any],
) -> str:
    payload = {
        "$comment": (
            "Phase 4.5e OSCAL round-trip report. Generated by "
            "scripts/audit_oscal_roundtrip.py. Every file under "
            "api/v1/oscal/component-definitions/ (except index.json) is "
            "validated against the NIST OSCAL 1.1.1 component-definition "
            "schema AND must round-trip byte-identically through "
            "json.dumps(..., indent=2, sort_keys=True, ensure_ascii=False). "
            "Any schema violation, round-trip drift, mismatched oscal-version, "
            "or missing crosswalk source hard-fails the CI."
        ),
        "schema": schema_meta,
        "records": records,
        "summary": summary,
    }
    return _canonical_serialise(payload)


def _print_human_summary(
    records: list[dict[str, Any]],
    summary: dict[str, Any],
    schema_meta: dict[str, Any],
) -> None:
    print("=== OSCAL round-trip gate ===")
    print(f"Schema           : {schema_meta['path']}")
    print(f"OSCAL version    : {schema_meta['oscal_version']}")
    print(
        f"Schema SHA-256   : observed={schema_meta['observed_sha256']}, "
        f"expected={schema_meta['expected_sha256']}, "
        f"match={schema_meta['expected_matches_observed']}"
    )
    print(f"Files examined   : {summary['total_files_examined']}")
    print(f"Schema violations: {summary['schema_violation_count']}")
    print(f"Round-trip drifts: {summary['roundtrip_drift_count']}")
    print(f"Warnings         : {summary['warning_count']}")
    print(f"Hard failures    : {summary['hard_failures']}")
    print()
    print("Status distribution:")
    for status in sorted(summary["statuses"].keys()):
        count = summary["statuses"][status]
        if count:
            print(f"  {status:<22} {count}")

    hard_recs = [r for r in records if r["status"] != STATUS_OK]
    if hard_recs:
        print()
        print("Hard failures:")
        for rec in hard_recs:
            print(f"  {rec['uc_id']} ({rec['status']}) - {rec['file']}")
            for issue in rec["issues"]:
                print(f"    - {issue}")
            for err in rec["schema_errors"][:5]:
                print(f"    - schema {err['path']}: {err['message'][:200]}")
            if len(rec["schema_errors"]) > 5:
                print(
                    f"    - ... {len(rec['schema_errors']) - 5} more schema error(s)"
                )


def _schema_meta() -> dict[str, Any]:
    observed = _schema_sha256_on_disk()
    expected, expected_local = _schema_sha256_from_manifest()
    return {
        "path": str(SCHEMA_PATH.relative_to(REPO)),
        "oscal_version": EXPECTED_OSCAL_VERSION,
        "observed_sha256": observed,
        "expected_sha256": expected,
        "expected_local": expected_local,
        "expected_matches_observed": bool(expected and expected == observed),
        "manifest_source_id": SCHEMA_SOURCE_ID,
        "manifest_path": str(MANIFEST_PATH.relative_to(REPO)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase 4.5e OSCAL round-trip gate."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "Regenerate the report in memory and diff against the "
            "committed reports/oscal-roundtrip.json; exit non-zero on drift."
        ),
    )
    args = parser.parse_args(argv)

    if not SCHEMA_PATH.is_file():
        sys.stderr.write(
            f"ERROR: NIST OSCAL schema missing at {SCHEMA_PATH.relative_to(REPO)}.\n"
            f"Re-download it from https://github.com/usnistgov/OSCAL/releases "
            f"and record provenance in {MANIFEST_PATH.relative_to(REPO)}.\n"
        )
        return 1

    schema_meta = _schema_meta()

    try:
        schema = _load_schema()
    except json.JSONDecodeError as err:
        sys.stderr.write(f"ERROR: NIST OSCAL schema is not valid JSON: {err}\n")
        return 1

    validator = Draft7Validator(schema)
    records, summary = _collect_records(validator)

    # Hard-fail if the schema on disk does not match the hash committed
    # in the ingest-manifest.  This catches tampering and stale schema
    # copies before they silently weaken the gate.
    schema_hash_mismatch = (
        schema_meta["expected_sha256"] is not None
        and not schema_meta["expected_matches_observed"]
    )
    if schema_hash_mismatch:
        summary["hard_failures"] += 1
        summary["statuses"]["schema-hash-mismatch"] = (
            summary["statuses"].get("schema-hash-mismatch", 0) + 1
        )
        summary["schema_hash_mismatch"] = True
    else:
        summary["schema_hash_mismatch"] = False

    payload_str = _render_report(records, summary, schema_meta)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if args.check:
        if not REPORT_PATH.is_file():
            sys.stderr.write(
                f"ERROR: --check requested but {REPORT_PATH.relative_to(REPO)} "
                "does not exist. Run without --check first to generate it.\n"
            )
            return 1
        existing = REPORT_PATH.read_text(encoding="utf-8")
        if existing != payload_str:
            sys.stderr.write(
                "ERROR: oscal-roundtrip.json is out of date. "
                "Run `python3 scripts/audit_oscal_roundtrip.py` and "
                "commit the updated report.\n"
            )
            return 1
    else:
        REPORT_PATH.write_text(payload_str, encoding="utf-8")

    _print_human_summary(records, summary, schema_meta)
    print()
    if summary["hard_failures"]:
        if schema_hash_mismatch:
            print(
                "ERROR: committed schema SHA-256 does not match "
                "the ingest-manifest record."
            )
        print("=== OSCAL GATE: RED ===")
        return 1
    print("=== OSCAL GATE: GREEN ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
