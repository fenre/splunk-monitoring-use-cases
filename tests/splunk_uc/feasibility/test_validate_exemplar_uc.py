"""Hermetic coverage suite for ``splunk_uc.feasibility.validate_exemplar_uc``.

This is the Phase 0.5c feasibility spike that validates the legacy
exemplar UC (``use-cases/cat-22/uc-22.35.1.json``) against the draft
schema. The production gate lives in ``audit_compliance_mappings`` —
this is just a small reference spike, but pinning its behaviour
prevents accidental regression while it stays in the dispatcher.

Brings coverage from 36.4% to 100%.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from splunk_uc.feasibility import validate_exemplar_uc as vex


@pytest.fixture
def staged_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> tuple[pathlib.Path, pathlib.Path]:
    """Stage minimal schema + UC files and rebind module-level constants
    onto them. Returns (schema_path, uc_path)."""
    schema_path = tmp_path / "schemas" / "uc.schema.json"
    uc_path = tmp_path / "use-cases" / "cat-22" / "uc-22.35.1.json"
    schema_path.parent.mkdir(parents=True)
    uc_path.parent.mkdir(parents=True)
    schema_path.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "required": ["id", "title"],
                "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                },
                "additionalProperties": True,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(vex, "REPO", tmp_path)
    monkeypatch.setattr(vex, "SCHEMA_PATH", schema_path)
    monkeypatch.setattr(vex, "EXEMPLAR_PATH", uc_path)
    return schema_path, uc_path


class TestLoadJson:
    def test_returns_parsed_dict(self, tmp_path: pathlib.Path) -> None:
        path = tmp_path / "x.json"
        path.write_text(json.dumps({"k": "v"}), encoding="utf-8")
        assert vex.load_json(path) == {"k": "v"}


class TestMainHappyPath:
    def test_returns_0_when_uc_conforms(
        self,
        staged_paths: tuple[pathlib.Path, pathlib.Path],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _, uc_path = staged_paths
        uc_path.write_text(
            json.dumps({"id": "22.35.1", "title": "T"}), encoding="utf-8"
        )
        rc = vex.main()
        assert rc == 0
        out = capsys.readouterr().out
        assert "PASS:" in out
        assert "uc-22.35.1.json" in out
        assert "uc.schema.json" in out

    def test_accepts_argv_and_discards_it(
        self,
        staged_paths: tuple[pathlib.Path, pathlib.Path],
    ) -> None:
        _, uc_path = staged_paths
        uc_path.write_text(
            json.dumps({"id": "22.35.1", "title": "T"}), encoding="utf-8"
        )
        # ``argv`` is documented as accepted for the registry contract
        # but otherwise ignored — pin that.
        assert vex.main(["--ignored"]) == 0


class TestMainFailures:
    def test_returns_1_when_uc_missing_required_field(
        self,
        staged_paths: tuple[pathlib.Path, pathlib.Path],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _, uc_path = staged_paths
        # Missing the required ``title``.
        uc_path.write_text(json.dumps({"id": "22.35.1"}), encoding="utf-8")
        rc = vex.main()
        assert rc == 1
        err = capsys.readouterr().err
        assert "FAIL:" in err
        assert "1 schema violation" in err
        # The root-pointer placeholder must appear since the violation
        # is at the top level.
        assert "(root)" in err

    def test_returns_1_when_nested_field_violates_schema(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Forces a non-root absolute_path so the nested-pointer formatting
        ('a/b/c' style) is exercised, not just the '(root)' fallback."""
        schema_path = tmp_path / "schemas" / "uc.schema.json"
        uc_path = tmp_path / "use-cases" / "cat-22" / "uc-22.35.1.json"
        schema_path.parent.mkdir(parents=True)
        uc_path.parent.mkdir(parents=True)
        schema_path.write_text(
            json.dumps(
                {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "required": ["id", "title", "nested"],
                    "properties": {
                        "id": {"type": "string"},
                        "title": {"type": "string"},
                        "nested": {
                            "type": "object",
                            "required": ["deep"],
                            "properties": {"deep": {"type": "integer"}},
                        },
                    },
                }
            ),
            encoding="utf-8",
        )
        uc_path.write_text(
            json.dumps(
                {
                    "id": "22.35.1",
                    "title": "T",
                    "nested": {"deep": "not-an-int"},
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(vex, "REPO", tmp_path)
        monkeypatch.setattr(vex, "SCHEMA_PATH", schema_path)
        monkeypatch.setattr(vex, "EXEMPLAR_PATH", uc_path)
        rc = vex.main()
        assert rc == 1
        err = capsys.readouterr().err
        # The non-root segment pointer must appear.
        assert "nested/deep" in err


class TestModuleConstants:
    def test_module_constants_resolve_to_repo_root(self) -> None:
        """Defensive sanity check: the module's constants should still
        point at the genuine repo layout (the patches done in other
        tests don't bleed across tests)."""
        # ``REPO`` should resolve four levels up from the module file
        # (parents[3]: feasibility -> splunk_uc -> src -> repo).
        assert vex.REPO.is_dir()
        # The schemas folder MUST exist in any healthy repo checkout.
        assert (vex.REPO / "schemas").is_dir()
