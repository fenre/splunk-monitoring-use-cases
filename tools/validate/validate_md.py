#!/usr/bin/env python3
"""tools.validate.validate_md — validate the per-UC content/ tree.

Replaces the v6 root-level ``validate_md.py`` that walked
``use-cases/cat-NN-*.md`` monoliths and only checked structural
markers. The new validator walks the per-UC ``content/`` tree
introduced by the ``migrate-to-per-uc-files`` migration:

* every ``UC-X.Y.Z.json`` is parsed and validated against
  ``schemas/uc.schema.json``,
* the embedded ``id`` must match the filename,
* the leading ``X.`` of the id must match the parent category id
  recorded in ``_category.json``,
* every ``UC-X.Y.Z.json`` must have a sibling ``UC-X.Y.Z.md``
  (so editors always have a prose canvas), and
* each ``_category.json`` is sanity-checked for required metadata.

Usage:

    python3 -m tools.validate.validate_md            # validate everything
    python3 -m tools.validate.validate_md --quiet    # exit code only
    python3 -m tools.validate.validate_md content/cat-22-regulatory-compliance

Exit code is 0 when all checks pass, otherwise 1. Designed to run in
CI without external dependencies; when ``jsonschema`` is available the
validator uses Draft 2020-12 errors directly. Otherwise it falls back
to a small built-in checker that enforces required keys, types, and
``additionalProperties: false`` from ``uc.schema.json``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CONTENT_DIR = REPO_ROOT / "content"
UC_SCHEMA = REPO_ROOT / "schemas" / "uc.schema.json"
UC_FILE_RE_PATTERN = r"UC-(?P<id>\d+\.\d+\.\d+)\.json"


# ---------------------------------------------------------------------------
# Schema loading
# ---------------------------------------------------------------------------


def _load_schema() -> dict[str, Any]:
    try:
        with UC_SCHEMA.open(encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"FATAL: cannot read {UC_SCHEMA}: {exc}")


# ---------------------------------------------------------------------------
# Optional jsonschema validator (preferred when installed)
# ---------------------------------------------------------------------------


def _try_jsonschema_validator(schema: dict[str, Any]):
    try:
        import jsonschema  # type: ignore[import-not-found]
    except Exception:
        return None
    try:
        from jsonschema import Draft202012Validator  # type: ignore
    except Exception:
        try:
            from jsonschema import Draft7Validator as Draft202012Validator  # type: ignore
        except Exception:
            return None

    validator = Draft202012Validator(schema)

    def _validate(payload: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        for err in sorted(validator.iter_errors(payload), key=lambda e: list(e.path)):
            location = "/".join(str(p) for p in err.path) or "<root>"
            errors.append(f"{location}: {err.message}")
        return errors

    return _validate


# ---------------------------------------------------------------------------
# Built-in fallback validator (covers the subset of JSON Schema that
# uc.schema.json actually uses: type, required, enum, pattern, minLength,
# minItems, additionalProperties, items, properties, oneOf, format=uri)
# ---------------------------------------------------------------------------


import re as _re


def _type_matches(value: Any, type_name: str) -> bool:
    if type_name == "object":
        return isinstance(value, dict)
    if type_name == "array":
        return isinstance(value, list)
    if type_name == "string":
        return isinstance(value, str)
    if type_name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if type_name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if type_name == "boolean":
        return isinstance(value, bool)
    if type_name == "null":
        return value is None
    return True


def _walk(
    value: Any,
    schema: dict[str, Any],
    path: list[str],
    errors: list[str],
) -> None:
    # oneOf
    one_of = schema.get("oneOf")
    if one_of:
        sub_errors: list[list[str]] = []
        matches = 0
        for option in one_of:
            tmp: list[str] = []
            _walk(value, option, path, tmp)
            if not tmp:
                matches += 1
            sub_errors.append(tmp)
        if matches != 1:
            location = "/".join(path) or "<root>"
            errors.append(
                f"{location}: did not match exactly one schema in oneOf "
                f"({matches} matches)"
            )
        return

    # type
    expected_type = schema.get("type")
    if expected_type and not _type_matches(value, expected_type):
        location = "/".join(path) or "<root>"
        errors.append(
            f"{location}: expected type '{expected_type}' but got "
            f"{type(value).__name__}"
        )
        return

    # enum
    if "enum" in schema and value not in schema["enum"]:
        location = "/".join(path) or "<root>"
        errors.append(
            f"{location}: value {value!r} is not one of {schema['enum']}"
        )

    # string-specific
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            location = "/".join(path) or "<root>"
            errors.append(
                f"{location}: string length {len(value)} < minLength "
                f"{schema['minLength']}"
            )
        if "pattern" in schema:
            try:
                if not _re.search(schema["pattern"], value):
                    location = "/".join(path) or "<root>"
                    errors.append(
                        f"{location}: value {value!r} does not match pattern "
                        f"{schema['pattern']}"
                    )
            except _re.error:
                pass
        fmt = schema.get("format")
        if fmt == "uri":
            if not value.lower().startswith(("http://", "https://")):
                location = "/".join(path) or "<root>"
                errors.append(
                    f"{location}: value {value!r} does not look like a URI"
                )
        elif fmt == "date":
            if not _re.match(r"^\d{4}-\d{2}-\d{2}$", value):
                location = "/".join(path) or "<root>"
                errors.append(
                    f"{location}: value {value!r} is not an ISO-8601 date"
                )

    # array-specific
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            location = "/".join(path) or "<root>"
            errors.append(
                f"{location}: array length {len(value)} < minItems "
                f"{schema['minItems']}"
            )
        if schema.get("uniqueItems"):
            seen: list[Any] = []
            for item in value:
                if item in seen:
                    location = "/".join(path) or "<root>"
                    errors.append(
                        f"{location}: array contains duplicate item {item!r}"
                    )
                    break
                seen.append(item)
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for idx, item in enumerate(value):
                _walk(item, item_schema, path + [str(idx)], errors)

    # object-specific
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        for req in required:
            if req not in value:
                location = "/".join(path) or "<root>"
                errors.append(f"{location}: missing required property '{req}'")
        if schema.get("additionalProperties") is False:
            allowed = set(properties.keys())
            for key in value:
                if key not in allowed:
                    location = "/".join(path) or "<root>"
                    errors.append(
                        f"{location}: additional property '{key}' not allowed"
                    )
        for key, sub_schema in properties.items():
            if key in value:
                _walk(value[key], sub_schema, path + [key], errors)


def _builtin_validator(schema: dict[str, Any]):
    def _validate(payload: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        _walk(payload, schema, [], errors)
        return errors

    return _validate


# ---------------------------------------------------------------------------
# Tree walker
# ---------------------------------------------------------------------------


def _iter_categories(root: Path) -> Iterator[Path]:
    return iter(sorted(p for p in root.iterdir() if p.is_dir() and p.name.startswith("cat-")))


def _read_json(path: Path) -> Optional[dict[str, Any]]:
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


# ---------------------------------------------------------------------------
# Per-file checks
# ---------------------------------------------------------------------------


def _check_uc_file(
    uc_path: Path,
    cat_id: int,
    validator,
    errors: list[str],
) -> None:
    rel = uc_path.relative_to(REPO_ROOT)
    payload = _read_json(uc_path)
    if payload is None:
        errors.append(f"{rel}: invalid JSON")
        return

    # Filename ↔ id consistency
    m = _re.match(r"^UC-(\d+\.\d+\.\d+)\.json$", uc_path.name)
    if not m:
        errors.append(f"{rel}: filename does not match UC-X.Y.Z.json")
        return
    file_uc_id = m.group(1)
    payload_uc_id = payload.get("id", "")
    if payload_uc_id != file_uc_id:
        errors.append(
            f"{rel}: filename id '{file_uc_id}' != payload id '{payload_uc_id}'"
        )

    # Category cross-check
    payload_cat = payload_uc_id.split(".")[0] if payload_uc_id else ""
    if payload_cat and str(cat_id) != payload_cat:
        errors.append(
            f"{rel}: id starts with category '{payload_cat}' but parent "
            f"_category.json declares cat id {cat_id}"
        )

    # Companion .md must exist
    md_sibling = uc_path.with_suffix(".md")
    if not md_sibling.exists():
        errors.append(f"{rel}: missing companion {md_sibling.name}")

    # Schema validation
    for problem in validator(payload):
        errors.append(f"{rel}: {problem}")


def _check_category(category_dir: Path, validator, errors: list[str]) -> int:
    """Validate a single content/cat-XX-slug/ directory.

    Returns the number of UC files validated (for reporting).
    """
    rel_dir = category_dir.relative_to(REPO_ROOT)
    cat_meta_path = category_dir / "_category.json"
    if not cat_meta_path.exists():
        errors.append(f"{rel_dir}/: missing _category.json")
        return 0
    cat_meta = _read_json(cat_meta_path)
    if cat_meta is None:
        errors.append(f"{cat_meta_path.relative_to(REPO_ROOT)}: invalid JSON")
        return 0
    cat_id = cat_meta.get("id")
    if not isinstance(cat_id, int):
        errors.append(
            f"{cat_meta_path.relative_to(REPO_ROOT)}: 'id' must be an integer"
        )
        return 0
    for required_key in ("name", "slug", "subcategories"):
        if required_key not in cat_meta:
            errors.append(
                f"{cat_meta_path.relative_to(REPO_ROOT)}: missing '{required_key}'"
            )

    uc_count = 0
    for uc_file in sorted(category_dir.glob("UC-*.json")):
        _check_uc_file(uc_file, cat_id, validator, errors)
        uc_count += 1
    return uc_count


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _print_errors(errors: list[str], limit: int) -> None:
    if not errors:
        return
    for err in errors[:limit]:
        print(err)
    if len(errors) > limit:
        print(f"… plus {len(errors) - limit} more error(s); rerun with --max=0 to see all")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the per-UC content/ tree against schemas/uc.schema.json"
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Optional category dirs to limit validation to (default: all of content/)",
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Suppress per-file output, only exit code"
    )
    parser.add_argument(
        "--max",
        type=int,
        default=50,
        help="Max errors to print (0 = unlimited; default: 50)",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    schema = _load_schema()
    validator = _try_jsonschema_validator(schema) or _builtin_validator(schema)

    if args.paths:
        targets = [Path(p).resolve() for p in args.paths]
    else:
        if not CONTENT_DIR.exists():
            print(f"FATAL: {CONTENT_DIR} does not exist", file=sys.stderr)
            return 1
        targets = list(_iter_categories(CONTENT_DIR))

    errors: list[str] = []
    total_ucs = 0
    for cat_dir in targets:
        if not cat_dir.is_dir():
            errors.append(f"{cat_dir}: not a directory")
            continue
        uc_count = _check_category(cat_dir, validator, errors)
        total_ucs += uc_count
        if not args.quiet:
            label = "OK " if not errors else "   "
            print(f"  {label} {cat_dir.relative_to(REPO_ROOT)}/  {uc_count:>4} UCs")

    if errors:
        if not args.quiet:
            print("")
            print(f"FAILED: {len(errors)} error(s) across {total_ucs} UCs")
            limit = args.max if args.max > 0 else len(errors)
            _print_errors(errors, limit)
        else:
            print(f"FAILED: {len(errors)} error(s) across {total_ucs} UCs")
        return 1

    if not args.quiet:
        print("")
        print(f"PASS: {total_ucs} use cases validated against {UC_SCHEMA.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
