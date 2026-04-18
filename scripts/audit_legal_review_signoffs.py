#!/usr/bin/env python3
"""audit_legal_review_signoffs.py - Phase 4.5b legal-review gate.

CI guardrail for the legal-review framework introduced in Phase 4.5b
(see ``docs/legal-review-guide.md``).  It enforces two invariants:

1.  **Schema invariant.** ``data/provenance/legal-review-signoffs.json``
    validates against ``schemas/legal-review-signoff.schema.json``
    (JSON Schema draft 2020-12).  This guarantees every record has
    the required fields, valid tier-1 regulation enum values, and
    consistent SHAs.

2.  **Semantic invariants** (not expressible in JSON Schema alone):

    *  ``outcome == 'approved-with-revisions'`` requires a non-empty
       ``revisionsRequested`` array.
    *  ``outcome == 'conditional'`` requires a non-empty
       ``caveats`` array.
    *  Each ``commit`` SHA is unique across the ``signoffs`` array.
    *  ``paralegal`` reviewerRole is only permitted when the review
       scope is limited to UC IDs (clause-number accuracy).  Primer
       or evidence-pack scope requires ``internal-counsel`` or
       ``external-counsel`` per the guide (\u00a72.1).
    *  Every UC ID in ``scope.ucs`` maps to a real sidecar on disk
       (``use-cases/cat-NN/uc-<id>.json``).
    *  Every document path in ``scope.documents`` resolves to a real
       file in the repo (the leading ``#anchor`` suffix is stripped
       before the existence check).
    *  Every ``caveats[]`` entry is mirrored by at least one
       ``legalCaveat`` field on a UC sidecar in the review scope.
       This prevents caveats from being "recorded and forgotten".

The script runs offline and stdlib-only except for ``jsonschema``,
already a project dependency.

Exit codes
----------

    0  All checks passed.
    1  Schema validation failed, semantic invariant violated, or the
       signoff file was missing or malformed.

Usage
-----

    python3 scripts/audit_legal_review_signoffs.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError as err:  # pragma: no cover - local ergonomics only
    raise SystemExit(
        "ERROR: jsonschema is required. Install with 'pip install jsonschema'."
    ) from err

REPO = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO / "schemas" / "legal-review-signoff.schema.json"
DATA_PATH = REPO / "data" / "provenance" / "legal-review-signoffs.json"
USE_CASES = REPO / "use-cases"

_SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")
_UC_ID_RE = re.compile(
    r"^(?P<cat>0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$"
)


def _load_json(path: Path, label: str) -> dict:
    if not path.is_file():
        sys.stderr.write(f"ERROR: {label} not found at {path}\n")
        raise SystemExit(1)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        sys.stderr.write(f"ERROR: {label} is not valid JSON: {err}\n")
        raise SystemExit(1) from err


def _validate_schema(data: dict) -> list[str]:
    schema = _load_json(SCHEMA_PATH, "legal-review signoff schema")
    validator = Draft202012Validator(schema)
    issues: list[str] = []
    for error in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        path = "/".join(str(p) for p in error.path) or "<root>"
        issues.append(f"schema: {path}: {error.message}")
    return issues


def _uc_sidecar_path(uc_id: str) -> Path | None:
    """Return the expected sidecar path for a UC id, or ``None`` if the
    id does not parse.

    A UC sidecar lives at ``use-cases/cat-<cat>/uc-<id>.json`` where
    ``<cat>`` is the category number and ``<id>`` is the full
    dotted id.  Callers should check ``path.is_file()`` before
    reading.
    """
    m = _UC_ID_RE.match(uc_id)
    if not m:
        return None
    cat = m.group("cat")
    return USE_CASES / f"cat-{cat}" / f"uc-{uc_id}.json"


def _collect_uc_legal_caveats(uc_ids: list[str]) -> set[str]:
    """Load every UC sidecar in ``uc_ids`` and return the set of
    ``legalCaveat`` strings found across their ``compliance[]`` entries.

    Used by the caveat-mirror semantic check.  Missing sidecars are
    silently skipped; the existence check is done separately.
    """
    caveats: set[str] = set()
    for uc_id in uc_ids:
        path = _uc_sidecar_path(uc_id)
        if path is None or not path.is_file():
            continue
        try:
            sidecar = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue  # Caught by the normal schema audit, not our concern here.
        compliance = sidecar.get("compliance") or []
        for entry in compliance:
            if not isinstance(entry, dict):
                continue
            caveat = entry.get("legalCaveat")
            if isinstance(caveat, str) and caveat.strip():
                caveats.add(caveat.strip())
    return caveats


def _validate_semantics(data: dict) -> list[str]:
    issues: list[str] = []
    signoffs = data.get("signoffs")
    if not isinstance(signoffs, list):
        return issues

    seen_commits: dict[str, int] = {}
    for idx, record in enumerate(signoffs):
        if not isinstance(record, dict):
            continue
        prefix = f"signoffs[{idx}] (pr={record.get('pr', '?')})"

        outcome = record.get("outcome")
        revisions = record.get("revisionsRequested") or []
        caveats = record.get("caveats") or []

        if outcome == "approved-with-revisions" and not revisions:
            issues.append(
                f"{prefix}: outcome='approved-with-revisions' requires a "
                f"non-empty 'revisionsRequested' array describing each "
                f"revision counsel required before sign-off."
            )
        if outcome == "conditional" and not caveats:
            issues.append(
                f"{prefix}: outcome='conditional' requires a non-empty "
                f"'caveats' array; each caveat must be mirrored in a "
                f"legalCaveat field on the relevant UC sidecar (see "
                f"docs/legal-review-guide.md \u00a73.1)."
            )

        commit = record.get("commit")
        if isinstance(commit, str):
            if not _SHA_RE.match(commit):
                issues.append(
                    f"{prefix}: commit SHA {commit!r} is not a valid short/long hex SHA."
                )
            elif commit in seen_commits:
                first_idx = seen_commits[commit]
                issues.append(
                    f"{prefix}: commit {commit} already signed off in "
                    f"signoffs[{first_idx}]. Each commit must be reviewed exactly once."
                )
            else:
                seen_commits[commit] = idx

        scope = record.get("scope") or {}
        role = record.get("reviewerRole")
        docs = scope.get("documents") or []
        ucs = scope.get("ucs") or []

        # Paralegal scope restriction
        if role == "paralegal" and (docs or not ucs):
            issues.append(
                f"{prefix}: reviewerRole='paralegal' may only sign off on "
                f"clause-number-accuracy reviews (scope.ucs is non-empty "
                f"and scope.documents is empty). Primer or evidence-pack "
                f"review requires internal-counsel or external-counsel "
                f"(see docs/legal-review-guide.md \u00a72.1)."
            )

        # UC existence
        for uc_id in ucs:
            if not isinstance(uc_id, str):
                continue
            path = _uc_sidecar_path(uc_id)
            if path is None:
                issues.append(
                    f"{prefix}: scope.ucs entry {uc_id!r} is not a valid UC id."
                )
            elif not path.is_file():
                issues.append(
                    f"{prefix}: scope.ucs entry {uc_id} has no sidecar on disk "
                    f"(expected {path.relative_to(REPO)}). Ensure the UC exists "
                    f"before recording the legal sign-off."
                )

        # Document existence (strip trailing #anchor)
        for doc in docs:
            if not isinstance(doc, str):
                continue
            bare = doc.split("#", 1)[0]
            doc_path = REPO / bare
            if not doc_path.is_file():
                issues.append(
                    f"{prefix}: scope.documents entry {doc!r} does not resolve "
                    f"to a file under the repo root (resolved path "
                    f"{doc_path.relative_to(REPO)})."
                )

        # Caveat mirror: every recorded caveat must show up as a
        # legalCaveat on at least one UC sidecar in the review scope.
        if caveats and ucs:
            sidecar_caveats = _collect_uc_legal_caveats(
                [u for u in ucs if isinstance(u, str)]
            )
            for caveat in caveats:
                if not isinstance(caveat, str):
                    continue
                if caveat.strip() not in sidecar_caveats:
                    issues.append(
                        f"{prefix}: caveat {caveat[:80]!r} is recorded in "
                        f"the legal signoff but is not present as a "
                        f"'legalCaveat' on any UC in scope.ucs {ucs}. "
                        f"Add the caveat to the relevant compliance[] entry "
                        f"before merging (see docs/legal-review-guide.md \u00a73.1)."
                    )

    baseline = data.get("baseline_commit")
    if isinstance(baseline, str) and not _SHA_RE.match(baseline):
        issues.append(
            f"baseline_commit: {baseline!r} is not a valid short/long hex SHA."
        )

    return issues


def _print_summary(data: dict, issues: list[str]) -> None:
    signoffs = data.get("signoffs") or []
    print("=== Legal-review signoff audit ===")
    print(f"Baseline commit : {data.get('baseline_commit', '<missing>')}")
    print(f"Signoffs total  : {len(signoffs)}")
    if signoffs:
        print("Recent entries  :")
        for record in signoffs[-5:]:
            pr = record.get("pr", "?")
            date = record.get("date", "?")
            commit = record.get("commit", "?")
            role = record.get("reviewerRole", "?")
            outcome = record.get("outcome", "?")
            regs = ", ".join(
                (record.get("scope") or {}).get("regulations") or []
            )
            print(
                f"  {pr:<8} {date}  {commit:<10} "
                f"role={role:<18} outcome={outcome:<24} regulations=[{regs}]"
            )
    print()
    if issues:
        print(f"=== ISSUES ({len(issues)}) ===")
        for msg in issues:
            print(msg)
    else:
        print("No issues. Legal-review gate is GREEN.")


def main() -> int:
    data = _load_json(DATA_PATH, "legal-review signoff file")
    issues: list[str] = []
    issues.extend(_validate_schema(data))
    issues.extend(_validate_semantics(data))
    _print_summary(data, issues)
    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
