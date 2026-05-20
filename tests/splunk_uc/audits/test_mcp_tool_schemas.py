"""Hermetic unit tests for ``splunk_uc.audits.mcp_tool_schemas``.

P16 wave UU (2026-05-19). The audit guards the contract between the MCP
server's tool declarations (``mcp/src/splunk_uc_mcp/``) and the catalog
JSON shape consumed by them. Real test coverage requires the audit to
exercise four things: importability of the MCP package, the eleven
expected tool surface declarations, the ``api/v1/manifest.json``
endpoint shape, and live validation of each tool's runtime payload
against its declared ``OUTPUT_SCHEMA``. We pin each one with a
controlled stub injected via ``sys.modules`` so the test suite never
spawns the real MCP server.

Tests pin every documented contract:

* Module-level constants (``REPO_ROOT`` walks three parents up;
  ``MCP_SRC`` targets ``mcp/src``; ``_PROBE_ARGS`` has the eleven
  documented tool names; ``_REQUIRED_MANIFEST_ENDPOINTS`` is the
  documented five-entry tuple; ``_EXPECTED_TOOLS`` is the set of
  _PROBE_ARGS keys).
* ``_ensure_importable`` matrix (prepends ``MCP_SRC`` to ``sys.path``
  on first call; idempotent on the second).
* ``_check_tools_surface`` matrix (clean state → no issues; missing
  tools → ``server is missing tools`` message; extra tools →
  ``advertises unexpected tools`` message; slug-regex tuple of the
  wrong length → ``_EXPECTED_SLUG_REGEXES has N entries`` message;
  missing inputSchema / outputSchema / short description all flagged).
* ``_check_manifest`` matrix (missing manifest file → flagged;
  invalid JSON → flagged with the parse error; missing nested
  endpoint paths → one entry per missing path, all five documented
  required endpoints; clean manifest → no issues).
* ``_check_runtime_schemas`` matrix (each callable's payload validated
  against its schema; a ValidationError surfaces with the path the
  failure landed on).
* ``main()`` exit-code matrix: 0 on clean, 1 on drift,
  2 when the MCP package can't be imported. ``--quiet`` suppresses
  the success message but still emits the FAIL header. ``--help``
  exits 0.
"""

from __future__ import annotations

import contextlib
import json
import pathlib
import re
import sys
import types
from typing import Any, NamedTuple

import jsonschema
import pytest

import splunk_uc.audits.mcp_tool_schemas as mts


# ----------------------------------------------------------- module constants --
def test_repo_root_walks_three_parents_up() -> None:
    here = pathlib.Path(mts.__file__).resolve()
    assert mts.REPO_ROOT == here.parents[3]


def test_mcp_src_constant() -> None:
    assert mts.MCP_SRC == mts.REPO_ROOT / "mcp" / "src"


def test_probe_args_has_eleven_tools() -> None:
    """The documented MVP + clause + markdown tool set."""
    assert set(mts._PROBE_ARGS.keys()) == {
        "search_use_cases",
        "get_use_case",
        "get_use_case_markdown",
        "list_categories",
        "list_regulations",
        "get_regulation",
        "list_equipment",
        "get_equipment",
        "find_compliance_gap",
        "get_clause_coverage",
        "list_uncovered_clauses",
    }


def test_required_manifest_endpoints_tuple() -> None:
    """The five documented nested endpoint paths."""
    assert mts._REQUIRED_MANIFEST_ENDPOINTS == (
        ("recommender", "ucThin"),
        ("compliance", "ucs"),
        ("compliance", "gaps"),
        ("compliance", "regulations"),
        ("equipment", "index"),
    )


def test_expected_tools_is_keys_of_probe_args() -> None:
    assert mts._EXPECTED_TOOLS == set(mts._PROBE_ARGS.keys())


# ----------------------------------------------------------- _ensure_importable
def test_ensure_importable_prepends_mcp_src(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If MCP_SRC isn't on sys.path, it gets inserted at index 0."""
    monkeypatch.setattr(sys, "path", ["/nothing"])
    mts._ensure_importable()
    assert sys.path[0] == str(mts.MCP_SRC)


def test_ensure_importable_idempotent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A second call should not re-insert the path."""
    monkeypatch.setattr(sys, "path", [str(mts.MCP_SRC), "/x"])
    mts._ensure_importable()
    # No duplicate at position 0.
    assert sys.path[0] == str(mts.MCP_SRC)
    assert sys.path.count(str(mts.MCP_SRC)) == 1


# ------------------------------------------ stub tool / server module helper --
class _StubTool(NamedTuple):
    name: str
    description: str
    inputSchema: dict[str, Any] | None
    outputSchema: dict[str, Any] | None


def _install_server_stub(
    monkeypatch: pytest.MonkeyPatch,
    *,
    tools: list[_StubTool] | None = None,
    regexes: tuple[re.Pattern[str], ...] | None = None,
) -> None:
    """Install a fake ``splunk_uc_mcp.server`` module in sys.modules."""
    if tools is None:
        tools = []
        for name in mts._EXPECTED_TOOLS:
            tools.append(
                _StubTool(
                    name=name,
                    description="A description that is long enough.",
                    inputSchema={"type": "object"},
                    outputSchema={"type": "object"},
                )
            )
    if regexes is None:
        regexes = (
            re.compile(r"\d+\.\d+\.\d+"),
            re.compile(r"[a-z0-9_-]+"),
            re.compile(r"[a-z0-9_-]+"),
        )

    fake = types.ModuleType("splunk_uc_mcp.server")
    fake._EXPECTED_SLUG_REGEXES = regexes  # type: ignore[attr-defined]
    fake._TOOL_DEFINITIONS = lambda: tools  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "splunk_uc_mcp.server", fake)


# ----------------------------------------------------- _check_tools_surface ---
def test_check_tools_surface_clean(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_server_stub(monkeypatch)
    issues: list[str] = []
    mts._check_tools_surface(issues)
    assert issues == []


def test_check_tools_surface_missing_tool(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Drop one of the expected tools → ``missing tools`` issue."""
    tools = [
        _StubTool(
            name=n,
            description="A description that is long enough.",
            inputSchema={"type": "object"},
            outputSchema={"type": "object"},
        )
        for n in mts._EXPECTED_TOOLS - {"search_use_cases"}
    ]
    _install_server_stub(monkeypatch, tools=tools)
    issues: list[str] = []
    mts._check_tools_surface(issues)
    assert any("missing tools" in i and "search_use_cases" in i for i in issues)


def test_check_tools_surface_extra_tool(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Adding a tool not in _EXPECTED_TOOLS → ``unexpected tools`` issue."""
    tools = [
        _StubTool(
            name=n,
            description="A description that is long enough.",
            inputSchema={"type": "object"},
            outputSchema={"type": "object"},
        )
        for n in mts._EXPECTED_TOOLS
    ]
    tools.append(
        _StubTool(
            name="speculative_future_tool",
            description="A description that is long enough.",
            inputSchema={"type": "object"},
            outputSchema={"type": "object"},
        )
    )
    _install_server_stub(monkeypatch, tools=tools)
    issues: list[str] = []
    mts._check_tools_surface(issues)
    assert any(
        "advertises unexpected tools" in i and "speculative_future_tool" in i for i in issues
    )


def test_check_tools_surface_slug_regex_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A regex tuple of length != 3 surfaces with the actual length."""
    _install_server_stub(
        monkeypatch,
        regexes=(re.compile("x"),),  # only one entry
    )
    issues: list[str] = []
    mts._check_tools_surface(issues)
    assert any("_EXPECTED_SLUG_REGEXES has 1 entries" in i for i in issues)


def test_check_tools_surface_missing_input_schema(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tools = [
        _StubTool(
            name="search_use_cases",
            description="A description that is long enough.",
            inputSchema=None,
            outputSchema={"type": "object"},
        )
    ] + [
        _StubTool(
            name=n,
            description="A description that is long enough.",
            inputSchema={"type": "object"},
            outputSchema={"type": "object"},
        )
        for n in mts._EXPECTED_TOOLS - {"search_use_cases"}
    ]
    _install_server_stub(monkeypatch, tools=tools)
    issues: list[str] = []
    mts._check_tools_surface(issues)
    assert any(i == "search_use_cases: inputSchema missing" for i in issues)


def test_check_tools_surface_missing_output_schema(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tools = [
        _StubTool(
            name="get_use_case",
            description="A description that is long enough.",
            inputSchema={"type": "object"},
            outputSchema=None,
        )
    ] + [
        _StubTool(
            name=n,
            description="A description that is long enough.",
            inputSchema={"type": "object"},
            outputSchema={"type": "object"},
        )
        for n in mts._EXPECTED_TOOLS - {"get_use_case"}
    ]
    _install_server_stub(monkeypatch, tools=tools)
    issues: list[str] = []
    mts._check_tools_surface(issues)
    assert any(i == "get_use_case: outputSchema missing" for i in issues)


def test_check_tools_surface_short_description(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Description shorter than 20 chars → surfaces as issue."""
    tools = [
        _StubTool(
            name="list_categories",
            description="too short",
            inputSchema={"type": "object"},
            outputSchema={"type": "object"},
        )
    ] + [
        _StubTool(
            name=n,
            description="A description that is long enough.",
            inputSchema={"type": "object"},
            outputSchema={"type": "object"},
        )
        for n in mts._EXPECTED_TOOLS - {"list_categories"}
    ]
    _install_server_stub(monkeypatch, tools=tools)
    issues: list[str] = []
    mts._check_tools_surface(issues)
    assert any("list_categories: description must be >=20 chars" in i for i in issues)


def test_check_tools_surface_empty_description(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Empty description (`not tool.description`) → surfaces as issue."""
    tools = [
        _StubTool(
            name="get_equipment",
            description="",
            inputSchema={"type": "object"},
            outputSchema={"type": "object"},
        )
    ] + [
        _StubTool(
            name=n,
            description="A description that is long enough.",
            inputSchema={"type": "object"},
            outputSchema={"type": "object"},
        )
        for n in mts._EXPECTED_TOOLS - {"get_equipment"}
    ]
    _install_server_stub(monkeypatch, tools=tools)
    issues: list[str] = []
    mts._check_tools_surface(issues)
    assert any("get_equipment: description must be >=20 chars" in i for i in issues)


# --------------------------------------------------------- _check_manifest ---
def _build_clean_manifest() -> dict[str, Any]:
    return {
        "endpoints": {
            "recommender": {"ucThin": "/api/v1/recommender/uc-thin.json"},
            "compliance": {
                "ucs": "/api/v1/compliance/ucs/",
                "gaps": "/api/v1/compliance/gaps/",
                "regulations": "/api/v1/compliance/regulations/",
            },
            "equipment": {"index": "/api/v1/equipment/index.json"},
        }
    }


@pytest.fixture
def fake_manifest_root(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """Provide a fake ``REPO_ROOT`` with ``api/v1/manifest.json`` ancestor."""
    monkeypatch.setattr(mts, "REPO_ROOT", tmp_path)
    (tmp_path / "api" / "v1").mkdir(parents=True)
    return tmp_path


def test_check_manifest_missing_file(
    fake_manifest_root: pathlib.Path,
) -> None:
    issues: list[str] = []
    mts._check_manifest(issues)
    assert any("api/v1/manifest.json missing" in i for i in issues)


def test_check_manifest_invalid_json(
    fake_manifest_root: pathlib.Path,
) -> None:
    (fake_manifest_root / "api" / "v1" / "manifest.json").write_text("not-json", encoding="utf-8")
    issues: list[str] = []
    mts._check_manifest(issues)
    assert any("manifest.json invalid JSON" in i for i in issues)


def test_check_manifest_clean(fake_manifest_root: pathlib.Path) -> None:
    (fake_manifest_root / "api" / "v1" / "manifest.json").write_text(
        json.dumps(_build_clean_manifest()), encoding="utf-8"
    )
    issues: list[str] = []
    mts._check_manifest(issues)
    assert issues == []


def test_check_manifest_missing_nested_endpoint(
    fake_manifest_root: pathlib.Path,
) -> None:
    """Strip one nested endpoint → one issue surfaces."""
    payload = _build_clean_manifest()
    del payload["endpoints"]["compliance"]["gaps"]
    (fake_manifest_root / "api" / "v1" / "manifest.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    issues: list[str] = []
    mts._check_manifest(issues)
    assert any("manifest.endpoints missing nested path 'compliance.gaps'" in i for i in issues)


def test_check_manifest_endpoints_block_missing(
    fake_manifest_root: pathlib.Path,
) -> None:
    """Missing ``endpoints`` block → every required path surfaces."""
    (fake_manifest_root / "api" / "v1" / "manifest.json").write_text(
        json.dumps({"version": "v1"}), encoding="utf-8"
    )
    issues: list[str] = []
    mts._check_manifest(issues)
    assert len(issues) == len(mts._REQUIRED_MANIFEST_ENDPOINTS)


def test_check_manifest_endpoint_path_intermediate_not_dict(
    fake_manifest_root: pathlib.Path,
) -> None:
    """``endpoints.compliance`` not a dict → all compliance paths surface."""
    payload = {
        "endpoints": {
            "compliance": "https://example/",
            "recommender": {"ucThin": "x"},
            "equipment": {"index": "x"},
        }
    }
    (fake_manifest_root / "api" / "v1" / "manifest.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    issues: list[str] = []
    mts._check_manifest(issues)
    # All three compliance.* paths surface
    assert sum("compliance" in i for i in issues) == 3


# ------------------------------------------------- _check_runtime_schemas ----
def _install_catalog_and_tools_stubs(
    monkeypatch: pytest.MonkeyPatch,
    *,
    payloads: dict[str, Any] | None = None,
) -> None:
    """Install fake ``splunk_uc_mcp.catalog`` and ``splunk_uc_mcp.tools``
    modules plus the ``tools.use_case`` submodule used by the audit.
    """

    @contextlib.contextmanager
    def _fake_catalog(*, catalog_root: pathlib.Path) -> Any:
        assert catalog_root == mts.REPO_ROOT
        yield types.SimpleNamespace(name="fake-catalog")

    class _Catalog:
        def __init__(self, *, catalog_root: pathlib.Path) -> None:
            assert catalog_root == mts.REPO_ROOT
            self.root = catalog_root

        def __enter__(self) -> _Catalog:
            return self

        def __exit__(self, *_a: Any) -> None:
            return None

    catalog_mod = types.ModuleType("splunk_uc_mcp.catalog")
    catalog_mod.Catalog = _Catalog  # type: ignore[attr-defined]

    permissive_schema: dict[str, Any] = {"type": "object"}

    # Build a tools module with 11 schemas + 11 callables. Each callable
    # accepts ``catalog`` kwarg + any other args and returns the documented
    # payload dict.
    tools_mod = types.ModuleType("splunk_uc_mcp.tools")
    use_case_mod = types.ModuleType("splunk_uc_mcp.tools.use_case")

    schemas = {
        "search_use_cases": "SEARCH_USE_CASES_OUTPUT_SCHEMA",
        "get_use_case": "GET_USE_CASE_OUTPUT_SCHEMA",
        "list_categories": "LIST_CATEGORIES_OUTPUT_SCHEMA",
        "list_regulations": "LIST_REGULATIONS_OUTPUT_SCHEMA",
        "get_regulation": "GET_REGULATION_OUTPUT_SCHEMA",
        "list_equipment": "LIST_EQUIPMENT_OUTPUT_SCHEMA",
        "get_equipment": "GET_EQUIPMENT_OUTPUT_SCHEMA",
        "find_compliance_gap": "FIND_COMPLIANCE_GAP_OUTPUT_SCHEMA",
        "get_clause_coverage": "GET_CLAUSE_COVERAGE_OUTPUT_SCHEMA",
        "list_uncovered_clauses": "LIST_UNCOVERED_CLAUSES_OUTPUT_SCHEMA",
    }
    for attr in schemas.values():
        setattr(tools_mod, attr, permissive_schema)

    # use_case submodule carries the markdown schema.
    use_case_mod.GET_USE_CASE_MARKDOWN_OUTPUT_SCHEMA = permissive_schema  # type: ignore[attr-defined]

    # 11 callables; honour the ``payloads`` override per-tool.
    payloads_dict = payloads or {}

    def _make(name: str) -> Any:
        def fn(*, catalog: Any, **_kw: Any) -> Any:
            assert catalog is not None
            return payloads_dict.get(name, {"ok": True})

        return fn

    tools_mod.search_use_cases = _make("search_use_cases")  # type: ignore[attr-defined]
    tools_mod.get_use_case = _make("get_use_case")  # type: ignore[attr-defined]
    tools_mod.get_use_case_markdown = _make("get_use_case_markdown")  # type: ignore[attr-defined]
    tools_mod.list_categories = _make("list_categories")  # type: ignore[attr-defined]
    tools_mod.list_regulations = _make("list_regulations")  # type: ignore[attr-defined]
    tools_mod.get_regulation = _make("get_regulation")  # type: ignore[attr-defined]
    tools_mod.list_equipment = _make("list_equipment")  # type: ignore[attr-defined]
    tools_mod.get_equipment = _make("get_equipment")  # type: ignore[attr-defined]
    tools_mod.find_compliance_gap = _make("find_compliance_gap")  # type: ignore[attr-defined]
    tools_mod.get_clause_coverage = _make("get_clause_coverage")  # type: ignore[attr-defined]
    tools_mod.list_uncovered_clauses = _make("list_uncovered_clauses")  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "splunk_uc_mcp.catalog", catalog_mod)
    monkeypatch.setitem(sys.modules, "splunk_uc_mcp.tools", tools_mod)
    monkeypatch.setitem(sys.modules, "splunk_uc_mcp.tools.use_case", use_case_mod)

    # Silence unused-symbol warnings.
    _ = _fake_catalog


def test_check_runtime_schemas_clean(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_catalog_and_tools_stubs(monkeypatch)
    issues: list[str] = []
    mts._check_runtime_schemas(issues)
    assert issues == []


def test_check_runtime_schemas_validation_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If jsonschema.validate raises, the issue carries the path."""
    _install_catalog_and_tools_stubs(monkeypatch)

    def fake_validate(*, instance: Any, schema: Any) -> None:
        if instance == {"ok": True}:
            err = jsonschema.ValidationError("boom")
            # absolute_path is a deque on the real exception.
            err.absolute_path.extend(["foo", 1, "bar"])
            raise err

    monkeypatch.setattr(mts.jsonschema, "validate", fake_validate)
    issues: list[str] = []
    mts._check_runtime_schemas(issues)
    # All 11 tools failed validation.
    assert len(issues) == 11
    assert all("payload does not match outputSchema" in i for i in issues)
    assert any("path: /foo/1/bar" in i for i in issues)


# -------------------------------------------------------------- main() ------
def _patch_main_dependencies(
    monkeypatch: pytest.MonkeyPatch,
    *,
    importable: bool = True,
    surface_issues: list[str] | None = None,
    manifest_issues: list[str] | None = None,
    runtime_issues: list[str] | None = None,
) -> None:
    """Stub everything ``main`` calls so we can isolate exit-code logic."""

    def fake_ensure_importable() -> None:
        return None

    monkeypatch.setattr(mts, "_ensure_importable", fake_ensure_importable)

    if importable:
        fake_pkg = types.ModuleType("splunk_uc_mcp")
        monkeypatch.setitem(sys.modules, "splunk_uc_mcp", fake_pkg)

        def fake_import(name: str) -> Any:
            if name == "splunk_uc_mcp":
                return fake_pkg
            raise ImportError(name)

        monkeypatch.setattr(mts.importlib, "import_module", fake_import)
    else:

        def boom(name: str) -> Any:
            raise ImportError(f"no module named {name}")

        monkeypatch.setattr(mts.importlib, "import_module", boom)

    def fake_tools_surface(issues: list[str]) -> None:
        if surface_issues:
            issues.extend(surface_issues)

    def fake_manifest(issues: list[str]) -> None:
        if manifest_issues:
            issues.extend(manifest_issues)

    def fake_runtime(issues: list[str]) -> None:
        if runtime_issues:
            issues.extend(runtime_issues)

    monkeypatch.setattr(mts, "_check_tools_surface", fake_tools_surface)
    monkeypatch.setattr(mts, "_check_manifest", fake_manifest)
    monkeypatch.setattr(mts, "_check_runtime_schemas", fake_runtime)


def test_main_clean(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _patch_main_dependencies(monkeypatch)
    assert mts.main([]) == 0
    out = capsys.readouterr().out
    assert "MCP drift guard: OK" in out
    assert "11 tools validated" in out


def test_main_quiet_suppresses_success(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _patch_main_dependencies(monkeypatch)
    assert mts.main(["--quiet"]) == 0
    cap = capsys.readouterr()
    assert cap.out == ""


def test_main_with_drift_returns_one(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _patch_main_dependencies(monkeypatch, surface_issues=["search_use_cases: bad"])
    assert mts.main([]) == 1
    err = capsys.readouterr().err
    assert "MCP drift guard: FAIL" in err
    assert "  - search_use_cases: bad" in err


def test_main_drift_quiet_still_prints_fail(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """``--quiet`` only suppresses the success line, not failures."""
    _patch_main_dependencies(monkeypatch, manifest_issues=["manifest is gone"])
    assert mts.main(["--quiet"]) == 1
    cap = capsys.readouterr()
    assert "MCP drift guard: FAIL" in cap.err
    assert "manifest is gone" in cap.err


def test_main_import_failure_returns_two(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _patch_main_dependencies(monkeypatch, importable=False)
    assert mts.main([]) == 2
    err = capsys.readouterr().err
    assert "cannot import splunk_uc_mcp" in err


def test_main_argv_none_falls_through(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_main_dependencies(monkeypatch)
    monkeypatch.setattr(mts.sys, "argv", ["audit"])
    assert mts.main() == 0


def test_main_help(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc:
        mts.main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "--quiet" in out


def test_main_aggregates_all_issue_sources(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _patch_main_dependencies(
        monkeypatch,
        surface_issues=["surface-1"],
        manifest_issues=["manifest-1"],
        runtime_issues=["runtime-1"],
    )
    assert mts.main([]) == 1
    err = capsys.readouterr().err
    assert "- surface-1" in err
    assert "- manifest-1" in err
    assert "- runtime-1" in err


# --------------------------------------- dispatcher entry-point smoke -------
def test_module_dunder_main_exists() -> None:
    src = pathlib.Path(mts.__file__).read_text()
    assert 'if __name__ == "__main__":' in src
    assert "sys.exit(main())" in src
