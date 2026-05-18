"""``lift-validate`` verb — apply an AI-authored diff under the firewall.

This is the §5 contract of the content-quality lift loop. It takes a
JSON diff produced by a subagent and refuses to commit it unless every
check in the chain passes:

1.  The diff JSON has the required shape ``{uc_id, target_tier, lifted_fields}``.
2.  The diff's ``uc_id`` matches the ``--uc-id`` arg (bare or prefixed).
3.  The diff's ``target_tier`` matches the ``--target-tier`` arg.
4.  Every key in ``lifted_fields`` is in :data:`LIFT_SURFACE_FIELDS`
    and not in :data:`FIREWALLED_FIELDS`.
5.  Each lifted value validates against the field's JSON schema
    fragment in ``schemas/uc.schema.json``.
6.  Identity fields (``id``, ``title``) on the in-memory lifted UC
    are unchanged from the on-disk sidecar.
7.  The lifted UC's score against the chosen target tier is
    **strictly greater** than the pre-lift score.
8.  ``--strict`` (opt-in) additionally runs the catalog-wide audit chain.

On success the lifted content is written back to the sidecar and the
markdown twin is regenerated. On any failure the on-disk sidecar is
left untouched and a structured error is printed to stderr.

The verb is pure-function except for:
* the optional ``generate-md-from-json`` subprocess (skip with
  ``--skip-md-regen`` — tests use this for speed).
* the optional ``--strict`` audit-chain subprocesses.

Usage::

    python -m splunk_uc lift-validate UC-15.1.1 --diff /tmp/lift-UC-15.1.1.diff.json
    python -m splunk_uc lift-validate UC-15.1.1 --diff <path> --dry-run
    python -m splunk_uc lift-validate UC-15.1.1 --diff <path> --strict
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import jsonschema

from splunk_uc.tools.lift._common import (
    DEFAULT_CONTENT_ROOT,
    REPO_ROOT,
    TargetTier,
    load_sidecar,
    resolve_sidecar_path,
    score_uc,
)

SRC_DIR = REPO_ROOT / "src"
SCHEMA_PATH = REPO_ROOT / "schemas" / "uc.schema.json"

#: Fields the diff is allowed to touch (spec §4).
LIFT_SURFACE_FIELDS: frozenset[str] = frozenset(
    {
        "description",
        "value",
        "dataSources",
        "implementation",
        "detailedImplementation",
        "visualization",
        "knownFalsePositives",
        "references",
        "controlTest",
        "evidence",
        "exclusions",
        "equipmentModels",
        "mitreAttack",
        "dataModelAcceleration",
    }
)

#: Fields the diff MUST NEVER touch (spec §4 firewall).
FIREWALLED_FIELDS: frozenset[str] = frozenset(
    {
        "spl",
        "cimSpl",
        "id",
        "title",
        "monitoringType",
        "splunkPillar",
        "criticality",
        "difficulty",
        "compliance",
        "fixtureRef",
        "assurance",
        "grandmaExplanation",
    }
)

#: Identity fields that must never change on either side of the diff.
_IDENTITY_FIELDS = ("id", "title")

#: Catalog-wide audits invoked when --strict is set. They scan the
#: full live catalog (none of these verbs accept a --files filter), so
#: --strict is meaningful only when the lifted sidecar has been written
#: to its real path in the canonical content tree.
STRICT_AUDIT_VERBS = (
    "audit-uc-structure",
    "audit-spl-hallucinations",
    "audit-prerequisites",
    "audit-roadmap-consistency",
)


class _ValidationError(Exception):
    """Raised when the diff or the lifted sidecar fails the §5 contract."""


def _load_diff(diff_path: Path) -> dict[str, Any]:
    """Parse and shape-check the diff JSON; raise on any malformation."""
    try:
        raw = diff_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise _ValidationError(f"cannot read diff file {diff_path}: {exc}") from exc
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise _ValidationError(f"diff is not valid JSON ({diff_path}): {exc}") from exc
    if not isinstance(payload, dict):
        raise _ValidationError(f"diff must be a JSON object; got {type(payload).__name__}")
    missing = sorted({"uc_id", "target_tier", "lifted_fields"} - payload.keys())
    if missing:
        raise _ValidationError(f"diff missing required keys: {missing}")
    if not isinstance(payload["lifted_fields"], dict):
        raise _ValidationError("diff.lifted_fields must be an object mapping field name -> value")
    return cast(dict[str, Any], payload)


def _check_identity_match(
    diff: dict[str, Any],
    uc_id_arg: str,
    target_tier_arg: TargetTier,
) -> None:
    """Confirm the diff is targeting the same UC + tier as the CLI args."""
    expected_bare = uc_id_arg.removeprefix("UC-")
    if diff["uc_id"] not in (uc_id_arg, expected_bare):
        raise _ValidationError(
            f"diff.uc_id {diff['uc_id']!r} does not match CLI uc_id {uc_id_arg!r}"
        )
    if diff["target_tier"] != target_tier_arg.value:
        raise _ValidationError(
            f"diff.target_tier {diff['target_tier']!r} does not match CLI "
            f"--target-tier {target_tier_arg.value!r}"
        )


def _check_field_allowlist(diff: dict[str, Any]) -> None:
    """Reject any lifted_fields key outside the lift surface or in the firewall."""
    keys = set(diff["lifted_fields"].keys())
    firewalled = sorted(keys & FIREWALLED_FIELDS)
    if firewalled:
        raise _ValidationError(
            f"diff touches firewalled fields (refused by §5 firewall): {firewalled}"
        )
    out_of_surface = sorted(keys - LIFT_SURFACE_FIELDS)
    if out_of_surface:
        raise _ValidationError(
            f"diff touches fields outside the lift surface (allow-list): {out_of_surface}"
        )


def _load_schema() -> dict[str, Any]:
    with SCHEMA_PATH.open(encoding="utf-8") as handle:
        return cast(dict[str, Any], json.load(handle))


def _validate_lifted_types(diff: dict[str, Any], schema: dict[str, Any]) -> None:
    """Validate each lifted value against its per-field JSON schema fragment.

    We do not validate the whole sidecar here (that is enforced at build
    time by ``audit-uc-structure``); we just want a fast, deterministic
    type / shape check per touched field so a malformed diff fails fast.
    """
    props = schema.get("properties", {})
    for field_name, new_value in diff["lifted_fields"].items():
        sub_schema = props.get(field_name)
        if sub_schema is None:
            # Field is on the lift surface but not in the schema — this
            # would only happen if LIFT_SURFACE_FIELDS drifts from the
            # schema. Surface it as a validation error rather than crash.
            raise _ValidationError(
                f"no schema fragment for lifted field {field_name!r}; "
                "schema and LIFT_SURFACE_FIELDS may have drifted"
            )
        try:
            jsonschema.validate(instance=new_value, schema=sub_schema)
        except jsonschema.ValidationError as exc:
            raise _ValidationError(
                f"lifted value for {field_name!r} fails schema: {exc.message}"
            ) from exc


def _apply_diff(sidecar: dict[str, Any], diff: dict[str, Any]) -> dict[str, Any]:
    """Return a new sidecar dict with the diff's lifted_fields applied."""
    out = deepcopy(sidecar)
    for field_name, new_value in diff["lifted_fields"].items():
        out[field_name] = new_value
    return out


def _dump_sidecar(data: dict[str, Any]) -> str:
    """Serialise a UC sidecar in the project's canonical form.

    Matches the convention used by ``generators/grandma_explanations``
    and friends: ``indent=2``, ``ensure_ascii=False`` (raw UTF-8 — 97 %
    of the catalog uses raw em dashes), trailing newline.
    """
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def _check_identity_preserved(original: dict[str, Any], lifted: dict[str, Any]) -> None:
    for field_name in _IDENTITY_FIELDS:
        if original.get(field_name) != lifted.get(field_name):
            raise _ValidationError(
                f"identity field {field_name!r} changed by diff "
                f"(was {original.get(field_name)!r}, became {lifted.get(field_name)!r})"
            )


def _run_strict_audits() -> None:
    """Run the opt-in catalog-wide audit chain.

    Each audit scans the full live content tree (none of them accept a
    ``--files`` filter today). The lifted sidecar must already be on
    disk at its canonical path when this runs.
    """
    env = {**os.environ, "PYTHONPATH": str(SRC_DIR)}
    for verb in STRICT_AUDIT_VERBS:
        result = subprocess.run(
            [sys.executable, "-m", "splunk_uc", verb, "--check"],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        if result.returncode != 0:
            raise _ValidationError(
                f"strict audit {verb} failed (exit {result.returncode}):\n"
                f"{result.stdout}\n{result.stderr}"
            )


def _regen_markdown(sidecar_path: Path) -> None:
    env = {**os.environ, "PYTHONPATH": str(SRC_DIR)}
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "splunk_uc",
            "generate-md-from-json",
            "--files",
            str(sidecar_path),
        ],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    if result.returncode != 0:
        raise _ValidationError(
            f"generate-md-from-json failed (exit {result.returncode}):\n"
            f"{result.stdout}\n{result.stderr}"
        )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m splunk_uc lift-validate",
        description=(
            "Apply an AI-authored diff to one UC and run the §5 validation "
            "chain. The on-disk sidecar is rewritten only when every check "
            "in the chain passes."
        ),
    )
    parser.add_argument("uc_id", help="UC identifier, e.g. UC-15.1.1")
    parser.add_argument(
        "--diff",
        required=True,
        type=Path,
        help="Path to the JSON diff emitted by the subagent.",
    )
    parser.add_argument(
        "--target-tier",
        default="silver",
        choices=["silver", "gold", "gold-v2"],
    )
    parser.add_argument(
        "--content-root",
        type=Path,
        default=DEFAULT_CONTENT_ROOT,
        help="Override the content root (for tests).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run every check but do NOT write the lifted sidecar.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Also run the catalog-wide audit chain after writing the "
            "lifted sidecar. Slow; opt in only for the orchestrator."
        ),
    )
    parser.add_argument(
        "--skip-md-regen",
        action="store_true",
        help="Skip regenerating the .md twin (test mode).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable success payload to stdout.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    try:
        sidecar_path = resolve_sidecar_path(args.uc_id, content_root=args.content_root)
        original = load_sidecar(sidecar_path)
        target_tier = TargetTier.from_str(args.target_tier)
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"lift-validate: {exc}", file=sys.stderr)
        return 1

    try:
        diff = _load_diff(args.diff)
        _check_identity_match(diff, args.uc_id, target_tier)
        _check_field_allowlist(diff)
        schema = _load_schema()
        _validate_lifted_types(diff, schema)
        lifted = _apply_diff(original, diff)
        _check_identity_preserved(original, lifted)
    except _ValidationError as exc:
        print(f"lift-validate: REFUSE: {exc}", file=sys.stderr)
        return 1

    score_before = score_uc(sidecar_path, target_tier=target_tier).current_score

    # Capture the on-disk bytes verbatim before writing so we can revert
    # byte-for-byte if any downstream check fails. Re-serialising via
    # ``json.dumps`` would not preserve formatting / encoding choices
    # made by the curator (e.g. raw UTF-8 em dashes vs ``\u2014``).
    original_bytes = sidecar_path.read_bytes()

    sidecar_path.write_text(_dump_sidecar(lifted), encoding="utf-8")
    try:
        score_after = score_uc(sidecar_path, target_tier=target_tier).current_score
        if score_after <= score_before:
            sidecar_path.write_bytes(original_bytes)
            print(
                "lift-validate: REFUSE: post-lift score "
                f"{score_after} is not strictly greater than pre-lift "
                f"{score_before}",
                file=sys.stderr,
            )
            return 1
        if args.strict:
            try:
                _run_strict_audits()
            except _ValidationError as exc:
                sidecar_path.write_bytes(original_bytes)
                print(f"lift-validate: REFUSE: {exc}", file=sys.stderr)
                return 1
        if args.dry_run:
            sidecar_path.write_bytes(original_bytes)
        elif not args.skip_md_regen:
            try:
                _regen_markdown(sidecar_path)
            except _ValidationError as exc:
                sidecar_path.write_bytes(original_bytes)
                print(f"lift-validate: REFUSE: {exc}", file=sys.stderr)
                return 1
    except Exception:
        sidecar_path.write_bytes(original_bytes)
        raise

    if args.json:
        print(
            json.dumps(
                {
                    "uc_id": args.uc_id,
                    "target_tier": target_tier.value,
                    "score_before": score_before,
                    "score_after": score_after,
                    "dry_run": bool(args.dry_run),
                    "wrote": str(sidecar_path),
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        prefix = "DRY-RUN OK" if args.dry_run else "OK"
        print(f"lift-validate: {prefix}: {score_before} -> {score_after}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
