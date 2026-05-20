"""Tests for ``splunk_uc.audits.license_inventory``.

P11 license inventory auditor. The audit is 971 lines wrapping ~30
small helpers — distribution-name normalisation, PEP 508 requirement
parsing, SPDX inference from messy metadata, LICENSE-file
recognition, vendored-content enumeration, markdown rendering,
allowlist violation reporting, and three orchestration modes
(``--check``, ``--write``, ``--print-{json,md}``). Before this
file landed there were zero unit tests for any of them; coverage
sat at 10.3 %.

The strategy here is:

* Pure helpers (string normalisation, PEP 508 parsing, SPDX
  inference, LICENSE-file recognition, markdown table-cell escape,
  diff/strip-volatile helpers) get exhaustive parametrised tests
  driven from the production constants (``DEFAULT_ALLOWLIST``,
  ``_LICENSE_ALIASES``, ``_LICENSE_TAG_ALLOWLIST``,
  ``_SKIP_TOP_LEVEL_DIRS``) so any future curation of those
  tables immediately surfaces here.
* I/O helpers (``_read_pyproject``, ``_enumerate_vendored_licenses``,
  ``_read_top_license``) get hermetic tests against ``tmp_path``.
* ``_resolve_python_packages`` is exercised with a stub
  ``importlib.metadata.metadata`` so we never depend on the real
  Python interpreter's package metadata (which would make the
  test non-deterministic across maintainer machines and CI).
* ``build_inventory``, ``_run_check``, ``_run_write``, ``_run_print``,
  and ``main`` are exercised with ``REPO_ROOT`` / inventory
  paths monkey-patched at ``tmp_path``, plus ``_resolve_python_packages``
  stubbed to a deterministic list.

All tests stay hermetic. No real ``pip``, no real ``git``, no real
network.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from splunk_uc.audits import license_inventory as audit


# --------------------------------------------------------------------- #
# _normalise_distribution_name
# --------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("MIT", "mit"),
        ("Apache_2.0", "apache-2-0"),
        ("pytest_cov", "pytest-cov"),
        ("PyYAML", "pyyaml"),
        ("types-PyYAML", "types-pyyaml"),
        ("zope.interface", "zope-interface"),
        ("a__b..c", "a-b-c"),
    ],
)
def test_normalise_distribution_name(raw: str, expected: str) -> None:
    assert audit._normalise_distribution_name(raw) == expected


# --------------------------------------------------------------------- #
# _split_requirement
# --------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "raw, name, constraint",
    [
        ("jsonschema>=4.21", "jsonschema", ">=4.21"),
        ("pytest-cov>=5.0", "pytest-cov", ">=5.0"),
        ("respx>=0.21", "respx", ">=0.21"),
        ("requests", "requests", ""),
        ("requests; python_version >= '3.10'", "requests", ""),
        ("splunk-uc[audits,build,test,dev]", "splunk-uc", ""),
        ("splunk-uc[audits]>=1.0", "splunk-uc", ">=1.0"),
        ("types-PyYAML>=6.0.12", "types-pyyaml", ">=6.0.12"),
        (
            "anthropic ~= 0.10, < 1.0; python_version >= '3.11'",
            "anthropic",
            "~= 0.10, < 1.0",
        ),
    ],
)
def test_split_requirement(raw: str, name: str, constraint: str) -> None:
    n, c = audit._split_requirement(raw)
    assert n == name
    assert c == constraint


def test_split_requirement_rejects_unparseable() -> None:
    with pytest.raises(ValueError, match="unparseable requirement"):
        audit._split_requirement("=== bad name ===")


def test_split_requirement_rejects_unterminated_extras() -> None:
    with pytest.raises(ValueError, match="unterminated extras group"):
        audit._split_requirement("splunk-uc[audits")


# --------------------------------------------------------------------- #
# _normalise_license_string
# --------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("MIT", "MIT"),
        ("MIT License", "MIT"),
        ("Apache 2.0", "Apache-2.0"),
        ("Apache License, Version 2.0", "Apache-2.0"),
        ("BSD 3-Clause", "BSD-3-Clause"),
        ("the unlicense", "Unlicense"),
        ("Apache-2.0 OR MIT", "Apache-2.0 OR MIT"),
        ("MIT WITH LLVM-exception", "MIT WITH LLVM-exception"),
        ("Apache-2.0.", "Apache-2.0"),  # trailing dot stripped
    ],
)
def test_normalise_license_string_resolves_known(raw: str, expected: str) -> None:
    assert audit._normalise_license_string(raw) == expected


@pytest.mark.parametrize("raw", ["", "  ", "   .", "complete prose with spaces"])
def test_normalise_license_string_returns_none_on_unknown(raw: str) -> None:
    assert audit._normalise_license_string(raw) is None


# --------------------------------------------------------------------- #
# _extract_spdx_from_metadata
# --------------------------------------------------------------------- #


class _StubMeta:
    """Mimic ``email.message.Message`` for ``importlib.metadata``."""

    def __init__(
        self,
        *,
        license_expr: str | None = None,
        license_legacy: str | None = None,
        classifiers: list[str] | None = None,
    ) -> None:
        self._le = license_expr
        self._ll = license_legacy
        self._cls = classifiers or []

    def get(self, key: str) -> str | None:
        if key == "License-Expression":
            return self._le
        if key == "License":
            return self._ll
        return None

    def get_all(self, key: str) -> list[str] | None:
        if key == "Classifier":
            return list(self._cls)
        return None


def test_extract_spdx_prefers_license_expression() -> None:
    meta = _StubMeta(license_expr="Apache-2.0 OR MIT")
    spdx, source = audit._extract_spdx_from_metadata(meta)
    assert spdx == "Apache-2.0 OR MIT"
    assert source == "license-expression"


def test_extract_spdx_falls_back_to_license_field() -> None:
    meta = _StubMeta(license_legacy="MIT License")
    spdx, source = audit._extract_spdx_from_metadata(meta)
    assert spdx == "MIT"
    assert source == "license"


def test_extract_spdx_uses_curated_classifier() -> None:
    meta = _StubMeta(
        classifiers=["License :: OSI Approved :: MIT License", "Topic :: Utilities"]
    )
    spdx, source = audit._extract_spdx_from_metadata(meta)
    assert spdx == "MIT"
    assert source == "classifier"


def test_extract_spdx_falls_back_to_raw_classifier() -> None:
    meta = _StubMeta(classifiers=["License :: OSI Approved :: Some Weird License"])
    spdx, source = audit._extract_spdx_from_metadata(meta)
    assert spdx == "License :: OSI Approved :: Some Weird License"
    assert source == "classifier"


def test_extract_spdx_returns_unknown_when_no_signal() -> None:
    spdx, source = audit._extract_spdx_from_metadata(_StubMeta())
    assert spdx == "UNKNOWN"
    assert source == "unknown"


# --------------------------------------------------------------------- #
# _identify_license_header
# --------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "head, expected",
    [
        (["MIT License", "", "Copyright (c) 2026"], "MIT"),
        (["Apache License", "Version 2.0"], "Apache-2.0"),
        (
            [
                "Redistribution and use in source and binary forms",
                "...",
                "Neither the name of the copyright holder...",
            ],
            "BSD-3-Clause",
        ),
        (
            [
                "Redistribution and use in source and binary forms",
                "with no name attribution clause",
            ],
            "BSD-2-Clause",
        ),
        (["ISC License"], "ISC"),
        (["Mozilla Public License", "Version 2.0"], "MPL-2.0"),
        (["Creative Commons", "CC0 1.0 Universal"], "CC0-1.0"),
        (["The Unlicense"], "Unlicense"),
        (["This is free and unencumbered software released into the public domain"], "Unlicense"),
        (["completely unknown blob"], "UNKNOWN"),
        ([], "UNKNOWN"),
        (["   ", "   "], "UNKNOWN"),  # whitespace-only
    ],
)
def test_identify_license_header(head: list[str], expected: str) -> None:
    assert audit._identify_license_header(head) == expected


# --------------------------------------------------------------------- #
# _is_license_filename
# --------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "name, expected",
    [
        ("LICENSE", True),
        ("LICENCE", True),
        ("LICENSE.txt", True),
        ("LICENSE.md", True),
        ("LICENSE.rst", True),
        ("LICENSE-MIT", True),
        ("LICENSE-APACHE", True),
        ("LICENSE-APACHE.txt", True),
        ("LICENCE-MIT", True),
        ("LICENSE-BSD3", True),
        # not a license filename at all
        ("README.md", False),
        ("OTHER", False),
        # disallowed extension
        ("LICENSE.pdf", False),
        ("LICENSE.html", False),
        # SPDX tag not on allowlist (the catch)
        ("LICENSE-WEIRD", False),
        ("LICENSE-INVENTORY", False),
        ("LICENSE-INVENTORY.MD", False),
        # double-hyphen / dot inside the tag part
        ("LICENSE-INVENTORY-V2", False),
        ("LICENSE-MIT-OLD", False),
    ],
)
def test_is_license_filename(name: str, expected: bool) -> None:
    assert audit._is_license_filename(name) is expected


# --------------------------------------------------------------------- #
# _is_inside_skip_dir
# --------------------------------------------------------------------- #


def test_is_inside_skip_dir_flags_hidden_dirs(tmp_path: Path) -> None:
    p = tmp_path / ".venv" / "lib" / "site-packages" / "x" / "LICENSE"
    p.parent.mkdir(parents=True)
    p.touch()
    assert audit._is_inside_skip_dir(p, tmp_path) is True


def test_is_inside_skip_dir_flags_pycache(tmp_path: Path) -> None:
    p = tmp_path / "src" / "__pycache__" / "x.cpython-314.pyc"
    p.parent.mkdir(parents=True)
    p.touch()
    assert audit._is_inside_skip_dir(p, tmp_path) is True


def test_is_inside_skip_dir_flags_dist(tmp_path: Path) -> None:
    p = tmp_path / "dist" / "LICENSE"
    p.parent.mkdir()
    p.touch()
    assert audit._is_inside_skip_dir(p, tmp_path) is True


def test_is_inside_skip_dir_accepts_source_tree(tmp_path: Path) -> None:
    p = tmp_path / "src" / "splunk_uc" / "LICENSE"
    p.parent.mkdir(parents=True)
    p.touch()
    assert audit._is_inside_skip_dir(p, tmp_path) is False


def test_is_inside_skip_dir_repo_root_itself_is_not_skipped(tmp_path: Path) -> None:
    """``path == repo_root`` has empty ``parts`` and must return False."""
    assert audit._is_inside_skip_dir(tmp_path, tmp_path) is False


# --------------------------------------------------------------------- #
# _vendored_subject
# --------------------------------------------------------------------- #


def test_vendored_subject_uses_curated_entry_when_match() -> None:
    sub = audit._vendored_subject("splunk-apps/splunk-uc-recommender/LICENSE")
    assert "splunk-uc-recommender" in sub
    assert "vendored verbatim" in sub


def test_vendored_subject_falls_back_to_two_level_structure() -> None:
    sub = audit._vendored_subject("foo/bar/baz/LICENSE")
    assert sub == "Vendored content under foo/bar/"


def test_vendored_subject_falls_back_to_full_path_for_top_level() -> None:
    sub = audit._vendored_subject("LICENSE-MIT")
    assert sub == "Vendored content at LICENSE-MIT"


# --------------------------------------------------------------------- #
# _md_cell — markdown pipe escape
# --------------------------------------------------------------------- #


def test_md_cell_escapes_pipe() -> None:
    assert audit._md_cell("foo | bar") == "foo \\| bar"


def test_md_cell_passthrough_when_no_pipe() -> None:
    assert audit._md_cell("plain") == "plain"


# --------------------------------------------------------------------- #
# _read_pyproject
# --------------------------------------------------------------------- #


def test_read_pyproject_parses_valid_toml(tmp_path: Path) -> None:
    p = tmp_path / "pyproject.toml"
    p.write_text('[project]\nname = "x"\nversion = "1.0"\n', encoding="utf-8")
    parsed = audit._read_pyproject(p)
    assert parsed["project"]["name"] == "x"


def test_read_pyproject_raises_on_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="missing pyproject.toml"):
        audit._read_pyproject(tmp_path / "no-such.toml")


# --------------------------------------------------------------------- #
# _collect_declared_dependencies
# --------------------------------------------------------------------- #


def test_collect_declared_dependencies_collects_runtime_and_extras() -> None:
    pyproject = {
        "project": {
            "name": "splunk-uc",
            "dependencies": ["jsonschema>=4.21", "respx>=0.21"],
            "optional-dependencies": {
                "test": ["pytest", "pytest-cov>=5.0"],
                "all": ["splunk-uc[test]"],  # MUST be skipped (meta-extra)
            },
        }
    }
    result = audit._collect_declared_dependencies(pyproject, skip_self="splunk-uc")
    assert set(result.keys()) == {"jsonschema", "respx", "pytest", "pytest-cov"}
    assert "runtime" in result["jsonschema"]["extras"]
    assert "test" in result["pytest"]["extras"]
    assert ">=4.21" in result["jsonschema"]["constraints"]


def test_collect_declared_dependencies_skips_self_reference() -> None:
    """A dependency named the same as ``skip_self`` is dropped to
    avoid the self-reference loop that the ``[all]`` meta-extra
    would otherwise introduce."""

    pyproject = {
        "project": {
            "dependencies": ["splunk-uc[audits]"],
        }
    }
    result = audit._collect_declared_dependencies(pyproject, skip_self="splunk-uc")
    assert result == {}


def test_collect_declared_dependencies_ignores_non_string_entries() -> None:
    """Malformed pyproject (e.g. someone put a dict in dependencies)
    must skip the bad entry rather than crash."""

    pyproject = {
        "project": {
            "dependencies": ["jsonschema", {"oops": "not a string"}, 123],
            "optional-dependencies": {
                "test": ["pytest", None, [1, 2]],
                # extras section that isn't a list — silently skipped
                "junk": "not-a-list",
            },
        }
    }
    result = audit._collect_declared_dependencies(pyproject, skip_self="x")
    assert set(result.keys()) == {"jsonschema", "pytest"}


def test_collect_declared_dependencies_propagates_value_error() -> None:
    pyproject = {
        "project": {
            "dependencies": ["=== unparseable ==="],
        }
    }
    with pytest.raises(ValueError):
        audit._collect_declared_dependencies(pyproject, skip_self="x")


def test_collect_declared_dependencies_propagates_value_error_from_extras() -> None:
    """Cover the second ``try/except ValueError: raise`` branch
    inside the ``optional-dependencies`` loop."""

    pyproject = {
        "project": {
            "dependencies": [],
            "optional-dependencies": {
                "test": ["=== unparseable ==="],
            },
        }
    }
    with pytest.raises(ValueError):
        audit._collect_declared_dependencies(pyproject, skip_self="x")


# --------------------------------------------------------------------- #
# _resolve_python_packages — importlib.metadata mocked
# --------------------------------------------------------------------- #


def test_resolve_python_packages_aggregates_across_consumers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Two consumers wanting the same dep collapse to one record with
    a union of extras + constraints."""

    declared = {
        "splunk-uc": {
            "jsonschema": {"extras": {"runtime"}, "constraints": {">=4.21"}},
        },
        "splunk-uc-mcp": {
            "jsonschema": {"extras": {"test"}, "constraints": {">=4.20"}},
        },
    }

    monkeypatch.setattr(
        audit._importlib_metadata,
        "metadata",
        lambda name: _StubMeta(license_expr="MIT"),
    )

    out = audit._resolve_python_packages(declared)
    assert len(out) == 1
    record = out[0]
    assert record["name"] == "jsonschema"
    assert record["spdx"] == "MIT"
    assert sorted(record["consumers"]) == ["splunk-uc", "splunk-uc-mcp"]
    assert sorted(record["extras"]) == ["runtime", "test"]
    # Two constraints join with ' | ' for transparency.
    assert ">=4.20" in record["version_constraint"]
    assert ">=4.21" in record["version_constraint"]
    assert " | " in record["version_constraint"]


def test_resolve_python_packages_raises_runtimeerror_on_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    declared = {"splunk-uc": {"nope": {"extras": {"runtime"}, "constraints": set()}}}

    def _miss(name: str) -> Any:
        raise audit._importlib_metadata.PackageNotFoundError(name)

    monkeypatch.setattr(audit._importlib_metadata, "metadata", _miss)
    with pytest.raises(RuntimeError, match="not importable in the running interpreter"):
        audit._resolve_python_packages(declared)


def test_resolve_python_packages_empty_input_returns_empty_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        audit._importlib_metadata,
        "metadata",
        lambda name: _StubMeta(license_expr="MIT"),
    )
    assert audit._resolve_python_packages({}) == []


# --------------------------------------------------------------------- #
# _read_top_license
# --------------------------------------------------------------------- #


def test_read_top_license_returns_unknown_when_missing(tmp_path: Path) -> None:
    assert audit._read_top_license(tmp_path) == {
        "spdx": "UNKNOWN",
        "file": "LICENSE",
    }


def test_read_top_license_identifies_mit(tmp_path: Path) -> None:
    (tmp_path / "LICENSE").write_text("MIT License\n\nCopyright 2026 X\n", encoding="utf-8")
    assert audit._read_top_license(tmp_path) == {
        "spdx": "MIT",
        "file": "LICENSE",
    }


# --------------------------------------------------------------------- #
# _enumerate_vendored_licenses
# --------------------------------------------------------------------- #


def test_enumerate_vendored_licenses_finds_recognised_files(tmp_path: Path) -> None:
    # NOTE: ``vendor/`` is in ``_SKIP_TOP_LEVEL_DIRS`` so we use
    # ``splunk-apps/`` and ``third_party/`` instead — those mirror the
    # real shape (the production repo vendors under ``splunk-apps/``).
    (tmp_path / "LICENSE").write_text("Top license", encoding="utf-8")
    (tmp_path / "splunk-apps").mkdir()
    (tmp_path / "splunk-apps" / "LICENSE").write_text(
        "MIT License\nCopyright X", encoding="utf-8"
    )
    (tmp_path / "third_party").mkdir()
    (tmp_path / "third_party" / "LICENSE-APACHE").write_text(
        "Apache License Version 2.0", encoding="utf-8"
    )
    # Should be skipped: hidden dir
    (tmp_path / ".cache").mkdir()
    (tmp_path / ".cache" / "LICENSE").write_text("hidden", encoding="utf-8")
    # Should be skipped: top-level skip dir
    (tmp_path / "dist").mkdir()
    (tmp_path / "dist" / "LICENSE").write_text("dist build output", encoding="utf-8")
    # Should be skipped: top-level skip dir
    (tmp_path / "vendor").mkdir()
    (tmp_path / "vendor" / "LICENSE").write_text("vendor skip", encoding="utf-8")
    # Should be skipped: not a license filename
    (tmp_path / "splunk-apps" / "README.md").write_text("readme", encoding="utf-8")

    vendored = audit._enumerate_vendored_licenses(tmp_path)
    paths = {v["path"] for v in vendored}
    assert paths == {"splunk-apps/LICENSE", "third_party/LICENSE-APACHE"}
    by_path = {v["path"]: v for v in vendored}
    assert by_path["splunk-apps/LICENSE"]["spdx"] == "MIT"
    assert by_path["third_party/LICENSE-APACHE"]["spdx"] == "Apache-2.0"


def test_enumerate_vendored_licenses_handles_unreadable_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When ``read_text`` raises OSError (corrupt file, permission
    denied), the audit must still emit the entry with empty
    head → ``UNKNOWN`` SPDX rather than crash."""

    (tmp_path / "third_party").mkdir()
    bad = tmp_path / "third_party" / "LICENSE"
    bad.write_text("dummy", encoding="utf-8")

    orig_read = Path.read_text

    # Match by name/parent rather than ``self == bad`` because macOS
    # tempdirs resolve through ``/private/var`` symlinks and direct
    # ``Path`` equality occasionally fails to fire inside rglob iteration.
    def _maybe_explode(self: Path, *a: object, **k: object) -> str:
        if self.name == "LICENSE" and self.parent.name == "third_party":
            raise OSError("simulated permission denied")
        return orig_read(self, *a, **k)

    monkeypatch.setattr(Path, "read_text", _maybe_explode)

    vendored = audit._enumerate_vendored_licenses(tmp_path)
    assert len(vendored) == 1
    assert vendored[0]["spdx"] == "UNKNOWN"


# --------------------------------------------------------------------- #
# _git_head / _read_repo_version
# --------------------------------------------------------------------- #


def test_git_head_returns_unknown_when_git_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _boom(*a: object, **k: object) -> bytes:
        raise OSError("git: not found")

    monkeypatch.setattr(audit.subprocess, "check_output", _boom)
    assert audit._git_head() == "unknown"


def test_git_head_returns_unknown_when_git_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _fail(*a: object, **k: object) -> bytes:
        raise subprocess.CalledProcessError(1, ["git"])

    monkeypatch.setattr(audit.subprocess, "check_output", _fail)
    assert audit._git_head() == "unknown"


def test_git_head_returns_sha_when_git_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(audit.subprocess, "check_output", lambda *a, **k: b"abc1234\n")
    assert audit._git_head() == "abc1234"


def test_read_repo_version_returns_unknown_when_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(audit, "REPO_ROOT", tmp_path)
    assert audit._read_repo_version() == "unknown"


def test_read_repo_version_reads_file_contents(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    (tmp_path / "VERSION").write_text("9.2.0\n", encoding="utf-8")
    monkeypatch.setattr(audit, "REPO_ROOT", tmp_path)
    assert audit._read_repo_version() == "9.2.0"


def test_read_repo_version_falls_back_when_empty(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    (tmp_path / "VERSION").write_text("   \n", encoding="utf-8")
    monkeypatch.setattr(audit, "REPO_ROOT", tmp_path)
    assert audit._read_repo_version() == "unknown"


# --------------------------------------------------------------------- #
# render_markdown
# --------------------------------------------------------------------- #


def _minimal_inventory(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "$schema": "../schemas/license-inventory.schema.json",
        "version": "9.0.0",
        "captured_at": "2026-05-20T00:00:00Z",
        "git_head": "abc1234",
        "repo_license": {"spdx": "MIT", "file": "LICENSE"},
        "allowlist": ["MIT", "Apache-2.0", "Apache-2.0 OR MIT"],
        "python_packages": [
            {
                "name": "jsonschema",
                "spdx": "MIT",
                "license_source": "license-expression",
                "consumers": ["splunk-uc"],
                "extras": ["audits"],
                "version_constraint": ">=4.21",
            }
        ],
        "vendored_licenses": [],
    }
    base.update(overrides)
    return base


def test_render_markdown_emits_summary_and_packages_table() -> None:
    md = audit.render_markdown(_minimal_inventory())
    assert "# License inventory" in md
    assert "**Repo licence**: `MIT`" in md
    assert "## Python dependencies" in md
    assert "`jsonschema`" in md
    assert "## Vendored LICENSE files" in md
    assert "_No vendored LICENSE files found" in md


def test_render_markdown_emits_vendored_table_when_present() -> None:
    inv = _minimal_inventory(
        vendored_licenses=[
            {
                "path": "vendor/LICENSE",
                "spdx": "Apache-2.0",
                "subject": "Vendored content under vendor/",
            }
        ]
    )
    md = audit.render_markdown(inv)
    assert "vendor/LICENSE" in md
    assert "Apache-2.0" in md
    assert "Vendored content under vendor/" in md


def test_render_markdown_escapes_pipes_in_consumer_and_constraint_cells() -> None:
    inv = _minimal_inventory(
        python_packages=[
            {
                "name": "x",
                "spdx": "MIT",
                "license_source": "license",
                "consumers": ["splunk-uc", "splunk-uc-mcp"],
                "extras": ["runtime"],
                "version_constraint": ">=4.21 | >=4.22",
            }
        ]
    )
    md = audit.render_markdown(inv)
    # The version_constraint contains ``|``; render_markdown must escape
    # it to avoid breaking the markdown table layout.
    assert ">=4.21 \\| >=4.22" in md


def test_render_markdown_renders_em_dash_for_empty_constraint() -> None:
    inv = _minimal_inventory(
        python_packages=[
            {
                "name": "x",
                "spdx": "MIT",
                "license_source": "license",
                "consumers": ["splunk-uc"],
                "extras": ["runtime"],
                "version_constraint": "",
            }
        ]
    )
    md = audit.render_markdown(inv)
    # Em-dash placeholder for "no constraint declared".
    assert "`—`" in md


# --------------------------------------------------------------------- #
# _violations_against_allowlist
# --------------------------------------------------------------------- #


def test_violations_empty_when_everything_passes() -> None:
    assert audit._violations_against_allowlist(_minimal_inventory()) == []


def test_violations_flags_unknown_python_package_license() -> None:
    inv = _minimal_inventory(
        python_packages=[
            {
                "name": "shady",
                "spdx": "GPL-3.0-only",
                "license_source": "classifier",
                "consumers": ["splunk-uc"],
                "extras": ["runtime"],
                "version_constraint": "",
            }
        ]
    )
    violations = audit._violations_against_allowlist(inv)
    assert any("shady" in v and "GPL-3.0-only" in v for v in violations)


def test_violations_flags_unknown_vendored_license() -> None:
    inv = _minimal_inventory(
        vendored_licenses=[
            {"path": "v/LICENSE-WEIRD", "spdx": "Proprietary", "subject": "?"},
        ]
    )
    violations = audit._violations_against_allowlist(inv)
    assert any("v/LICENSE-WEIRD" in v and "Proprietary" in v for v in violations)


def test_violations_flags_unknown_repo_license() -> None:
    inv = _minimal_inventory(repo_license={"spdx": "MysteryLic", "file": "LICENSE"})
    violations = audit._violations_against_allowlist(inv)
    assert any("repo-license" in v and "MysteryLic" in v for v in violations)


# --------------------------------------------------------------------- #
# _strip_volatile / _diff_inventories
# --------------------------------------------------------------------- #


def test_strip_volatile_redacts_captured_at_and_git_head() -> None:
    inv = _minimal_inventory()
    redacted = audit._strip_volatile(inv)
    assert redacted["captured_at"] == "<redacted>"
    assert redacted["git_head"] == "<redacted>"
    assert inv["captured_at"] != "<redacted>"  # original not mutated


def test_diff_inventories_empty_when_structurally_equal() -> None:
    a = _minimal_inventory(captured_at="2026-01-01T00:00:00Z", git_head="aaaa111")
    b = _minimal_inventory(captured_at="2026-05-01T00:00:00Z", git_head="bbbb222")
    # Only volatile fields differ — diff must report no drift.
    assert audit._diff_inventories(a, b) == []


def test_diff_inventories_surfaces_structural_drift() -> None:
    a = _minimal_inventory()
    b = _minimal_inventory(allowlist=["MIT"])  # dropped Apache + dual
    diff = audit._diff_inventories(a, b)
    assert diff
    # The unified-diff header MUST identify both sides.
    assert any("committed" in line for line in diff)
    assert any("live" in line for line in diff)


# --------------------------------------------------------------------- #
# build_inventory / _run_check / _run_write / _run_print / main
# --------------------------------------------------------------------- #


def _hermetic_repo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, Path]:
    """Build a hermetic mini-repo at ``tmp_path`` with two
    pyproject.toml files, a LICENSE, and a VERSION. Repoint every
    module-level path constant. Returns
    ``(inventory_json_path, inventory_md_path)``."""

    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "splunk-uc"\ndependencies = ["jsonschema>=4.21"]\n',
        encoding="utf-8",
    )
    (tmp_path / "mcp").mkdir()
    (tmp_path / "mcp" / "pyproject.toml").write_text(
        '[project]\nname = "splunk-uc-mcp"\ndependencies = []\n',
        encoding="utf-8",
    )
    (tmp_path / "LICENSE").write_text(
        "MIT License\n\nCopyright (c) 2026 splunk-uc\n", encoding="utf-8"
    )
    (tmp_path / "VERSION").write_text("9.0.0\n", encoding="utf-8")

    data_dir = tmp_path / "data"
    docs_dir = tmp_path / "docs"
    inventory_json = data_dir / "license-inventory.json"
    inventory_md = docs_dir / "license-inventory.md"

    monkeypatch.setattr(audit, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        audit,
        "_PYPROJECT_FILES",
        (
            ("splunk-uc", tmp_path / "pyproject.toml"),
            ("splunk-uc-mcp", tmp_path / "mcp" / "pyproject.toml"),
        ),
    )
    monkeypatch.setattr(audit, "_INVENTORY_PATH", inventory_json)
    monkeypatch.setattr(audit, "_INVENTORY_MD_PATH", inventory_md)

    # Stub importlib.metadata so we don't depend on whether ``jsonschema``
    # is actually importable in the running interpreter.
    monkeypatch.setattr(
        audit._importlib_metadata,
        "metadata",
        lambda name: _StubMeta(license_expr="MIT"),
    )
    # Pin _git_head so the volatile-strip test is deterministic.
    monkeypatch.setattr(
        audit.subprocess, "check_output", lambda *a, **k: b"abc1234\n"
    )

    return inventory_json, inventory_md


def test_build_inventory_returns_structurally_valid_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _hermetic_repo(tmp_path, monkeypatch)
    inv = audit.build_inventory(captured_at="2026-01-01T00:00:00Z", git_head="abc1234")
    assert inv["version"] == "9.0.0"
    assert inv["git_head"] == "abc1234"
    assert inv["captured_at"] == "2026-01-01T00:00:00Z"
    assert inv["repo_license"]["spdx"] == "MIT"
    names = [p["name"] for p in inv["python_packages"]]
    assert names == ["jsonschema"]


def test_run_check_returns_one_when_inventory_json_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    json_path, md_path = _hermetic_repo(tmp_path, monkeypatch)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text("placeholder", encoding="utf-8")
    rc = audit._run_check(inventory_path=json_path, inventory_md_path=md_path)
    err = capsys.readouterr().err
    assert rc == 1
    assert "committed inventory missing" in err


def test_run_check_returns_one_when_md_rollup_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    json_path, md_path = _hermetic_repo(tmp_path, monkeypatch)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text("{}", encoding="utf-8")
    rc = audit._run_check(inventory_path=json_path, inventory_md_path=md_path)
    err = capsys.readouterr().err
    assert rc == 1
    assert "committed rollup missing" in err


def test_run_check_returns_zero_on_clean_inventory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """First run write+check round-trip — write commits the live
    inventory and the matching markdown, then check reads them back
    and must agree."""

    json_path, md_path = _hermetic_repo(tmp_path, monkeypatch)
    assert audit._run_write(inventory_path=json_path, inventory_md_path=md_path) == 0
    rc = audit._run_check(inventory_path=json_path, inventory_md_path=md_path)
    out = capsys.readouterr().out
    assert rc == 0
    assert "OK — license inventory matches" in out


def test_run_check_returns_one_on_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Write a stale inventory, then mutate the live computation
    (by changing the stub SPDX) — check must surface the diff."""

    json_path, md_path = _hermetic_repo(tmp_path, monkeypatch)
    audit._run_write(inventory_path=json_path, inventory_md_path=md_path)

    # Now flip the live SPDX so re-running build_inventory disagrees.
    monkeypatch.setattr(
        audit._importlib_metadata,
        "metadata",
        lambda name: _StubMeta(license_expr="Apache-2.0"),
    )
    rc = audit._run_check(inventory_path=json_path, inventory_md_path=md_path)
    cap = capsys.readouterr()
    assert rc == 1
    assert "drifted vs. the live computation" in cap.err


def test_run_check_returns_one_on_markdown_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The JSON matches, but someone hand-edited the Markdown."""

    json_path, md_path = _hermetic_repo(tmp_path, monkeypatch)
    audit._run_write(inventory_path=json_path, inventory_md_path=md_path)

    md_path.write_text("# corrupted rollup\n", encoding="utf-8")
    rc = audit._run_check(inventory_path=json_path, inventory_md_path=md_path)
    err = capsys.readouterr().err
    assert rc == 1
    assert "Markdown rollup does not match the committed JSON" in err


def test_run_check_returns_two_when_build_inventory_raises(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    json_path, md_path = _hermetic_repo(tmp_path, monkeypatch)
    audit._run_write(inventory_path=json_path, inventory_md_path=md_path)

    def _miss(name: str) -> Any:
        raise audit._importlib_metadata.PackageNotFoundError(name)

    monkeypatch.setattr(audit._importlib_metadata, "metadata", _miss)
    rc = audit._run_check(inventory_path=json_path, inventory_md_path=md_path)
    err = capsys.readouterr().err
    assert rc == 2
    assert "not importable" in err


def test_run_check_returns_one_on_allowlist_violation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Live inventory carries a GPL package that isn't on the
    allowlist — write captures the violation (with a warning), check
    must reject it cleanly even though the JSON / Markdown match."""

    json_path, md_path = _hermetic_repo(tmp_path, monkeypatch)
    monkeypatch.setattr(
        audit._importlib_metadata,
        "metadata",
        lambda name: _StubMeta(license_expr="GPL-3.0-only"),
    )
    audit._run_write(inventory_path=json_path, inventory_md_path=md_path)
    rc = audit._run_check(inventory_path=json_path, inventory_md_path=md_path)
    err = capsys.readouterr().err
    assert rc == 1
    assert "not on the allowlist" in err
    assert "GPL-3.0-only" in err


def test_run_write_emits_warning_on_violation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    json_path, md_path = _hermetic_repo(tmp_path, monkeypatch)
    monkeypatch.setattr(
        audit._importlib_metadata,
        "metadata",
        lambda name: _StubMeta(license_expr="GPL-3.0-only"),
    )
    rc = audit._run_write(inventory_path=json_path, inventory_md_path=md_path)
    cap = capsys.readouterr()
    assert rc == 0
    assert "warning: writing inventory but the following entries are not" in cap.err
    assert "GPL-3.0-only" in cap.err


def test_run_write_returns_two_when_build_raises(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    json_path, md_path = _hermetic_repo(tmp_path, monkeypatch)

    def _miss(name: str) -> Any:
        raise audit._importlib_metadata.PackageNotFoundError(name)

    monkeypatch.setattr(audit._importlib_metadata, "metadata", _miss)
    rc = audit._run_write(inventory_path=json_path, inventory_md_path=md_path)
    err = capsys.readouterr().err
    assert rc == 2
    assert "not importable" in err


def test_run_print_json_emits_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _hermetic_repo(tmp_path, monkeypatch)
    rc = audit._run_print(json_output=True)
    out = capsys.readouterr().out
    assert rc == 0
    parsed = json.loads(out)
    assert parsed["repo_license"]["spdx"] == "MIT"


def test_run_print_markdown_emits_markdown(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _hermetic_repo(tmp_path, monkeypatch)
    rc = audit._run_print(json_output=False)
    out = capsys.readouterr().out
    assert rc == 0
    assert "# License inventory" in out


def test_run_print_returns_two_when_build_raises(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _hermetic_repo(tmp_path, monkeypatch)

    def _miss(name: str) -> Any:
        raise audit._importlib_metadata.PackageNotFoundError(name)

    monkeypatch.setattr(audit._importlib_metadata, "metadata", _miss)
    rc = audit._run_print(json_output=True)
    err = capsys.readouterr().err
    assert rc == 2
    assert "not importable" in err


def test_main_default_is_check_mode(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    json_path, md_path = _hermetic_repo(tmp_path, monkeypatch)
    audit._run_write(inventory_path=json_path, inventory_md_path=md_path)
    assert audit.main([]) == 0


def test_main_routes_to_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    json_path, md_path = _hermetic_repo(tmp_path, monkeypatch)
    assert audit.main(["--write"]) == 0
    assert json_path.is_file()
    assert md_path.is_file()


def test_main_routes_to_print_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _hermetic_repo(tmp_path, monkeypatch)
    assert audit.main(["--print-json"]) == 0
    out = capsys.readouterr().out
    assert json.loads(out)["repo_license"]["spdx"] == "MIT"


def test_main_routes_to_print_md(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _hermetic_repo(tmp_path, monkeypatch)
    assert audit.main(["--print-md"]) == 0
    out = capsys.readouterr().out
    assert "# License inventory" in out


def test_main_routes_to_check_explicit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    json_path, md_path = _hermetic_repo(tmp_path, monkeypatch)
    audit._run_write(inventory_path=json_path, inventory_md_path=md_path)
    assert audit.main(["--check"]) == 0
