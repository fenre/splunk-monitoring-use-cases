"""Hermetic coverage suite for ``splunk_uc.tools.validate_uc_schema_staged``.

This pre-commit hook validates a subset of staged UC JSON sidecars
against ``schemas/uc.schema.json``. It is invoked from
``.pre-commit-config.yaml`` with the list of staged paths, so a
regression here can either (a) silently let a malformed sidecar slip
through pre-commit, or (b) crash the hook for every contributor.

Brings coverage from 12.5% to 100%.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from splunk_uc.tools import validate_uc_schema_staged as vus


@pytest.fixture
def fake_schema(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> pathlib.Path:
    """Stage a minimal JSON-schema-2020-12 schema for hermetic validation."""
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["id", "title"],
        "properties": {
            "id": {"type": "string"},
            "title": {"type": "string"},
            "spl": {"type": "string"},
        },
        "additionalProperties": True,
    }
    schema_path = tmp_path / "uc.schema.json"
    schema_path.write_text(json.dumps(schema), encoding="utf-8")
    # Monkeypatch the constants the hook reads.
    monkeypatch.setattr(vus, "SCHEMA_PATH", schema_path)
    monkeypatch.setattr(vus, "REPO_ROOT", tmp_path)
    return schema_path


def _make_sidecar(path: pathlib.Path, payload: dict[str, object]) -> pathlib.Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


class TestMainHappyPath:
    def test_passes_for_valid_single_sidecar(
        self, fake_schema: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        sc = _make_sidecar(
            tmp_path / "UC-1.1.1.json",
            {"id": "1.1.1", "title": "Demo", "spl": "search index=foo"},
        )
        assert vus.main([str(sc)]) == 0

    def test_passes_for_empty_input(self, fake_schema: pathlib.Path) -> None:
        # No staged UC files → nothing to check → success.
        assert vus.main([]) == 0


class TestMainSkipsGracefully:
    def test_skips_when_schema_missing(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(vus, "SCHEMA_PATH", tmp_path / "missing.json")
        monkeypatch.setattr(vus, "REPO_ROOT", tmp_path)
        rc = vus.main([str(tmp_path / "UC-1.1.1.json")])
        assert rc == 0
        assert "not found" in capsys.readouterr().err

    def test_skips_when_jsonschema_unavailable(
        self,
        fake_schema: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Simulate an environment without jsonschema installed by
        # forcing the import to raise.
        import builtins

        real_import = builtins.__import__

        def _hide_jsonschema(name: str, *a: object, **kw: object) -> object:
            if name == "jsonschema":
                raise ImportError("simulated missing jsonschema")
            return real_import(name, *a, **kw)

        monkeypatch.setattr(builtins, "__import__", _hide_jsonschema)
        sc = _make_sidecar(
            tmp_path / "UC-1.1.1.json",
            {"id": "1.1.1", "title": "Demo"},
        )
        rc = vus.main([str(sc)])
        assert rc == 0
        err = capsys.readouterr().err
        assert "jsonschema not installed" in err

    def test_skips_missing_input_files_silently(
        self, fake_schema: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        # A staged path that no longer exists must NOT crash — it is
        # silently skipped (e.g. file was deleted then re-staged).
        ghost = tmp_path / "UC-deleted.json"
        rc = vus.main([str(ghost)])
        assert rc == 0


class TestMainFailures:
    def test_returns_1_on_invalid_json(
        self,
        fake_schema: pathlib.Path,
        tmp_path: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        bad = tmp_path / "UC-bad.json"
        bad.write_text("{not json", encoding="utf-8")
        rc = vus.main([str(bad)])
        assert rc == 1
        err = capsys.readouterr().err
        assert "UC schema validation failed" in err
        assert "invalid JSON" in err
        assert "UC-bad.json" in err

    def test_returns_1_on_missing_required_field(
        self,
        fake_schema: pathlib.Path,
        tmp_path: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        sc = _make_sidecar(
            tmp_path / "UC-1.1.1.json",
            {"id": "1.1.1"},  # missing required ``title``
        )
        rc = vus.main([str(sc)])
        assert rc == 1
        err = capsys.readouterr().err
        assert "UC-1.1.1.json" in err
        # The location is "<root>" for a top-level required-field
        # violation in jsonschema.
        assert "<root>" in err

    def test_returns_1_on_typed_field_violation(
        self,
        fake_schema: pathlib.Path,
        tmp_path: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        sc = _make_sidecar(
            tmp_path / "UC-1.1.2.json",
            {"id": "1.1.2", "title": "T", "spl": 12345},  # spl must be a string
        )
        rc = vus.main([str(sc)])
        assert rc == 1
        err = capsys.readouterr().err
        assert "spl:" in err
        # A typed-field violation should surface the nested-path location.
        assert "12345" in err or "string" in err.lower()


class TestMainPathRelative:
    def test_renders_path_relative_to_repo_root_when_possible(
        self,
        fake_schema: pathlib.Path,
        tmp_path: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        nested = tmp_path / "content" / "cat-01"
        nested.mkdir(parents=True)
        bad = _make_sidecar(nested / "UC-1.1.1.json", {"id": "1.1.1"})
        rc = vus.main([str(bad)])
        assert rc == 1
        err = capsys.readouterr().err
        # The relative path should appear without the leading tmp_path.
        assert "content/cat-01/UC-1.1.1.json" in err

    def test_falls_back_to_absolute_when_path_outside_repo(
        self,
        fake_schema: pathlib.Path,
        tmp_path: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Point REPO_ROOT at a sibling directory so the bad sidecar's
        # path is NOT relative to it. Pins the ``except ValueError``
        # fallback branch in main().
        other_root = tmp_path.parent / "elsewhere"
        other_root.mkdir(exist_ok=True)
        import pytest as _pt

        monkeypatch = _pt.MonkeyPatch()
        monkeypatch.setattr(vus, "REPO_ROOT", other_root)
        try:
            bad = _make_sidecar(tmp_path / "UC-1.1.3.json", {"id": "1.1.3"})
            rc = vus.main([str(bad)])
            assert rc == 1
            err = capsys.readouterr().err
            # The absolute path must show up because the relative_to fallback
            # was triggered.
            assert str(bad) in err
        finally:
            monkeypatch.undo()


class TestMainArgvDefault:
    def test_falls_back_to_sys_argv_when_argv_omitted(
        self,
        fake_schema: pathlib.Path,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        sc = _make_sidecar(
            tmp_path / "UC-1.1.1.json",
            {"id": "1.1.1", "title": "Demo"},
        )
        # Mimic a pre-commit invocation.
        monkeypatch.setattr(
            vus.sys, "argv", ["validate-uc-schema-staged", str(sc)]
        )
        assert vus.main(None) == 0
