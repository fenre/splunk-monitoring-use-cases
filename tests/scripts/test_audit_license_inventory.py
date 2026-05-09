"""Unit tests for ``scripts/audit_license_inventory.py``.

Repo-overhaul plan §P11 (2026-05-09): the license auditor backstops
the legal-review story every time a new dependency lands. These tests
exercise the pure helpers (PEP 508 parsing, SPDX normalisation, header
heuristics, skip-dir logic, Markdown rendering) directly, then drive
``main()`` end-to-end via :func:`monkeypatch.setattr` to swap in a
synthetic ``REPO_ROOT`` so the live working tree never affects the
assertions.

Test surface
------------

* :func:`test_split_requirement_handles_extras` — PEP 508 parser drops
  ``[extras]`` groups but preserves the version constraint.
* :func:`test_normalise_license_string_aliases_known_strings` — alias
  table maps messy ``License`` metadata back to SPDX.
* :func:`test_extract_spdx_prefers_license_expression` — PEP 639
  ``License-Expression`` wins over the legacy ``License`` field.
* :func:`test_extract_spdx_falls_back_to_classifier` — when neither of
  the modern fields produce an SPDX, the trove classifiers carry it.
* :func:`test_is_license_filename_rejects_lookalikes` — the filename
  filter rejects ``license-inventory.schema.json`` and accepts canonical
  names.
* :func:`test_is_inside_skip_dir_skips_dist_and_hidden_paths` —
  ``dist-content/foo/LICENSE`` and ``.venv-feasibility/x/LICENSE``
  are skipped.
* :func:`test_render_markdown_escapes_pipe_characters` — pipes inside
  table cells (e.g. ``>=4.21 | >=4.23``) are escaped.
* :func:`test_main_check_passes_with_committed_inventory` — happy path.
* :func:`test_main_check_fails_when_committed_drifts` — drift in the
  committed JSON fails CI.
* :func:`test_main_check_fails_on_disallowed_license` — a non-allowlist
  SPDX fails CI.
* :func:`test_main_write_produces_committable_artefacts` — ``--write``
  emits the JSON + Markdown pair and the resulting --check passes.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "audit_license_inventory.py"


def _load_audit_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "audit_license_inventory", SCRIPT_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["audit_license_inventory"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def ali() -> ModuleType:
    """Module-scoped import; the audit script has no side effects on import."""
    return _load_audit_module()


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def test_split_requirement_handles_extras(ali: ModuleType) -> None:
    """``[extras]`` groups are dropped; constraint preserved verbatim."""
    name, constraint = ali._split_requirement("splunk-uc[audits,build,test,dev]")
    assert name == "splunk-uc"
    assert constraint == ""

    name, constraint = ali._split_requirement("jsonschema>=4.21")
    assert name == "jsonschema"
    assert constraint == ">=4.21"

    # Markers (``; python_version`` etc.) must be stripped because the
    # dep exists regardless of the marker.
    name, constraint = ali._split_requirement(
        "respx>=0.21 ; python_version >= '3.11'"
    )
    assert name == "respx"
    assert constraint == ">=0.21"


def test_split_requirement_normalises_distribution_name(ali: ModuleType) -> None:
    """PEP 503 normalises ``Types_Pyyaml`` to ``types-pyyaml``."""
    name, _ = ali._split_requirement("Types_PyYAML>=6.0.12")
    assert name == "types-pyyaml"


def test_split_requirement_rejects_garbage(ali: ModuleType) -> None:
    """Garbage strings raise so the auditor surfaces the bad pyproject."""
    with pytest.raises(ValueError):
        ali._split_requirement("===not-a-requirement===")


def test_normalise_license_string_aliases_known_strings(ali: ModuleType) -> None:
    assert ali._normalise_license_string("MIT License") == "MIT"
    assert ali._normalise_license_string("Apache 2.0") == "Apache-2.0"
    assert ali._normalise_license_string("BSD 3-clause") == "BSD-3-Clause"
    # Already-SPDX expressions pass through unchanged.
    assert ali._normalise_license_string("Apache-2.0") == "Apache-2.0"
    assert ali._normalise_license_string("MIT OR Apache-2.0") == "MIT OR Apache-2.0"


def test_normalise_license_string_returns_none_for_unknown(ali: ModuleType) -> None:
    assert ali._normalise_license_string("") is None
    assert ali._normalise_license_string("Some weirdly-worded prose licence.") is None


class _FakeMetadata:
    """Stand-in for ``importlib.metadata.PackageMetadata``.

    Mimics only the slice of the interface the audit hits:
    ``.get(field)`` and ``.get_all(field)``.
    """

    def __init__(
        self,
        *,
        license_expression: str | None = None,
        license: str | None = None,
        classifiers: list[str] | None = None,
    ) -> None:
        self._fields: dict[str, str | None] = {
            "License-Expression": license_expression,
            "License": license,
        }
        self._classifiers: list[str] = classifiers or []

    def get(self, key: str) -> str | None:
        return self._fields.get(key)

    def get_all(self, key: str) -> list[str] | None:
        if key == "Classifier":
            return list(self._classifiers)
        return None


def test_extract_spdx_prefers_license_expression(ali: ModuleType) -> None:
    meta = _FakeMetadata(
        license_expression="MIT",
        license="Some prose",
        classifiers=["License :: OSI Approved :: BSD License"],
    )
    spdx, source = ali._extract_spdx_from_metadata(meta)
    assert spdx == "MIT"
    assert source == "license-expression"


def test_extract_spdx_falls_back_to_license_then_classifier(
    ali: ModuleType,
) -> None:
    meta = _FakeMetadata(
        license=None,
        classifiers=[
            "License :: OSI Approved :: Apache Software License",
            "Topic :: Security",
        ],
    )
    spdx, source = ali._extract_spdx_from_metadata(meta)
    assert spdx == "Apache-2.0"
    assert source == "classifier"


def test_extract_spdx_returns_unknown_when_no_signal(ali: ModuleType) -> None:
    meta = _FakeMetadata()
    spdx, source = ali._extract_spdx_from_metadata(meta)
    assert spdx == "UNKNOWN"
    assert source == "unknown"


def test_is_license_filename_rejects_lookalikes(ali: ModuleType) -> None:
    """Names that *contain* "LICENSE" but are different files should not match."""
    assert not ali._is_license_filename("license-inventory.schema.json")
    assert not ali._is_license_filename("LICENSE-MIT.json")
    # Canonical names match.
    assert ali._is_license_filename("LICENSE")
    assert ali._is_license_filename("LICENCE")
    assert ali._is_license_filename("LICENSE.txt")
    assert ali._is_license_filename("LICENSE.md")
    assert ali._is_license_filename("LICENSE.rst")
    assert ali._is_license_filename("LICENSE-MIT")
    assert ali._is_license_filename("LICENSE-APACHE.txt")


def test_is_inside_skip_dir_skips_dist_and_hidden_paths(
    ali: ModuleType, tmp_path: Path
) -> None:
    """Build outputs and dotted dirs are excluded from the enumeration."""
    skip_paths = [
        tmp_path / "dist" / "splunk-apps" / "x" / "LICENSE",
        tmp_path / "dist-content" / "splunk-apps" / "x" / "LICENSE",
        tmp_path / "dist-legacy" / "splunk-apps" / "x" / "LICENSE",
        tmp_path / ".venv" / "lib" / "x" / "LICENSE",
        tmp_path / ".venv-feasibility" / "lib" / "x" / "LICENSE",
        tmp_path / ".git" / "hooks" / "LICENSE",
        tmp_path / "node_modules" / "x" / "LICENSE",
        tmp_path / "__pycache__" / "x" / "LICENSE",
        tmp_path / "vendor" / "swagger-ui" / "LICENSE",
    ]
    for p in skip_paths:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("MIT License\n")
        assert ali._is_inside_skip_dir(p, tmp_path), p

    keep_paths = [
        tmp_path / "splunk-apps" / "x" / "LICENSE",
        tmp_path / "LICENSE",
    ]
    for p in keep_paths:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("MIT License\n")
        assert not ali._is_inside_skip_dir(p, tmp_path), p


def test_identify_license_header_recognises_common_licenses(ali: ModuleType) -> None:
    assert ali._identify_license_header(["MIT License", ""]) == "MIT"
    assert (
        ali._identify_license_header(
            ["Apache License", "Version 2.0, January 2004"]
        )
        == "Apache-2.0"
    )
    assert ali._identify_license_header(["The Unlicense"]) == "Unlicense"
    assert ali._identify_license_header(["Random prose"]) == "UNKNOWN"


def test_render_markdown_escapes_pipe_characters(ali: ModuleType) -> None:
    """``|`` inside cells is escaped so the table layout survives."""
    inventory = {
        "$schema": "../schemas/license-inventory.schema.json",
        "version": "9.2.0",
        "captured_at": "2026-05-09T11:30:00Z",
        "git_head": "0" * 40,
        "repo_license": {"spdx": "MIT", "file": "LICENSE"},
        "allowlist": ["MIT", "Apache-2.0"],
        "python_packages": [
            {
                "name": "jsonschema",
                "spdx": "MIT",
                "license_source": "license-expression",
                "consumers": ["splunk-uc", "splunk-uc-mcp"],
                "extras": ["audits", "test"],
                "version_constraint": ">=4.21 | >=4.23",
            }
        ],
        "vendored_licenses": [],
    }
    rendered = ali.render_markdown(inventory)
    # The pipe inside the version cell must be backslash-escaped.
    assert ">=4.21 \\| >=4.23" in rendered
    # The opening cell delimiter is still there.
    assert "| `jsonschema` |" in rendered


# ---------------------------------------------------------------------------
# main(): --check / --write end-to-end with a synthetic repo
# ---------------------------------------------------------------------------


@pytest.fixture
def isolated_repo(
    ali: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> dict[str, Any]:
    """Build a minimal synthetic repo and rewire the audit's globals at it.

    The script reads constants ``REPO_ROOT``, ``_PYPROJECT_FILES``,
    ``_INVENTORY_PATH`` and ``_INVENTORY_MD_PATH`` at module import time
    and keeps them as module-level globals; we monkeypatch each so a
    ``--check`` / ``--write`` run targets the fixture instead of the
    actual repo working tree.
    """
    (tmp_path / "LICENSE").write_text("MIT License\n", encoding="utf-8")
    (tmp_path / "VERSION").write_text("1.0.0\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\n'
        'name = "splunk-uc"\n'
        'version = "1.0.0"\n'
        'dependencies = []\n'
        '[project.optional-dependencies]\n'
        'audits = ["jsonschema>=4.21"]\n'
        'test = ["pytest>=8.0"]\n',
        encoding="utf-8",
    )
    (tmp_path / "mcp").mkdir()
    (tmp_path / "mcp" / "pyproject.toml").write_text(
        '[project]\n'
        'name = "splunk-uc-mcp"\n'
        'version = "0.1.0"\n'
        'dependencies = ["mcp>=1.0.0", "anyio>=4.5"]\n',
        encoding="utf-8",
    )
    inventory_path = tmp_path / "data" / "license-inventory.json"
    inventory_md_path = tmp_path / "docs" / "license-inventory.md"

    monkeypatch.setattr(ali, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        ali,
        "_PYPROJECT_FILES",
        (
            ("splunk-uc", tmp_path / "pyproject.toml"),
            ("splunk-uc-mcp", tmp_path / "mcp" / "pyproject.toml"),
        ),
    )
    monkeypatch.setattr(ali, "_INVENTORY_PATH", inventory_path)
    monkeypatch.setattr(ali, "_INVENTORY_MD_PATH", inventory_md_path)

    return {
        "root": tmp_path,
        "inventory_path": inventory_path,
        "inventory_md_path": inventory_md_path,
    }


def test_main_write_produces_committable_artefacts(
    ali: ModuleType, isolated_repo: dict[str, Any], capsys: pytest.CaptureFixture[str]
) -> None:
    """``--write`` writes both files; subsequent ``--check`` is clean."""
    rc = ali.main(["--write"])
    assert rc == 0, capsys.readouterr().err
    inv = json.loads(isolated_repo["inventory_path"].read_text(encoding="utf-8"))
    assert inv["repo_license"]["spdx"] == "MIT"
    names = sorted(p["name"] for p in inv["python_packages"])
    assert names == ["anyio", "jsonschema", "mcp", "pytest"]
    md = isolated_repo["inventory_md_path"].read_text(encoding="utf-8")
    assert "# License inventory" in md
    assert "| `jsonschema` |" in md

    rc = ali.main(["--check"])
    assert rc == 0


def test_main_check_passes_with_committed_inventory(
    ali: ModuleType,
    isolated_repo: dict[str, Any],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Bare ``main()`` (no flags) defaults to --check and passes."""
    assert ali.main(["--write"]) == 0
    rc = ali.main([])
    out = capsys.readouterr().out
    assert rc == 0
    assert "OK" in out


def test_main_check_fails_when_committed_drifts(
    ali: ModuleType,
    isolated_repo: dict[str, Any],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A committed inventory missing a real dependency fails ``--check``."""
    assert ali.main(["--write"]) == 0
    inv = json.loads(isolated_repo["inventory_path"].read_text(encoding="utf-8"))
    inv["python_packages"] = [
        p for p in inv["python_packages"] if p["name"] != "jsonschema"
    ]
    isolated_repo["inventory_path"].write_text(
        json.dumps(inv, indent=2) + "\n", encoding="utf-8"
    )
    rc = ali.main(["--check"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "drifted" in err


def test_main_check_fails_on_disallowed_license(
    ali: ModuleType,
    isolated_repo: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A non-allowlisted SPDX in the live computation fails ``--check``.

    The audit's allowlist check runs on the *live* inventory, so the
    test patches ``build_inventory`` to return a static synthetic
    inventory that includes a GPL-licensed package. The committed JSON
    + Markdown are seeded to match that exact inventory so the
    structural-drift gate and Markdown-consistency gate both pass —
    isolating the allowlist gate for the assertion.
    """
    synthetic = {
        "$schema": "../schemas/license-inventory.schema.json",
        "version": "1.0.0",
        "captured_at": "2026-05-09T00:00:00Z",
        "git_head": "0" * 40,
        "repo_license": {"spdx": "MIT", "file": "LICENSE"},
        "allowlist": list(ali.DEFAULT_ALLOWLIST),
        "python_packages": [
            {
                "name": "evil-pkg",
                "spdx": "GPL-3.0-or-later",
                "license_source": "license",
                "consumers": ["splunk-uc"],
                "extras": ["test"],
                "version_constraint": ">=1.0",
            }
        ],
        "vendored_licenses": [],
    }
    monkeypatch.setattr(ali, "build_inventory", lambda **kw: dict(synthetic))
    isolated_repo["inventory_path"].parent.mkdir(parents=True, exist_ok=True)
    isolated_repo["inventory_md_path"].parent.mkdir(parents=True, exist_ok=True)
    isolated_repo["inventory_path"].write_text(
        json.dumps(synthetic, indent=2) + "\n", encoding="utf-8"
    )
    isolated_repo["inventory_md_path"].write_text(
        ali.render_markdown(synthetic), encoding="utf-8"
    )
    rc = ali.main(["--check"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "GPL-3.0-or-later" in err
    assert "evil-pkg" in err


def test_main_check_fails_when_files_missing(
    ali: ModuleType,
    isolated_repo: dict[str, Any],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Missing committed files surface a clear remediation hint."""
    rc = ali.main(["--check"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "missing" in err
