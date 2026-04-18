#!/usr/bin/env python3
"""audit_peer_review_signoffs.py - Phase 4.5a peer-review gate.

This script is the CI gatekeeper for the peer-review framework that was
introduced in Phase 4.5a (see ``docs/peer-review-guide.md``).  It
enforces two invariants:

1.  **Schema invariant.** ``data/provenance/peer-review-signoffs.json``
    validates against ``schemas/peer-review-signoff.schema.json``
    (JSON Schema draft 2020-12).  This guarantees every record has the
    required rubric fields, valid scope markers, and consistent SHAs.

2.  **Semantic invariants** (not expressible in JSON Schema):

    *  ``author`` and ``reviewer`` MUST differ (case-insensitive, with
       optional leading ``@`` stripped).  No self-review.
    *  ``notes`` is REQUIRED whenever any check in ``checks`` is
       ``fail``.  Reviewers must document the fix.
    *  ``notes`` is REQUIRED whenever ``checks.derivatives`` is
       ``n/a``.  Reviewers must state why the PR is not derivative
       content.
    *  Each ``commit`` SHA is unique across the ``signoffs`` array.
       A single commit is reviewed once.
    *  ``signoffs`` is append-only relative to ``baseline_commit``: the
       script does not enforce this over time (git history is the
       source of truth), but it does flag commit SHAs that look
       syntactically invalid.

The script is deliberately offline and stdlib-only except for
``jsonschema``, which is already a project dependency (see
``scripts/audit_compliance_mappings.py``).

Exit codes
----------

    0  All checks passed.
    1  Schema validation failed, semantic invariant violated, or the
       signoff file was missing or malformed.

Usage
-----

    python3 scripts/audit_peer_review_signoffs.py

CI wiring lives in ``.github/workflows/validate.yml`` under the
``Phase 4.5 QA gate`` section.
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
SCHEMA_PATH = REPO / "schemas" / "peer-review-signoff.schema.json"
DATA_PATH = REPO / "data" / "provenance" / "peer-review-signoffs.json"

# Accept SHAs between 7 and 40 hex chars.  The schema does the same,
# but we keep a local copy so the semantic stage can produce richer
# error messages without re-parsing the schema JSON.
_SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")


def _load_json(path: Path, label: str) -> dict:
    """Read ``path`` and return the parsed JSON, exiting on failure.

    The ``label`` is a human-readable name used in the error message.
    """
    if not path.is_file():
        sys.stderr.write(f"ERROR: {label} not found at {path}\n")
        raise SystemExit(1)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        sys.stderr.write(f"ERROR: {label} is not valid JSON: {err}\n")
        raise SystemExit(1) from err


def _normalise_handle(handle: str) -> str:
    """Strip a leading ``@`` and lower-case the handle for comparison.

    GitHub usernames are case-insensitive; we compare after dropping
    the optional ``@`` prefix so ``@Alice`` and ``alice`` are treated
    as the same person (and therefore flagged as self-review).
    """
    return handle.lstrip("@").strip().lower()


def _validate_schema(data: dict) -> list[str]:
    """Run JSON Schema validation and return human-readable errors."""
    schema = _load_json(SCHEMA_PATH, "peer-review signoff schema")
    validator = Draft202012Validator(schema)
    issues: list[str] = []
    for error in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        path = "/".join(str(p) for p in error.path) or "<root>"
        issues.append(f"schema: {path}: {error.message}")
    return issues


def _validate_semantics(data: dict) -> list[str]:
    """Check invariants JSON Schema cannot express.

    Returns a list of human-readable issues.  The list is empty when
    the file passes every semantic check.
    """
    issues: list[str] = []

    signoffs = data.get("signoffs")
    if not isinstance(signoffs, list):
        # Schema validation will already have caught this; bail out
        # cleanly so we do not produce a cascade of NoneType errors.
        return issues

    seen_commits: dict[str, int] = {}
    for idx, record in enumerate(signoffs):
        if not isinstance(record, dict):
            continue  # Schema stage handles type errors.
        prefix = f"signoffs[{idx}] (pr={record.get('pr', '?')})"

        author = record.get("author", "")
        reviewer = record.get("reviewer", "")
        if isinstance(author, str) and isinstance(reviewer, str):
            if _normalise_handle(author) == _normalise_handle(reviewer):
                issues.append(
                    f"{prefix}: author and reviewer must differ "
                    f"(got author={author!r}, reviewer={reviewer!r}). "
                    f"Self-review is not permitted."
                )

        # secondReviewer, if present, must differ from both author and reviewer
        second = record.get("secondReviewer")
        if isinstance(second, str) and second:
            second_norm = _normalise_handle(second)
            if isinstance(author, str) and second_norm == _normalise_handle(author):
                issues.append(
                    f"{prefix}: secondReviewer must differ from author "
                    f"(got author={author!r}, secondReviewer={second!r})."
                )
            if isinstance(reviewer, str) and second_norm == _normalise_handle(reviewer):
                issues.append(
                    f"{prefix}: secondReviewer must differ from primary reviewer "
                    f"(got reviewer={reviewer!r}, secondReviewer={second!r})."
                )

        checks = record.get("checks") or {}
        notes = record.get("notes", "")
        notes_is_present = isinstance(notes, str) and notes.strip() != ""

        fail_names: list[str] = []
        for name, value in checks.items():
            if value == "fail":
                fail_names.append(name)
        if fail_names and not notes_is_present:
            issues.append(
                f"{prefix}: one or more checks failed {sorted(fail_names)} "
                f"but 'notes' is empty. Explain the fix applied before merge."
            )

        derivatives_result = checks.get("derivatives")
        if derivatives_result == "n/a" and not notes_is_present:
            issues.append(
                f"{prefix}: checks.derivatives is 'n/a' but 'notes' is empty. "
                f"State why the PR is not derivative content "
                f"(e.g. 'UC is authored from scratch, no UK GDPR/CCPA/nFADP/LGPD/APPI entries')."
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

    baseline = data.get("baseline_commit")
    if isinstance(baseline, str) and not _SHA_RE.match(baseline):
        issues.append(
            f"baseline_commit: {baseline!r} is not a valid short/long hex SHA."
        )

    return issues


def _print_summary(data: dict, issues: list[str]) -> None:
    """Emit a deterministic, human-friendly summary to stdout."""
    signoffs = data.get("signoffs") or []
    print("=== Peer-review signoff audit ===")
    print(f"Baseline commit : {data.get('baseline_commit', '<missing>')}")
    print(f"Signoffs total  : {len(signoffs)}")
    if signoffs:
        print("Recent entries  :")
        for record in signoffs[-5:]:
            pr = record.get("pr", "?")
            date = record.get("date", "?")
            commit = record.get("commit", "?")
            author = record.get("author", "?")
            reviewer = record.get("reviewer", "?")
            scope = ", ".join(record.get("scope", []) or [])
            print(
                f"  {pr:<8} {date}  {commit:<10} "
                f"author={author}  reviewer={reviewer}  scope=[{scope}]"
            )
    print()
    if issues:
        print(f"=== ISSUES ({len(issues)}) ===")
        for msg in issues:
            print(msg)
    else:
        print("No issues. Peer-review gate is GREEN.")


def main() -> int:
    data = _load_json(DATA_PATH, "peer-review signoff file")
    issues: list[str] = []
    issues.extend(_validate_schema(data))
    issues.extend(_validate_semantics(data))
    _print_summary(data, issues)
    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
