"""Comprehensive unit tests for ``src/splunk_uc/audits/openapi_drift.py``.

Pins every documented contract of the ``audit-openapi-drift`` drift check:

- module-level constants (``PROJECT_ROOT`` is a resolved absolute path);
- ``load_yaml_paths`` — regex matches 2-space indented top-level path keys,
  missing file returns empty set, more deeply nested keys (4+ space indent)
  are not collected, lines without trailing colon are not matched;
- ``collect_dist_paths`` — walks ``dist/api/`` for JSON/YAML/JSONLD files,
  returns paths relative to the parent directory with a leading ``/``, skips
  unsupported extensions, missing directory returns empty set;
- ``main()`` — happy path (all paths documented), missing ``dist/api/``
  skips with exit 0, undocumented paths surface on stderr with exit 1,
  ``{param}`` template expansion via regex match, output truncation at 20
  undocumented paths, ``argv`` is intentionally ignored via ``del argv``.
"""

from __future__ import annotations

import pathlib
from typing import Protocol

import pytest

from splunk_uc.audits import openapi_drift as od


class WriteSpec(Protocol):
    def __call__(self, rel: str, body: str) -> pathlib.Path: ...


class WriteDistApi(Protocol):
    def __call__(self, rel: str, body: str = ...) -> pathlib.Path: ...


@pytest.fixture
def fake_repo(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """Build a hermetic project root + monkey-patch ``PROJECT_ROOT``."""
    monkeypatch.setattr(od, "PROJECT_ROOT", tmp_path)
    return tmp_path


@pytest.fixture
def write_spec(fake_repo: pathlib.Path) -> WriteSpec:
    """Factory that materialises an OpenAPI YAML file."""

    def _make(rel: str, body: str) -> pathlib.Path:
        p = fake_repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
        return p

    return _make


@pytest.fixture
def write_dist_api(fake_repo: pathlib.Path) -> WriteDistApi:
    """Factory that materialises a ``dist/api/`` file."""

    def _make(rel: str, body: str = "{}") -> pathlib.Path:
        p = fake_repo / "dist" / "api" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
        return p

    return _make


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------


def test_project_root_resolves_to_absolute_path() -> None:
    """`PROJECT_ROOT` is a `Path` resolved at import time."""
    assert isinstance(od.PROJECT_ROOT, pathlib.Path)
    assert od.PROJECT_ROOT.is_absolute()


# ---------------------------------------------------------------------------
# load_yaml_paths
# ---------------------------------------------------------------------------


def test_load_yaml_paths_missing_file_returns_empty(
    fake_repo: pathlib.Path,
) -> None:
    """Non-existent YAML returns empty set (does not raise)."""
    assert od.load_yaml_paths(fake_repo / "nope.yaml") == set()


def test_load_yaml_paths_extracts_top_level_paths(
    write_spec: WriteSpec,
) -> None:
    """Two-space-indented `/path:` lines are extracted."""
    spec = write_spec(
        "openapi.yaml",
        """\
openapi: 3.0.0
paths:
  /api/v1/foo:
    get:
      summary: Foo
  /api/v1/bar:
    get:
      summary: Bar
""",
    )
    assert od.load_yaml_paths(spec) == {"/api/v1/foo", "/api/v1/bar"}


def test_load_yaml_paths_ignores_four_space_nested_keys(
    write_spec: WriteSpec,
) -> None:
    """Keys indented with 4+ spaces are not collected (only 2-space level)."""
    spec = write_spec(
        "openapi.yaml",
        """\
paths:
  /api/v1/foo:
    get:
      parameters:
        - name: id
          in: query
""",
    )
    assert od.load_yaml_paths(spec) == {"/api/v1/foo"}


def test_load_yaml_paths_requires_trailing_colon(
    write_spec: WriteSpec,
) -> None:
    """Lines without a trailing colon are not matched."""
    spec = write_spec(
        "openapi.yaml",
        """\
paths:
  /api/v1/foo
  /api/v1/bar:
""",
    )
    assert od.load_yaml_paths(spec) == {"/api/v1/bar"}


def test_load_yaml_paths_path_must_start_with_slash(
    write_spec: WriteSpec,
) -> None:
    """The path value must start with `/` (the leading `/` is required)."""
    spec = write_spec(
        "openapi.yaml",
        """\
paths:
  noleadingslash:
    get:
      summary: foo
  /api/v1/ok:
    get:
      summary: ok
""",
    )
    assert od.load_yaml_paths(spec) == {"/api/v1/ok"}


def test_load_yaml_paths_no_whitespace_or_colon_inside_path(
    write_spec: WriteSpec,
) -> None:
    """The `[^\\s:]+` quantifier excludes paths with embedded space/colon."""
    spec = write_spec(
        "openapi.yaml",
        """\
paths:
  /api/v1/with space:
    get: foo
  /api/v1/clean:
    get: bar
""",
    )
    result = od.load_yaml_paths(spec)
    assert "/api/v1/clean" in result
    assert "/api/v1/with space" not in result


def test_load_yaml_paths_empty_file_returns_empty(
    write_spec: WriteSpec,
) -> None:
    """Empty YAML returns empty set."""
    spec = write_spec("openapi.yaml", "")
    assert od.load_yaml_paths(spec) == set()


def test_load_yaml_paths_with_template_params(
    write_spec: WriteSpec,
) -> None:
    """Paths with `{param}` placeholders are captured verbatim."""
    spec = write_spec(
        "openapi.yaml",
        """\
paths:
  /api/v1/uc/{ucId}:
    get: foo
""",
    )
    assert od.load_yaml_paths(spec) == {"/api/v1/uc/{ucId}"}


# ---------------------------------------------------------------------------
# collect_dist_paths
# ---------------------------------------------------------------------------


def test_collect_dist_paths_missing_dir_returns_empty(
    fake_repo: pathlib.Path,
) -> None:
    """Missing dist/api directory returns empty set."""
    assert od.collect_dist_paths(fake_repo / "nope") == set()


def test_collect_dist_paths_collects_supported_extensions(
    fake_repo: pathlib.Path, write_dist_api: WriteDistApi
) -> None:
    """`.json`, `.yaml`, `.jsonld` are all collected.

    The path format is `/<rel-to-grandparent>` so for ``dist/api/v1/foo.json``
    we get ``/dist/api/v1/foo.json`` (the ``relative_to(dist_api.parent.parent)``
    call walks up two levels from the api directory).
    """
    write_dist_api("v1/uc.json")
    write_dist_api("v1/manifest.yaml", "name: foo\n")
    write_dist_api("v1/oscal.jsonld", '{"@context": {}}')
    paths = od.collect_dist_paths(fake_repo / "dist" / "api")
    assert paths == {
        "/dist/api/v1/uc.json",
        "/dist/api/v1/manifest.yaml",
        "/dist/api/v1/oscal.jsonld",
    }


def test_collect_dist_paths_ignores_unsupported_extensions(
    fake_repo: pathlib.Path, write_dist_api: WriteDistApi
) -> None:
    """`.txt`, `.html`, `.csv` etc. are NOT collected."""
    write_dist_api("v1/uc.json")
    write_dist_api("v1/readme.txt", "noise")
    write_dist_api("v1/page.html", "<html/>")
    write_dist_api("v1/data.csv", "a,b\n")
    paths = od.collect_dist_paths(fake_repo / "dist" / "api")
    assert paths == {"/dist/api/v1/uc.json"}


def test_collect_dist_paths_ignores_directories(
    fake_repo: pathlib.Path, write_dist_api: WriteDistApi
) -> None:
    """Directories are skipped by the `is_file()` guard."""
    (fake_repo / "dist" / "api" / "subdir").mkdir(parents=True)
    write_dist_api("v1/uc.json")
    paths = od.collect_dist_paths(fake_repo / "dist" / "api")
    assert paths == {"/dist/api/v1/uc.json"}


def test_collect_dist_paths_recursive_walk(
    fake_repo: pathlib.Path, write_dist_api: WriteDistApi
) -> None:
    """`rglob('*')` walks nested directories."""
    write_dist_api("v1/uc/UC-1.1.1/index.json")
    write_dist_api("v1/uc/UC-1.1.2/index.json")
    write_dist_api("v1/manifest.json")
    paths = od.collect_dist_paths(fake_repo / "dist" / "api")
    assert paths == {
        "/dist/api/v1/uc/UC-1.1.1/index.json",
        "/dist/api/v1/uc/UC-1.1.2/index.json",
        "/dist/api/v1/manifest.json",
    }


def test_collect_dist_paths_includes_leading_slash(
    fake_repo: pathlib.Path, write_dist_api: WriteDistApi
) -> None:
    """All collected paths have a leading `/` prefix."""
    write_dist_api("v1/manifest.json")
    paths = od.collect_dist_paths(fake_repo / "dist" / "api")
    assert all(p.startswith("/") for p in paths)


def test_collect_dist_paths_empty_dir_returns_empty(
    fake_repo: pathlib.Path,
) -> None:
    """Existing-but-empty dist/api returns empty set."""
    (fake_repo / "dist" / "api").mkdir(parents=True)
    assert od.collect_dist_paths(fake_repo / "dist" / "api") == set()


# ---------------------------------------------------------------------------
# main() — missing dist short-circuit
# ---------------------------------------------------------------------------


def test_main_missing_dist_api_skips_with_exit_zero(
    fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Missing `dist/api/` produces a skip message and exits 0."""
    assert od.main([]) == 0
    captured = capsys.readouterr()
    assert "dist/api/ not found" in captured.out
    assert "run 'make build' first" in captured.out


def test_main_argv_is_intentionally_ignored(
    fake_repo: pathlib.Path,
    write_dist_api: WriteDistApi,
    write_spec: WriteSpec,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`del argv` means any argv value is accepted without parsing."""
    write_spec("openapi.yaml", "paths:\n  /dist/api/v1/x.json:\n")
    write_dist_api("v1/x.json")
    assert od.main(["--unknown", "--foo", "bar"]) == 0


def test_main_argv_none_passes_through(
    fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`argv=None` is accepted (also discarded via `del argv`)."""
    assert od.main(None) == 0


# ---------------------------------------------------------------------------
# main() — happy paths
# ---------------------------------------------------------------------------


def test_main_all_paths_documented_returns_zero(
    fake_repo: pathlib.Path,
    write_spec: WriteSpec,
    write_dist_api: WriteDistApi,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """All actual paths documented → exit 0 + summary message."""
    write_spec(
        "openapi.yaml",
        """\
paths:
  /dist/api/v1/uc.json:
    get: foo
  /dist/api/v1/manifest.json:
    get: bar
""",
    )
    write_dist_api("v1/uc.json")
    write_dist_api("v1/manifest.json")
    assert od.main([]) == 0
    captured = capsys.readouterr()
    assert "all 2 API paths documented" in captured.out
    assert captured.err == ""


def test_main_root_spec_and_v1_spec_unioned(
    fake_repo: pathlib.Path,
    write_spec: WriteSpec,
    write_dist_api: WriteDistApi,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The root `openapi.yaml` and `api/v1/openapi.yaml` are both loaded."""
    write_spec(
        "openapi.yaml",
        "paths:\n  /dist/api/v1/uc.json:\n    get: x\n",
    )
    write_spec(
        "api/v1/openapi.yaml",
        "paths:\n  /dist/api/v1/manifest.json:\n    get: y\n",
    )
    write_dist_api("v1/uc.json")
    write_dist_api("v1/manifest.json")
    assert od.main([]) == 0
    assert "all 2 API paths documented" in capsys.readouterr().out


def test_main_empty_dist_api_returns_zero(
    fake_repo: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Empty-but-existing dist/api → exit 0 with `all 0 API paths`."""
    (fake_repo / "dist" / "api").mkdir(parents=True)
    assert od.main([]) == 0
    captured = capsys.readouterr()
    assert "all 0 API paths documented" in captured.out


# ---------------------------------------------------------------------------
# main() — undocumented paths
# ---------------------------------------------------------------------------


def test_main_undocumented_path_surfaces_on_stderr(
    fake_repo: pathlib.Path,
    write_spec: WriteSpec,
    write_dist_api: WriteDistApi,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An undocumented path → stderr + exit 1."""
    write_spec(
        "openapi.yaml",
        "paths:\n  /dist/api/v1/known.json:\n    get: x\n",
    )
    write_dist_api("v1/known.json")
    write_dist_api("v1/unknown.json")
    assert od.main([]) == 1
    captured = capsys.readouterr()
    assert "OpenAPI drift: 1 undocumented path(s)" in captured.err
    assert "/dist/api/v1/unknown.json" in captured.err


def test_main_undocumented_path_truncated_at_twenty(
    fake_repo: pathlib.Path,
    write_dist_api: WriteDistApi,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Stderr lists at most the first 20 undocumented paths."""
    for i in range(25):
        write_dist_api(f"v1/file_{i:02d}.json")
    assert od.main([]) == 1
    captured = capsys.readouterr()
    assert "OpenAPI drift: 25 undocumented path(s)" in captured.err
    listed = [line for line in captured.err.splitlines() if line.startswith("  /dist/api/v1/file_")]
    assert len(listed) == 20


def test_main_undocumented_paths_sorted(
    fake_repo: pathlib.Path,
    write_dist_api: WriteDistApi,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Undocumented paths are surfaced in sorted order."""
    write_dist_api("v1/zzz.json")
    write_dist_api("v1/aaa.json")
    write_dist_api("v1/mmm.json")
    assert od.main([]) == 1
    captured = capsys.readouterr()
    pos_a = captured.err.index("/dist/api/v1/aaa.json")
    pos_m = captured.err.index("/dist/api/v1/mmm.json")
    pos_z = captured.err.index("/dist/api/v1/zzz.json")
    assert pos_a < pos_m < pos_z


# ---------------------------------------------------------------------------
# main() — template parameter matching
# ---------------------------------------------------------------------------


def test_main_template_param_matches_concrete_path(
    fake_repo: pathlib.Path,
    write_spec: WriteSpec,
    write_dist_api: WriteDistApi,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`/dist/api/v1/uc/{ucId}/index.json` matches `/dist/api/v1/uc/UC-1.1.1/index.json`."""
    write_spec(
        "openapi.yaml",
        "paths:\n  /dist/api/v1/uc/{ucId}/index.json:\n    get: x\n",
    )
    write_dist_api("v1/uc/UC-1.1.1/index.json")
    write_dist_api("v1/uc/UC-1.1.2/index.json")
    assert od.main([]) == 0
    assert "all 2 API paths documented" in capsys.readouterr().out


def test_main_template_param_does_not_match_across_slashes(
    fake_repo: pathlib.Path,
    write_spec: WriteSpec,
    write_dist_api: WriteDistApi,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`{ucId}` is `[^/]+` so it doesn't cross a slash boundary."""
    write_spec(
        "openapi.yaml",
        "paths:\n  /dist/api/v1/uc/{ucId}.json:\n    get: x\n",
    )
    write_dist_api("v1/uc/UC-1.1.1/extra.json")
    assert od.main([]) == 1
    err = capsys.readouterr().err
    assert "/dist/api/v1/uc/UC-1.1.1/extra.json" in err


def test_main_exact_match_takes_priority_via_short_circuit(
    fake_repo: pathlib.Path,
    write_spec: WriteSpec,
    write_dist_api: WriteDistApi,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Exact match (no `{` substitution needed) is matched via the `==` arm."""
    write_spec(
        "openapi.yaml",
        "paths:\n  /dist/api/v1/manifest.json:\n    get: x\n",
    )
    write_dist_api("v1/manifest.json")
    assert od.main([]) == 0
    assert "all 1 API paths documented" in capsys.readouterr().out


def test_main_mixed_documented_and_undocumented(
    fake_repo: pathlib.Path,
    write_spec: WriteSpec,
    write_dist_api: WriteDistApi,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Some paths documented (template match) + some undocumented → exit 1."""
    write_spec(
        "openapi.yaml",
        """\
paths:
  /dist/api/v1/uc/{ucId}/index.json:
    get: x
""",
    )
    write_dist_api("v1/uc/UC-1.1.1/index.json")
    write_dist_api("v1/orphan.json")
    assert od.main([]) == 1
    err = capsys.readouterr().err
    assert "OpenAPI drift: 1 undocumented path(s)" in err
    assert "/dist/api/v1/orphan.json" in err
    assert "/dist/api/v1/uc/UC-1.1.1/index.json" not in err


def test_main_path_match_anchor_is_end_of_string(
    fake_repo: pathlib.Path,
    write_spec: WriteSpec,
    write_dist_api: WriteDistApi,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Trailing `$` in regex ensures `/foo` doesn't match `/foo/bar`.

    Note: `re.match` already anchors at the beginning so without the `$` the
    template would match prefix-only, which would be wrong.
    """
    write_spec(
        "openapi.yaml",
        "paths:\n  /dist/api/v1/uc/{ucId}:\n    get: x\n",
    )
    write_dist_api("v1/uc/UC-1.1.1/index.json")
    assert od.main([]) == 1
    err = capsys.readouterr().err
    assert "/dist/api/v1/uc/UC-1.1.1/index.json" in err
