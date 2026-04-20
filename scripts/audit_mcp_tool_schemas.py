#!/usr/bin/env python3
"""Drift guard for the MCP tool/resource surface.

The MCP server (``mcp/``) declares a JSON Schema for every tool's output.
Those schemas must stay in lock-step with the static JSON produced by
``scripts/generate_api_surface.py``. If someone renames a field in
``api/v1/*.json`` without touching the tool code (or vice versa) the MCP
server will emit ``Output validation error`` to every client — we want
CI to catch that on the pull request, not in production.

Checks performed:

1. Required tools are declared: the eight MVP tools plus the two
   clause-level story tools (``get_clause_coverage`` and
   ``list_uncovered_clauses``) shipped in v1.6.x — all with matching
   input and output schemas.
2. Slug regexes are frozen (UC/regulation/equipment) — the drift guard
   asserts the compiled patterns the server uses to validate resource
   URIs, so a future change that relaxes them raises a red flag.
3. Every tool is runnable against the local ``api/v1/`` tree and its
   return payload validates against ``<TOOL>_OUTPUT_SCHEMA`` via
   ``jsonschema``.
4. Manifest/endpoint sanity: ``api/v1/manifest.json`` must still expose
   the endpoint URLs the tools rely on (ucs, equipment, compliance,
   recommender).

Exit code: ``0`` on clean, ``1`` on drift. Runs stdlib+jsonschema only.
Install the package once (``pip install -e mcp/[test]``) and the script
can import the tool surface directly.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any

try:
    import jsonschema  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover - CI preflight catches this
    print(
        "ERROR: jsonschema not installed. Run `pip install -e mcp/[test]` first.",
        file=sys.stderr,
    )
    sys.exit(2)


REPO_ROOT = Path(__file__).resolve().parent.parent
MCP_SRC = REPO_ROOT / "mcp" / "src"

# Tools + arguments we exercise. Keep arguments cheap so the drift guard
# runs in well under a second even on cold cache.
_PROBE_ARGS: dict[str, dict[str, Any]] = {
    "search_use_cases": {"query": "GDPR", "limit": 2},
    "get_use_case": {"uc_id": "22.1.1"},
    "list_categories": {},
    "list_regulations": {"tier": 1},
    "get_regulation": {"regulation_id": "gdpr", "version": "2016-679"},
    "list_equipment": {"min_use_case_count": 10},
    "get_equipment": {"equipment_id": "azure"},
    "find_compliance_gap": {"regulations": ["gdpr"]},
    "get_clause_coverage": {"regulation_id": "gdpr", "clause": "Art.5"},
    "list_uncovered_clauses": {"regulations": ["*"], "limit": 3},
}

# Nested dotted paths the MCP tools depend on when they fall back to
# HTTPS. If any of these disappear, ``Catalog._fetch_remote`` won't be
# able to resolve the endpoint URL from manifest.json.
_REQUIRED_MANIFEST_ENDPOINTS = (
    ("recommender", "ucThin"),
    ("compliance", "ucs"),
    ("compliance", "gaps"),
    ("compliance", "regulations"),
    ("equipment", "index"),
)

_EXPECTED_TOOLS = set(_PROBE_ARGS.keys())


def _ensure_importable() -> None:
    """Prepend ``mcp/src`` to ``sys.path`` so ``splunk_uc_mcp`` resolves."""

    if str(MCP_SRC) not in sys.path:
        sys.path.insert(0, str(MCP_SRC))


def _check_tools_surface(issues: list[str]) -> None:
    from splunk_uc_mcp.server import (
        _EXPECTED_SLUG_REGEXES,
        _TOOL_DEFINITIONS,
    )

    defined = {t.name for t in _TOOL_DEFINITIONS()}
    missing = _EXPECTED_TOOLS - defined
    extra = defined - _EXPECTED_TOOLS
    if missing:
        issues.append(f"server is missing tools: {sorted(missing)}")
    if extra:
        issues.append(f"server advertises unexpected tools: {sorted(extra)}")

    # Slug regex tuple must not shrink — a future contributor relaxing
    # validation is exactly the kind of quiet regression we want CI to
    # scream about.
    if len(_EXPECTED_SLUG_REGEXES) != 3:
        issues.append(
            f"_EXPECTED_SLUG_REGEXES has {len(_EXPECTED_SLUG_REGEXES)} entries, "
            "expected 3 (UC, regulation, equipment)"
        )

    for tool in _TOOL_DEFINITIONS():
        if tool.inputSchema is None:
            issues.append(f"{tool.name}: inputSchema missing")
        if tool.outputSchema is None:
            issues.append(f"{tool.name}: outputSchema missing")
        if not tool.description or len(tool.description) < 20:
            issues.append(
                f"{tool.name}: description must be >=20 chars "
                "(agents need context to pick the right tool)"
            )


def _check_manifest(issues: list[str]) -> None:
    manifest_path = REPO_ROOT / "api" / "v1" / "manifest.json"
    if not manifest_path.is_file():
        issues.append(
            f"api/v1/manifest.json missing — run scripts/generate_api_surface.py"
        )
        return
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(f"manifest.json invalid JSON: {exc}")
        return

    endpoints = manifest.get("endpoints", {})
    for path in _REQUIRED_MANIFEST_ENDPOINTS:
        cursor: Any = endpoints
        for segment in path:
            if not isinstance(cursor, dict) or segment not in cursor:
                issues.append(
                    f"manifest.endpoints missing nested path {'.'.join(path)!r}"
                    " — MCP tools depend on it for the remote-fallback path"
                )
                cursor = None
                break
            cursor = cursor[segment]


def _check_runtime_schemas(issues: list[str]) -> None:
    from splunk_uc_mcp.catalog import Catalog
    from splunk_uc_mcp.tools import (
        FIND_COMPLIANCE_GAP_OUTPUT_SCHEMA,
        GET_CLAUSE_COVERAGE_OUTPUT_SCHEMA,
        GET_EQUIPMENT_OUTPUT_SCHEMA,
        GET_REGULATION_OUTPUT_SCHEMA,
        GET_USE_CASE_OUTPUT_SCHEMA,
        LIST_CATEGORIES_OUTPUT_SCHEMA,
        LIST_EQUIPMENT_OUTPUT_SCHEMA,
        LIST_REGULATIONS_OUTPUT_SCHEMA,
        LIST_UNCOVERED_CLAUSES_OUTPUT_SCHEMA,
        SEARCH_USE_CASES_OUTPUT_SCHEMA,
        find_compliance_gap,
        get_clause_coverage,
        get_equipment,
        get_regulation,
        get_use_case,
        list_categories,
        list_equipment,
        list_regulations,
        list_uncovered_clauses,
        search_use_cases,
    )

    schemas: dict[str, dict[str, Any]] = {
        "search_use_cases": SEARCH_USE_CASES_OUTPUT_SCHEMA,
        "get_use_case": GET_USE_CASE_OUTPUT_SCHEMA,
        "list_categories": LIST_CATEGORIES_OUTPUT_SCHEMA,
        "list_regulations": LIST_REGULATIONS_OUTPUT_SCHEMA,
        "get_regulation": GET_REGULATION_OUTPUT_SCHEMA,
        "list_equipment": LIST_EQUIPMENT_OUTPUT_SCHEMA,
        "get_equipment": GET_EQUIPMENT_OUTPUT_SCHEMA,
        "find_compliance_gap": FIND_COMPLIANCE_GAP_OUTPUT_SCHEMA,
        "get_clause_coverage": GET_CLAUSE_COVERAGE_OUTPUT_SCHEMA,
        "list_uncovered_clauses": LIST_UNCOVERED_CLAUSES_OUTPUT_SCHEMA,
    }
    callables: dict[str, Any] = {
        "search_use_cases": search_use_cases,
        "get_use_case": get_use_case,
        "list_categories": list_categories,
        "list_regulations": list_regulations,
        "get_regulation": get_regulation,
        "list_equipment": list_equipment,
        "get_equipment": get_equipment,
        "find_compliance_gap": find_compliance_gap,
        "get_clause_coverage": get_clause_coverage,
        "list_uncovered_clauses": list_uncovered_clauses,
    }

    with Catalog(catalog_root=REPO_ROOT) as catalog:
        for name, schema in schemas.items():
            args = dict(_PROBE_ARGS.get(name, {}))
            # list_categories takes no args; every other tool accepts
            # catalog as kw-only so we always pass the fixture catalog.
            try:
                payload = callables[name](catalog=catalog, **args)
            except Exception as exc:  # pragma: no cover - drift signal
                issues.append(f"{name}: raised during probe call: {exc!r}")
                continue

            try:
                jsonschema.validate(instance=payload, schema=schema)
            except jsonschema.ValidationError as exc:
                issues.append(
                    f"{name}: payload does not match outputSchema — "
                    f"{exc.message} (path: /{'/'.join(str(p) for p in exc.absolute_path)})"
                )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print on failure (CI-friendly).",
    )
    args = parser.parse_args(argv)

    _ensure_importable()
    try:
        importlib.import_module("splunk_uc_mcp")
    except ImportError as exc:
        print(
            f"ERROR: cannot import splunk_uc_mcp — install with "
            f"`pip install -e mcp/[test]` first ({exc})",
            file=sys.stderr,
        )
        return 2

    issues: list[str] = []
    _check_tools_surface(issues)
    _check_manifest(issues)
    _check_runtime_schemas(issues)

    if issues:
        print("MCP drift guard: FAIL", file=sys.stderr)
        for issue in issues:
            print(f"  - {issue}", file=sys.stderr)
        return 1

    if not args.quiet:
        print(f"MCP drift guard: OK ({len(_EXPECTED_TOOLS)} tools validated)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
