#!/usr/bin/env python3
"""audit_sme_review_signoffs.py - Phase 5.2 SME-review gate.

CI guardrail for the SME-review framework introduced in Phase 5.2
(see ``docs/sme-review-guide.md``).  It enforces two invariants:

1.  **Schema invariant.** ``data/provenance/sme-signoffs.json``
    validates against ``schemas/sme-review-signoff.schema.json``
    (JSON Schema draft 2020-12).  This guarantees every record has
    the required fields, valid reviewer-role / outcome / check enums,
    and the basic structure of ``scope`` and ``checks``.

2.  **Semantic invariants** (not expressible in JSON Schema alone):

    *  ``outcome == 'approved-with-revisions'`` requires a non-empty
       ``revisionsRequested`` array.
    *  ``outcome == 'conditional'`` requires a non-empty
       ``caveats`` array AND every caveat must be mirrored by at
       least one ``smeCaveat`` field on a UC sidecar in scope.
    *  ``outcome == 'rejected'`` requires a non-empty
       ``rejectionReason`` (\u2265 20 chars).
    *  ``outcome == 'approved'`` requires every ``checks.*`` entry to
       be ``'pass'`` or ``'n/a'``.  A ``'fail'`` in an ``approved``
       signoff is contradictory.
    *  A single ``reviewer`` may not sign off on a commit twice; the
       ``(commit, reviewer)`` pair is unique.  Two different SMEs
       signing off on the same commit IS permitted (dual-SME review,
       see docs/sme-review-guide.md \u00a75).
    *  ``fixtureReplayResult`` must be self-consistent:
       ``replayed=false`` implies ``checks.splCorrectness`` is ``'n/a'``;
       ``replayed=true`` with ``positiveDetected=false`` or
       ``negativeSilent=false`` implies ``checks.splCorrectness`` is
       ``'fail'``.  A silent mismatch is reported as an error.
    *  Every UC ID in ``scope.ucs`` maps to a real sidecar on disk
       (``use-cases/cat-NN/uc-<id>.json``).
    *  Every fixture path in ``scope.fixtures`` resolves to a real
       file under ``sample-data/``.
    *  Every evidence-pack path in ``scope.evidencePacks`` resolves
       to a real file under ``docs/evidence-packs/``.
    *  ``reviewerRole == 'splunk-engineer'`` with ``checks.splCorrectness``
       set to ``'pass'`` SHOULD record a ``fixtureReplayResult`` with
       ``replayed=true``.  This is a WARNING (not a hard error) so
       that a senior SME's structural review can still land.

The script runs offline and stdlib-only except for ``jsonschema``,
already a project dependency.

Exit codes
----------

    0  All checks passed (warnings may still be emitted).
    1  Schema validation failed, semantic invariant violated, or the
       signoff file was missing or malformed.

Usage
-----

    python3 scripts/audit_sme_review_signoffs.py
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
SCHEMA_PATH = REPO / "schemas" / "sme-review-signoff.schema.json"
DATA_PATH = REPO / "data" / "provenance" / "sme-signoffs.json"
USE_CASES = REPO / "use-cases"
SAMPLE_DATA = REPO / "sample-data"
EVIDENCE_PACKS = REPO / "docs" / "evidence-packs"

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
    schema = _load_json(SCHEMA_PATH, "SME-review signoff schema")
    validator = Draft202012Validator(schema)
    issues: list[str] = []
    for error in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        path = "/".join(str(p) for p in error.path) or "<root>"
        issues.append(f"schema: {path}: {error.message}")
    return issues


def _uc_sidecar_path(uc_id: str) -> Path | None:
    """Return the expected sidecar path for a UC id, or ``None`` if the
    id does not parse.

    The historical ``use-cases/`` layout uses zero-padded category
    directories for single-digit categories (``cat-01`` … ``cat-09``)
    and un-padded for two-digit (``cat-10`` upwards).  Resolve against
    whichever variant actually exists on disk.
    """
    m = _UC_ID_RE.match(uc_id)
    if not m:
        return None
    cat = m.group("cat")
    filename = f"uc-{uc_id}.json"
    # Prefer the padded variant when the category is single-digit AND
    # the file exists there; fall back to the un-padded form otherwise.
    candidates: list[Path] = []
    if len(cat) == 1:
        candidates.append(USE_CASES / f"cat-0{cat}" / filename)
    candidates.append(USE_CASES / f"cat-{cat}" / filename)
    for cand in candidates:
        if cand.is_file():
            return cand
    # Return the un-padded form as the "expected" path when neither
    # variant exists so the error message reads naturally.
    return candidates[-1]


def _collect_uc_sme_caveats(uc_ids: list[str]) -> set[str]:
    """Load every UC sidecar in ``uc_ids`` and return the set of
    ``smeCaveat`` strings found across their ``compliance[]`` entries.
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
            caveat = entry.get("smeCaveat")
            if isinstance(caveat, str) and caveat.strip():
                caveats.add(caveat.strip())
    return caveats


def _validate_semantics(data: dict) -> tuple[list[str], list[str]]:
    """Return ``(errors, warnings)`` for the signoff file."""
    errors: list[str] = []
    warnings: list[str] = []
    signoffs = data.get("signoffs")
    if not isinstance(signoffs, list):
        return errors, warnings

    seen_pairs: dict[tuple[str, str], int] = {}
    for idx, record in enumerate(signoffs):
        if not isinstance(record, dict):
            continue
        prefix = f"signoffs[{idx}] (pr={record.get('pr', '?')})"

        outcome = record.get("outcome")
        revisions = record.get("revisionsRequested") or []
        caveats = record.get("caveats") or []
        rejection = record.get("rejectionReason")
        checks = record.get("checks") or {}
        reviewer = record.get("reviewer") or ""
        role = record.get("reviewerRole")
        commit = record.get("commit")
        scope = record.get("scope") or {}
        ucs = scope.get("ucs") or []
        fixtures = scope.get("fixtures") or []
        evidence_packs = scope.get("evidencePacks") or []
        replay = record.get("fixtureReplayResult") or {}

        # Outcome-driven required fields.
        if outcome == "approved-with-revisions" and not revisions:
            errors.append(
                f"{prefix}: outcome='approved-with-revisions' requires a "
                f"non-empty 'revisionsRequested' array describing each "
                f"revision the SME required before sign-off "
                f"(docs/sme-review-guide.md \u00a73.7)."
            )
        if outcome == "conditional" and not caveats:
            errors.append(
                f"{prefix}: outcome='conditional' requires a non-empty "
                f"'caveats' array; each caveat must be mirrored in an "
                f"smeCaveat field on the relevant UC sidecar "
                f"(docs/sme-review-guide.md \u00a74.1)."
            )
        if outcome == "rejected":
            if not isinstance(rejection, str) or len(rejection.strip()) < 20:
                errors.append(
                    f"{prefix}: outcome='rejected' requires a "
                    f"'rejectionReason' of at least 20 characters "
                    f"explaining why the UC cannot land as-authored "
                    f"(docs/sme-review-guide.md \u00a73.7)."
                )

        # 'approved' must have all checks pass/n-a.
        if outcome == "approved" and isinstance(checks, dict):
            failing = [k for k, v in checks.items() if v == "fail"]
            if failing:
                errors.append(
                    f"{prefix}: outcome='approved' is inconsistent with "
                    f"checks.{failing} == 'fail'. An SME approval must "
                    f"resolve every failing check before merge; use "
                    f"'approved-with-revisions' if revisions were required "
                    f"(docs/sme-review-guide.md \u00a73.7)."
                )

        # Reviewer/commit uniqueness (two-SME review is fine; same SME twice is not).
        if isinstance(commit, str):
            if not _SHA_RE.match(commit):
                errors.append(
                    f"{prefix}: commit SHA {commit!r} is not a valid short/long hex SHA."
                )
            if isinstance(reviewer, str) and reviewer.strip():
                pair = (commit, reviewer.strip())
                if pair in seen_pairs:
                    first_idx = seen_pairs[pair]
                    errors.append(
                        f"{prefix}: reviewer {reviewer!r} has already signed off on "
                        f"commit {commit} in signoffs[{first_idx}]. Dual-SME review "
                        f"requires TWO DIFFERENT reviewers on the same commit."
                    )
                else:
                    seen_pairs[pair] = idx

        # Fixture replay self-consistency.
        if isinstance(replay, dict) and replay:
            replayed = replay.get("replayed")
            pos_detected = replay.get("positiveDetected")
            neg_silent = replay.get("negativeSilent")
            spl_check = checks.get("splCorrectness")

            if replayed is False and spl_check == "pass":
                errors.append(
                    f"{prefix}: fixtureReplayResult.replayed=false but "
                    f"checks.splCorrectness='pass'. A 'pass' on SPL correctness "
                    f"without a fixture replay is not defensible; set "
                    f"splCorrectness='n/a' or replay the fixture "
                    f"(docs/sme-review-guide.md \u00a74.2)."
                )
            if replayed is True:
                if (pos_detected is False or neg_silent is False) and spl_check == "pass":
                    errors.append(
                        f"{prefix}: fixtureReplayResult shows positiveDetected="
                        f"{pos_detected} / negativeSilent={neg_silent} but "
                        f"checks.splCorrectness='pass'. A fixture replay mismatch "
                        f"must be graded 'fail' or explained via "
                        f"approved-with-revisions."
                    )
                if pos_detected is True and neg_silent is True and spl_check == "fail":
                    errors.append(
                        f"{prefix}: fixtureReplayResult shows a clean replay "
                        f"(positiveDetected=true, negativeSilent=true) but "
                        f"checks.splCorrectness='fail'. The check grade "
                        f"contradicts the replay result."
                    )

        # splunk-engineer SHOULD replay fixtures (warning, not error).
        if (
            role == "splunk-engineer"
            and checks.get("splCorrectness") == "pass"
            and (not isinstance(replay, dict) or replay.get("replayed") is not True)
        ):
            warnings.append(
                f"{prefix}: reviewerRole='splunk-engineer' with "
                f"checks.splCorrectness='pass' should record a "
                f"fixtureReplayResult with replayed=true (see "
                f"docs/sme-review-guide.md \u00a74.2)."
            )

        # UC existence
        for uc_id in ucs:
            if not isinstance(uc_id, str):
                continue
            path = _uc_sidecar_path(uc_id)
            if path is None:
                errors.append(
                    f"{prefix}: scope.ucs entry {uc_id!r} is not a valid UC id."
                )
            elif not path.is_file():
                errors.append(
                    f"{prefix}: scope.ucs entry {uc_id} has no sidecar on disk "
                    f"(expected {path.relative_to(REPO)}). Ensure the UC exists "
                    f"before recording the SME sign-off."
                )

        # Fixture existence (must live under sample-data/).
        for fixture in fixtures:
            if not isinstance(fixture, str):
                continue
            fixture_path = (REPO / fixture).resolve()
            try:
                fixture_path.relative_to(SAMPLE_DATA.resolve())
            except ValueError:
                errors.append(
                    f"{prefix}: scope.fixtures entry {fixture!r} must live under "
                    f"sample-data/ (got {fixture!r})."
                )
                continue
            if not fixture_path.is_file():
                errors.append(
                    f"{prefix}: scope.fixtures entry {fixture!r} does not resolve "
                    f"to a file on disk."
                )

        # Evidence-pack existence (must live under docs/evidence-packs/).
        for pack in evidence_packs:
            if not isinstance(pack, str):
                continue
            bare = pack.split("#", 1)[0]
            pack_path = (REPO / bare).resolve()
            try:
                pack_path.relative_to(EVIDENCE_PACKS.resolve())
            except ValueError:
                errors.append(
                    f"{prefix}: scope.evidencePacks entry {pack!r} must live "
                    f"under docs/evidence-packs/ (got {pack!r})."
                )
                continue
            if not pack_path.is_file():
                errors.append(
                    f"{prefix}: scope.evidencePacks entry {pack!r} does not "
                    f"resolve to a file on disk (resolved to "
                    f"{pack_path.relative_to(REPO)})."
                )

        # Caveat mirror: every recorded caveat must show up as a
        # smeCaveat on at least one UC sidecar in the review scope.
        if caveats and ucs:
            sidecar_caveats = _collect_uc_sme_caveats(
                [u for u in ucs if isinstance(u, str)]
            )
            for caveat in caveats:
                if not isinstance(caveat, str):
                    continue
                if caveat.strip() not in sidecar_caveats:
                    errors.append(
                        f"{prefix}: caveat {caveat[:80]!r} is recorded in "
                        f"the SME signoff but is not present as an "
                        f"'smeCaveat' on any UC in scope.ucs {ucs}. "
                        f"Add the caveat to the relevant compliance[] entry "
                        f"before merging (see docs/sme-review-guide.md \u00a74.1)."
                    )

    baseline = data.get("baseline_commit")
    if isinstance(baseline, str) and not _SHA_RE.match(baseline):
        errors.append(
            f"baseline_commit: {baseline!r} is not a valid short/long hex SHA."
        )

    return errors, warnings


def _print_summary(data: dict, errors: list[str], warnings: list[str]) -> None:
    signoffs = data.get("signoffs") or []
    print("=== SME-review signoff audit ===")
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
                f"role={role:<22} outcome={outcome:<24} regulations=[{regs}]"
            )
    print()
    if warnings:
        print(f"=== WARNINGS ({len(warnings)}) ===")
        for msg in warnings:
            print(msg)
        print()
    if errors:
        print(f"=== ERRORS ({len(errors)}) ===")
        for msg in errors:
            print(msg)
    else:
        print("No errors. SME-review gate is GREEN.")


def main() -> int:
    data = _load_json(DATA_PATH, "SME-review signoff file")
    errors: list[str] = []
    errors.extend(_validate_schema(data))
    semantic_errors, warnings = _validate_semantics(data)
    errors.extend(semantic_errors)
    _print_summary(data, errors, warnings)
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
