#!/usr/bin/env python3
"""Validate SARIF 2.1.0 logs emitted by ``generate-sarif``.

Checks:
* ``version == "2.1.0"``
* ``$schema`` matches the canonical SchemaStore URI
* Every ``result.ruleId`` exists in ``runs[*].tool.driver.rules``
* Every ``result.level`` is a SARIF 2.1.0 level enum value
* Every ``artifactLocation.uri`` resolves under the repo (or is a
  synthetic ``content/cat-NN/UC-X.Y.Z.json`` path)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from splunk_uc.generators.sarif_emit import REPO_ROOT, SARIF_SCHEMA, SARIF_VERSION

_VALID_LEVELS = frozenset({"none", "note", "warning", "error"})
_SIDEcar_PATH_RE = re.compile(r"^content/cat-\d+[^/]*/UC-\d+\.\d+\.\d+\.json$")


def _load_sarif(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: top-level value must be an object")
    return payload


def _validate_schema(payload: dict[str, Any], *, path_label: str) -> list[str]:
    errors: list[str] = []
    schema = payload.get("$schema")
    if schema != SARIF_SCHEMA:
        errors.append(f"{path_label}: $schema must be {SARIF_SCHEMA!r}, got {schema!r}")
    version = payload.get("version")
    if version != SARIF_VERSION:
        errors.append(f"{path_label}: version must be {SARIF_VERSION!r}, got {version!r}")
    runs = payload.get("runs")
    if not isinstance(runs, list):
        errors.append(f"{path_label}: runs must be a list")
    return errors


def _uri_resolves(uri: str) -> bool:
    if _SIDEcar_PATH_RE.match(uri):
        return True
    candidate = REPO_ROOT / uri
    return candidate.is_file()


def validate_sarif_payload(payload: dict[str, Any], *, path_label: str = "<sarif>") -> list[str]:
    """Return a list of validation error messages (empty == valid)."""
    errors = _validate_schema(payload, path_label=path_label)
    runs = payload.get("runs")
    if not isinstance(runs, list):
        return errors

    for run_idx, run in enumerate(runs):
        if not isinstance(run, dict):
            errors.append(f"{path_label}: runs[{run_idx}] must be an object")
            continue
        tool = run.get("tool")
        if not isinstance(tool, dict):
            errors.append(f"{path_label}: runs[{run_idx}].tool missing")
            continue
        driver = tool.get("driver")
        if not isinstance(driver, dict):
            errors.append(f"{path_label}: runs[{run_idx}].tool.driver missing")
            continue
        rules_raw = driver.get("rules")
        if not isinstance(rules_raw, list):
            errors.append(f"{path_label}: runs[{run_idx}].tool.driver.rules must be a list")
            continue
        rule_ids = {
            str(rule.get("id"))
            for rule in rules_raw
            if isinstance(rule, dict) and isinstance(rule.get("id"), str)
        }

        results = run.get("results")
        if not isinstance(results, list):
            errors.append(f"{path_label}: runs[{run_idx}].results must be a list")
            continue

        for res_idx, result in enumerate(results):
            if not isinstance(result, dict):
                errors.append(f"{path_label}: runs[{run_idx}].results[{res_idx}] must be an object")
                continue
            rule_id = result.get("ruleId")
            if not isinstance(rule_id, str):
                errors.append(
                    f"{path_label}: runs[{run_idx}].results[{res_idx}].ruleId must be a string"
                )
            elif rule_id not in rule_ids:
                errors.append(
                    f"{path_label}: orphan ruleId {rule_id!r} "
                    f"(runs[{run_idx}].results[{res_idx}])"
                )

            level = result.get("level")
            if not isinstance(level, str):
                errors.append(
                    f"{path_label}: runs[{run_idx}].results[{res_idx}].level must be a string"
                )
            elif level not in _VALID_LEVELS:
                errors.append(
                    f"{path_label}: invalid level {level!r} "
                    f"(runs[{run_idx}].results[{res_idx}])"
                )

            locations = result.get("locations")
            if not isinstance(locations, list) or not locations:
                errors.append(
                    f"{path_label}: runs[{run_idx}].results[{res_idx}] missing locations"
                )
                continue
            loc0 = locations[0]
            if not isinstance(loc0, dict):
                continue
            physical = loc0.get("physicalLocation")
            if not isinstance(physical, dict):
                continue
            artifact = physical.get("artifactLocation")
            if not isinstance(artifact, dict):
                continue
            uri = artifact.get("uri")
            if not isinstance(uri, str):
                errors.append(
                    f"{path_label}: runs[{run_idx}].results[{res_idx}] missing artifact uri"
                )
            elif not _uri_resolves(uri):
                errors.append(
                    f"{path_label}: unresolved artifact uri {uri!r} "
                    f"(runs[{run_idx}].results[{res_idx}])"
                )

    return errors


def validate_sarif_file(path: Path) -> list[str]:
    try:
        payload = _load_sarif(path)
    except ValueError as exc:
        return [str(exc)]
    return validate_sarif_payload(payload, path_label=str(path))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sarif",
        type=Path,
        action="append",
        dest="sarif_paths",
        help="SARIF file to validate (repeatable). Default: dist/sarif/catalogue.sarif",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 when any validation error is found (CI gate).",
    )
    args = parser.parse_args(argv)

    paths = args.sarif_paths or [REPO_ROOT / "dist" / "sarif" / "catalogue.sarif"]
    all_errors: list[str] = []

    for path in paths:
        if not path.is_file():
            msg = f"FATAL: SARIF file does not exist: {path}"
            print(msg, file=sys.stderr)
            all_errors.append(msg)
            continue
        errors = validate_sarif_file(path)
        if errors:
            for err in errors:
                print(f"ERROR: {err}", file=sys.stderr)
            all_errors.extend(errors)
        else:
            print(f"OK: {path}")

    if all_errors:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
