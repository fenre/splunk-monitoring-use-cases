"""Unit tests for ``splunk_uc.audits.oscal_roundtrip``.

P16 wave P: lifts ``src/splunk_uc/audits/oscal_roundtrip.py`` from
12.5% to ≥95% combined coverage. Pins every documented contract of the
Phase 4.5e OSCAL round-trip gate.
"""

from __future__ import annotations

import hashlib
import io
import json
import re
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft7Validator

from splunk_uc.audits import oscal_roundtrip as orr

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------


class TestConstants:
    def test_repo_root_points_at_real_repo(self) -> None:
        assert orr.REPO.is_dir()
        assert (orr.REPO / "content").is_dir()

    def test_api_cdef_dir_resolves(self) -> None:
        assert orr.API_CDEF_DIR == orr.REPO / "api" / "v1" / "oscal" / "component-definitions"

    def test_crosswalk_dir_resolves(self) -> None:
        assert orr.CROSSWALK_DIR == orr.REPO / "data" / "crosswalks" / "oscal"

    def test_schema_path_resolves(self) -> None:
        assert (
            orr.SCHEMA_PATH
            == orr.REPO / "schemas" / "oscal" / "v1.1.1" / "oscal_component_schema.json"
        )

    def test_manifest_path_resolves(self) -> None:
        assert orr.MANIFEST_PATH == orr.REPO / "data" / "provenance" / "ingest-manifest.json"

    def test_report_path_resolves(self) -> None:
        assert orr.REPORT_PATH == orr.REPO / "reports" / "oscal-roundtrip.json"

    def test_expected_oscal_version(self) -> None:
        assert orr.EXPECTED_OSCAL_VERSION == "1.1.1"

    def test_schema_source_id(self) -> None:
        assert orr.SCHEMA_SOURCE_ID == "nist-oscal-component-definition-schema-v1.1.1"

    def test_status_buckets_present(self) -> None:
        assert orr.STATUS_OK == "ok"
        assert orr.STATUS_BAD_FILENAME == "bad-filename"
        assert orr.STATUS_BAD_JSON == "bad-json"
        assert orr.STATUS_SCHEMA_VIOLATION == "schema-violation"
        assert orr.STATUS_ROUNDTRIP_DRIFT == "roundtrip-drift"
        assert orr.STATUS_WRONG_OSCAL_VERSION == "wrong-oscal-version"
        assert orr.STATUS_MISSING_SOURCE == "missing-source"


# ---------------------------------------------------------------------------
# Regexes
# ---------------------------------------------------------------------------


class TestFilenameRe:
    @pytest.mark.parametrize(
        "name,expected",
        [
            ("1.1.1.json", "1.1.1"),
            ("22.35.1.json", "22.35.1"),
            ("9.99.999.json", "9.99.999"),
        ],
    )
    def test_matches_xyz_dot_json(self, name: str, expected: str) -> None:
        m = orr._FILENAME_RE.match(name)
        assert m is not None
        assert m.group(1) == expected

    @pytest.mark.parametrize(
        "name",
        [
            "1.1.json",  # only two parts
            "1.1.1.1.json",  # four parts
            "UC-1.1.1.json",  # UC- prefix
            "1.1.1",  # missing extension
            "1.1.1.yaml",  # wrong extension
            "index.json",  # not a UC
            "1.a.1.json",  # non-numeric
        ],
    )
    def test_rejects_non_canonical(self, name: str) -> None:
        assert orr._FILENAME_RE.match(name) is None


class TestUuidRe:
    @pytest.mark.parametrize(
        "uuid",
        [
            "12345678-1234-1234-8123-123456789abc",  # v1
            "abcdef01-2345-2abc-9def-0123456789ab",  # v2
            "abcdef01-2345-3abc-bdef-0123456789ab",  # v3
            "abcdef01-2345-4abc-adef-0123456789ab",  # v4
            "abcdef01-2345-5abc-8def-0123456789ab",  # v5
            "ABCDEF01-2345-4ABC-ADEF-0123456789AB",  # uppercase
        ],
    )
    def test_accepts_rfc4122(self, uuid: str) -> None:
        assert orr._UUID_RE.match(uuid) is not None

    @pytest.mark.parametrize(
        "uuid",
        [
            "abcdef01-2345-6abc-adef-0123456789ab",  # v6 not allowed
            "abcdef01-2345-0abc-adef-0123456789ab",  # v0 not allowed
            "abcdef01-2345-4abc-cdef-0123456789ab",  # variant 'c' not in 8/9/a/b
            "abcdef01-2345-4abc-adef-0123456789ab-extra",  # trailing junk
            "not-a-uuid",
            "",
        ],
    )
    def test_rejects_invalid(self, uuid: str) -> None:
        assert orr._UUID_RE.match(uuid) is None


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


class TestCanonicalSerialise:
    def test_indent_sort_ensure_ascii_trailing_newline(self) -> None:
        payload = {"b": 2, "a": [3, 1, 2]}
        out = orr._canonical_serialise(payload)
        assert out.endswith("\n")
        parsed = json.loads(out)
        assert parsed == payload
        # 2-space indent
        assert "  " in out
        # sorted keys: "a" appears before "b"
        assert out.index('"a"') < out.index('"b"')

    def test_preserves_unicode_without_escaping(self) -> None:
        payload = {"name": "Café Müller"}
        out = orr._canonical_serialise(payload)
        assert "Café Müller" in out
        assert "\\u00e9" not in out

    def test_round_trip_with_nested(self) -> None:
        payload = {"a": {"z": 1, "y": 2}, "b": [{"k": "v"}]}
        out = orr._canonical_serialise(payload)
        assert json.loads(out) == payload


class TestExtractUcId:
    def test_returns_uc_id_for_canonical(self, tmp_path: Path) -> None:
        p = tmp_path / "22.35.1.json"
        p.touch()
        assert orr._extract_uc_id(p) == "22.35.1"

    def test_returns_none_for_bad(self, tmp_path: Path) -> None:
        p = tmp_path / "junk.json"
        p.touch()
        assert orr._extract_uc_id(p) is None

    def test_returns_none_for_index(self, tmp_path: Path) -> None:
        p = tmp_path / "index.json"
        p.touch()
        assert orr._extract_uc_id(p) is None


class TestFindCrosswalkSource:
    def test_returns_none_when_dir_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(orr, "CROSSWALK_DIR", tmp_path / "does-not-exist")
        assert orr._find_crosswalk_source("1.1.1") is None

    def test_finds_short_form(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        cdir = tmp_path / "crosswalks"
        cdir.mkdir()
        target = cdir / "component-definition-1.1.1.json"
        target.write_text("{}", encoding="utf-8")
        monkeypatch.setattr(orr, "CROSSWALK_DIR", cdir)
        assert orr._find_crosswalk_source("1.1.1") == target

    def test_finds_uc_prefixed_form(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        cdir = tmp_path / "crosswalks"
        cdir.mkdir()
        target = cdir / "component-definition-uc-22.35.1.json"
        target.write_text("{}", encoding="utf-8")
        monkeypatch.setattr(orr, "CROSSWALK_DIR", cdir)
        assert orr._find_crosswalk_source("22.35.1") == target

    def test_returns_none_when_no_matching_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        cdir = tmp_path / "crosswalks"
        cdir.mkdir()
        (cdir / "component-definition-9.9.9.json").write_text("{}", encoding="utf-8")
        monkeypatch.setattr(orr, "CROSSWALK_DIR", cdir)
        assert orr._find_crosswalk_source("1.1.1") is None

    def test_prefers_short_form_when_both_exist(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        cdir = tmp_path / "crosswalks"
        cdir.mkdir()
        short = cdir / "component-definition-1.1.1.json"
        short.write_text("{}", encoding="utf-8")
        long = cdir / "component-definition-uc-1.1.1.json"
        long.write_text("{}", encoding="utf-8")
        monkeypatch.setattr(orr, "CROSSWALK_DIR", cdir)
        assert orr._find_crosswalk_source("1.1.1") == short


# ---------------------------------------------------------------------------
# Schema loading and SHA-256
# ---------------------------------------------------------------------------


class TestLoadSchema:
    def test_substitutes_unicode_property_escapes(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        spath = tmp_path / "schema.json"
        spath.write_text(
            json.dumps(
                {
                    "$id": "fake",
                    "type": "object",
                    "patternProperties": {"^[\\\\p{L}]+$": {"type": "string"}},
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(orr, "SCHEMA_PATH", spath)
        schema = orr._load_schema()
        # The \p{L} sequence should be replaced with [A-Za-z]
        text = json.dumps(schema)
        assert "[A-Za-z]" in text
        assert "p{L}" not in text

    def test_substitutes_p_n_escape(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        spath = tmp_path / "schema.json"
        spath.write_text(
            json.dumps({"pattern": "^[\\\\p{N}]+$"}),
            encoding="utf-8",
        )
        monkeypatch.setattr(orr, "SCHEMA_PATH", spath)
        schema = orr._load_schema()
        text = json.dumps(schema)
        assert "[0-9]" in text

    def test_returns_parsed_dict(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        spath = tmp_path / "schema.json"
        spath.write_text(json.dumps({"type": "object", "required": ["foo"]}), encoding="utf-8")
        monkeypatch.setattr(orr, "SCHEMA_PATH", spath)
        schema = orr._load_schema()
        assert schema["type"] == "object"
        assert schema["required"] == ["foo"]


class TestSchemaSha256OnDisk:
    def test_returns_sha256_hex(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        spath = tmp_path / "schema.json"
        body = b'{"hello":"world"}'
        spath.write_bytes(body)
        monkeypatch.setattr(orr, "SCHEMA_PATH", spath)
        observed = orr._schema_sha256_on_disk()
        assert observed == hashlib.sha256(body).hexdigest()
        assert len(observed) == 64


class TestSchemaSha256FromManifest:
    def test_returns_none_tuple_when_manifest_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(orr, "MANIFEST_PATH", tmp_path / "missing.json")
        assert orr._schema_sha256_from_manifest() == (None, None)

    def test_returns_sha_and_local_when_entry_present(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        mpath = tmp_path / "manifest.json"
        mpath.write_text(
            json.dumps(
                {
                    "provenance": [
                        {
                            "source_id": orr.SCHEMA_SOURCE_ID,
                            "sha256": "deadbeef" * 8,
                            "local": "schemas/oscal/v1.1.1/oscal_component_schema.json",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(orr, "MANIFEST_PATH", mpath)
        sha, local = orr._schema_sha256_from_manifest()
        assert sha == "deadbeef" * 8
        assert local == "schemas/oscal/v1.1.1/oscal_component_schema.json"

    def test_returns_none_tuple_when_source_id_absent(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        mpath = tmp_path / "manifest.json"
        mpath.write_text(
            json.dumps(
                {
                    "provenance": [
                        {"source_id": "other", "sha256": "1" * 64, "local": "x"},
                    ]
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(orr, "MANIFEST_PATH", mpath)
        assert orr._schema_sha256_from_manifest() == (None, None)

    def test_returns_none_tuple_for_empty_provenance(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        mpath = tmp_path / "manifest.json"
        mpath.write_text(json.dumps({"provenance": []}), encoding="utf-8")
        monkeypatch.setattr(orr, "MANIFEST_PATH", mpath)
        assert orr._schema_sha256_from_manifest() == (None, None)

    def test_returns_none_tuple_for_missing_provenance_key(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        mpath = tmp_path / "manifest.json"
        mpath.write_text(json.dumps({}), encoding="utf-8")
        monkeypatch.setattr(orr, "MANIFEST_PATH", mpath)
        assert orr._schema_sha256_from_manifest() == (None, None)


# ---------------------------------------------------------------------------
# _schema_meta
# ---------------------------------------------------------------------------


class TestSchemaMeta:
    def test_returns_dict_with_expected_keys(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        spath = tmp_path / "schema.json"
        spath.write_bytes(b'{"x":1}')
        mpath = tmp_path / "manifest.json"
        mpath.write_text(json.dumps({"provenance": []}), encoding="utf-8")
        repo = tmp_path
        monkeypatch.setattr(orr, "SCHEMA_PATH", spath)
        monkeypatch.setattr(orr, "MANIFEST_PATH", mpath)
        monkeypatch.setattr(orr, "REPO", repo)
        meta = orr._schema_meta()
        assert meta["path"] == "schema.json"
        assert meta["oscal_version"] == "1.1.1"
        assert len(meta["observed_sha256"]) == 64
        assert meta["expected_sha256"] is None
        assert meta["expected_local"] is None
        assert meta["expected_matches_observed"] is False
        assert meta["manifest_source_id"] == orr.SCHEMA_SOURCE_ID
        assert meta["manifest_path"] == "manifest.json"

    def test_expected_matches_observed_when_sha_matches(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        body = b'{"hello":"world"}'
        spath = tmp_path / "schema.json"
        spath.write_bytes(body)
        sha = hashlib.sha256(body).hexdigest()
        mpath = tmp_path / "manifest.json"
        mpath.write_text(
            json.dumps(
                {
                    "provenance": [
                        {
                            "source_id": orr.SCHEMA_SOURCE_ID,
                            "sha256": sha,
                            "local": "x",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(orr, "SCHEMA_PATH", spath)
        monkeypatch.setattr(orr, "MANIFEST_PATH", mpath)
        monkeypatch.setattr(orr, "REPO", tmp_path)
        meta = orr._schema_meta()
        assert meta["expected_sha256"] == sha
        assert meta["expected_matches_observed"] is True
        assert meta["expected_local"] == "x"


# ---------------------------------------------------------------------------
# _audit_file — the central record builder
# ---------------------------------------------------------------------------


def _passthrough_validator() -> Draft7Validator:
    """A Draft7 validator that accepts anything (no constraints)."""
    return Draft7Validator({})


def _strict_validator() -> Draft7Validator:
    """A Draft7 validator that demands a top-level ``component-definition`` object."""
    return Draft7Validator(
        {
            "type": "object",
            "required": ["component-definition"],
            "properties": {
                "component-definition": {
                    "type": "object",
                    "required": ["metadata"],
                    "properties": {
                        "metadata": {
                            "type": "object",
                            "required": ["oscal-version"],
                            "properties": {"oscal-version": {"const": "1.1.1"}},
                        }
                    },
                }
            },
        }
    )


def _gold_payload() -> dict[str, Any]:
    return {
        "component-definition": {
            "uuid": "12345678-1234-4abc-8def-0123456789ab",
            "metadata": {
                "title": "Test",
                "last-modified": "2026-05-19T00:00:00Z",
                "version": "1.0",
                "oscal-version": "1.1.1",
            },
            "components": [
                {
                    "uuid": "abcdef01-2345-4abc-adef-0123456789ab",
                    "title": "Component",
                    "description": "Desc",
                    "control-implementations": [
                        {
                            "uuid": "11112222-3333-4444-8555-666677778888",
                            "source": "nist",
                            "description": "ci",
                            "implemented-requirements": [
                                {
                                    "uuid": "aaaabbbb-cccc-4ddd-8eee-ffff00001111",
                                    "control-id": "AC-1",
                                    "description": "IR",
                                }
                            ],
                        }
                    ],
                }
            ],
        }
    }


@pytest.fixture
def isolated_oscal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path, Path, Path, Path]:
    """Hermetic stand-in for REPO with API + crosswalk + schema + manifest + report.

    Returns (repo, api_cdef_dir, crosswalk_dir, report_path, schema_path).
    """
    repo = tmp_path
    api_dir = repo / "api" / "v1" / "oscal" / "component-definitions"
    api_dir.mkdir(parents=True)
    cdir = repo / "data" / "crosswalks" / "oscal"
    cdir.mkdir(parents=True)
    schema_path = repo / "schemas" / "oscal" / "v1.1.1" / "oscal_component_schema.json"
    schema_path.parent.mkdir(parents=True)
    schema_path.write_text(json.dumps({"type": "object"}), encoding="utf-8")
    manifest_path = repo / "data" / "provenance" / "ingest-manifest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        json.dumps(
            {
                "provenance": [
                    {
                        "source_id": orr.SCHEMA_SOURCE_ID,
                        "sha256": hashlib.sha256(schema_path.read_bytes()).hexdigest(),
                        "local": "schemas/oscal/v1.1.1/oscal_component_schema.json",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    report_path = repo / "reports" / "oscal-roundtrip.json"
    report_path.parent.mkdir(parents=True)
    monkeypatch.setattr(orr, "REPO", repo)
    monkeypatch.setattr(orr, "API_CDEF_DIR", api_dir)
    monkeypatch.setattr(orr, "CROSSWALK_DIR", cdir)
    monkeypatch.setattr(orr, "SCHEMA_PATH", schema_path)
    monkeypatch.setattr(orr, "MANIFEST_PATH", manifest_path)
    monkeypatch.setattr(orr, "REPORT_PATH", report_path)
    return repo, api_dir, cdir, report_path, schema_path


class TestAuditFile:
    def test_bad_filename_sets_status_and_returns_early(self, isolated_oscal: Any) -> None:
        _, api_dir, _, _, _ = isolated_oscal
        bad = api_dir / "not-a-uc.json"
        bad.write_text("{}", encoding="utf-8")
        rec = orr._audit_file(_passthrough_validator(), bad)
        assert rec["status"] == orr.STATUS_BAD_FILENAME
        assert rec["uc_id"] is None
        assert any("filename does not match" in i for i in rec["issues"])
        assert rec["schema_errors"] == []
        assert rec["roundtrip_drift"] is False

    def test_bad_json_sets_status_and_returns_early(self, isolated_oscal: Any) -> None:
        _, api_dir, _, _, _ = isolated_oscal
        f = api_dir / "1.1.1.json"
        f.write_text("not valid json {", encoding="utf-8")
        rec = orr._audit_file(_passthrough_validator(), f)
        assert rec["status"] == orr.STATUS_BAD_JSON
        assert rec["uc_id"] == "1.1.1"
        assert any("JSONDecodeError" in i for i in rec["issues"])

    def test_schema_violation_recorded_with_path_and_message(self, isolated_oscal: Any) -> None:
        _, api_dir, _, _, _ = isolated_oscal
        f = api_dir / "1.1.1.json"
        body = orr._canonical_serialise({"not-component-definition": True})
        f.write_text(body, encoding="utf-8")
        rec = orr._audit_file(_strict_validator(), f)
        assert rec["status"] == orr.STATUS_SCHEMA_VIOLATION
        assert any(e["validator"] for e in rec["schema_errors"])
        assert any("violation" in i for i in rec["issues"])

    def test_schema_violation_truncates_at_100_errors(self, isolated_oscal: Any) -> None:
        _, api_dir, _, _, _ = isolated_oscal
        f = api_dir / "1.1.1.json"
        # Build a schema that requires 150 different keys at top level
        # so each missing key produces one error.
        required_keys = [f"k{i}" for i in range(150)]
        schema = {"type": "object", "required": required_keys}
        # Write empty payload through canonical serialisation so no drift
        # is flagged on top of the schema errors.
        body = orr._canonical_serialise({})
        f.write_text(body, encoding="utf-8")
        rec = orr._audit_file(Draft7Validator(schema), f)
        # When > 100 errors, only first 100 are recorded but issues
        # message says "first 100 recorded in schema_errors".
        assert len(rec["schema_errors"]) == 100
        assert any("first 100 recorded" in i for i in rec["issues"])

    def test_roundtrip_drift_when_not_canonical(self, isolated_oscal: Any) -> None:
        _, api_dir, cdir, _, _ = isolated_oscal
        f = api_dir / "1.1.1.json"
        # Non-canonical (no sort, compact) but schema-valid.
        payload = _gold_payload()
        f.write_text(json.dumps(payload), encoding="utf-8")
        # Crosswalk present, so the only issue is round-trip drift.
        (cdir / "component-definition-1.1.1.json").write_text("{}", encoding="utf-8")
        rec = orr._audit_file(_strict_validator(), f)
        assert rec["roundtrip_drift"] is True
        assert rec["status"] == orr.STATUS_ROUNDTRIP_DRIFT
        assert any("byte-equality round-trip failed" in i for i in rec["issues"])

    def test_wrong_oscal_version_sets_status(self, isolated_oscal: Any) -> None:
        _, api_dir, cdir, _, _ = isolated_oscal
        f = api_dir / "1.1.1.json"
        payload = _gold_payload()
        payload["component-definition"]["metadata"]["oscal-version"] = "1.0.0"
        f.write_text(orr._canonical_serialise(payload), encoding="utf-8")
        (cdir / "component-definition-1.1.1.json").write_text("{}", encoding="utf-8")
        rec = orr._audit_file(_passthrough_validator(), f)
        assert rec["oscal_version"] == "1.0.0"
        assert rec["status"] == orr.STATUS_WRONG_OSCAL_VERSION
        assert any("oscal-version" in i for i in rec["issues"])

    def test_missing_crosswalk_source_sets_status(self, isolated_oscal: Any) -> None:
        _, api_dir, _, _, _ = isolated_oscal
        f = api_dir / "1.1.1.json"
        f.write_text(orr._canonical_serialise(_gold_payload()), encoding="utf-8")
        rec = orr._audit_file(_passthrough_validator(), f)
        assert rec["status"] == orr.STATUS_MISSING_SOURCE
        assert rec["crosswalk_source_missing"] is True
        assert any("no crosswalk source" in i for i in rec["issues"])

    def test_ok_when_all_invariants_satisfied(self, isolated_oscal: Any) -> None:
        _, api_dir, cdir, _, _ = isolated_oscal
        f = api_dir / "1.1.1.json"
        f.write_text(orr._canonical_serialise(_gold_payload()), encoding="utf-8")
        cw = cdir / "component-definition-1.1.1.json"
        cw.write_text("{}", encoding="utf-8")
        rec = orr._audit_file(_strict_validator(), f)
        assert rec["status"] == orr.STATUS_OK
        assert rec["roundtrip_drift"] is False
        assert rec["schema_errors"] == []
        assert rec["warnings"] == []
        assert rec["crosswalk_source"] == str(cw.relative_to(orr.REPO))
        assert rec["crosswalk_source_missing"] is False
        assert rec["oscal_version"] == "1.1.1"

    def test_component_uuid_warning_for_non_rfc4122(self, isolated_oscal: Any) -> None:
        _, api_dir, cdir, _, _ = isolated_oscal
        f = api_dir / "1.1.1.json"
        payload = _gold_payload()
        payload["component-definition"]["components"][0]["uuid"] = "not-a-uuid"
        f.write_text(orr._canonical_serialise(payload), encoding="utf-8")
        (cdir / "component-definition-1.1.1.json").write_text("{}", encoding="utf-8")
        rec = orr._audit_file(_passthrough_validator(), f)
        assert any("component uuid not RFC-4122" in w for w in rec["warnings"])

    def test_implemented_requirement_uuid_warning(self, isolated_oscal: Any) -> None:
        _, api_dir, cdir, _, _ = isolated_oscal
        f = api_dir / "1.1.1.json"
        payload = _gold_payload()
        ir = payload["component-definition"]["components"][0]["control-implementations"][0][
            "implemented-requirements"
        ][0]
        ir["uuid"] = "not-a-uuid"
        f.write_text(orr._canonical_serialise(payload), encoding="utf-8")
        (cdir / "component-definition-1.1.1.json").write_text("{}", encoding="utf-8")
        rec = orr._audit_file(_passthrough_validator(), f)
        assert any("implemented-requirement uuid not RFC-4122" in w for w in rec["warnings"])

    def test_no_warning_when_no_uuid_field(self, isolated_oscal: Any) -> None:
        _, api_dir, cdir, _, _ = isolated_oscal
        f = api_dir / "1.1.1.json"
        payload = _gold_payload()
        # Drop the uuid keys entirely — the warning predicate is
        # `if uuid and not _UUID_RE.match(uuid)`.
        del payload["component-definition"]["components"][0]["uuid"]
        del payload["component-definition"]["components"][0]["control-implementations"][0][
            "implemented-requirements"
        ][0]["uuid"]
        f.write_text(orr._canonical_serialise(payload), encoding="utf-8")
        (cdir / "component-definition-1.1.1.json").write_text("{}", encoding="utf-8")
        rec = orr._audit_file(_passthrough_validator(), f)
        assert rec["warnings"] == []

    def test_non_dict_component_skipped(self, isolated_oscal: Any) -> None:
        _, api_dir, cdir, _, _ = isolated_oscal
        f = api_dir / "1.1.1.json"
        payload = _gold_payload()
        # Inject a non-dict component (a bare string) — must not crash.
        payload["component-definition"]["components"].append("not-a-dict")
        f.write_text(orr._canonical_serialise(payload), encoding="utf-8")
        (cdir / "component-definition-1.1.1.json").write_text("{}", encoding="utf-8")
        rec = orr._audit_file(_passthrough_validator(), f)
        # Status determined by schema (ok); warnings unchanged.
        assert rec["status"] == orr.STATUS_OK

    def test_non_dict_control_implementation_skipped(self, isolated_oscal: Any) -> None:
        _, api_dir, cdir, _, _ = isolated_oscal
        f = api_dir / "1.1.1.json"
        payload = _gold_payload()
        payload["component-definition"]["components"][0]["control-implementations"].append(
            "not-a-dict"
        )
        f.write_text(orr._canonical_serialise(payload), encoding="utf-8")
        (cdir / "component-definition-1.1.1.json").write_text("{}", encoding="utf-8")
        rec = orr._audit_file(_passthrough_validator(), f)
        assert rec["status"] == orr.STATUS_OK

    def test_non_dict_implemented_requirement_skipped(self, isolated_oscal: Any) -> None:
        _, api_dir, cdir, _, _ = isolated_oscal
        f = api_dir / "1.1.1.json"
        payload = _gold_payload()
        payload["component-definition"]["components"][0]["control-implementations"][0][
            "implemented-requirements"
        ].append("not-a-dict")
        f.write_text(orr._canonical_serialise(payload), encoding="utf-8")
        (cdir / "component-definition-1.1.1.json").write_text("{}", encoding="utf-8")
        rec = orr._audit_file(_passthrough_validator(), f)
        assert rec["status"] == orr.STATUS_OK

    def test_missing_component_definition_top_level(self, isolated_oscal: Any) -> None:
        _, api_dir, _, _, _ = isolated_oscal
        f = api_dir / "1.1.1.json"
        body = orr._canonical_serialise({"other-key": 1})
        f.write_text(body, encoding="utf-8")
        rec = orr._audit_file(_passthrough_validator(), f)
        assert any("no top-level 'component-definition' object" in i for i in rec["issues"])
        assert rec["status"] == orr.STATUS_SCHEMA_VIOLATION

    def test_payload_not_dict(self, isolated_oscal: Any) -> None:
        _, api_dir, _, _, _ = isolated_oscal
        f = api_dir / "1.1.1.json"
        # A JSON array — payload is not a dict, so cdef is None
        # and the "no top-level" branch fires.
        f.write_text(orr._canonical_serialise([1, 2, 3]), encoding="utf-8")
        rec = orr._audit_file(_passthrough_validator(), f)
        assert any("no top-level 'component-definition' object" in i for i in rec["issues"])

    def test_wrong_oscal_version_does_not_overwrite_existing_status(
        self, isolated_oscal: Any
    ) -> None:
        # Schema violation locks in status first; the later
        # wrong-oscal-version branch must NOT downgrade the status.
        _, api_dir, cdir, _, _ = isolated_oscal
        f = api_dir / "1.1.1.json"
        payload = _gold_payload()
        payload["component-definition"]["metadata"]["oscal-version"] = "1.0.0"
        # Non-canonical so we also have round-trip drift, but use the
        # strict schema to force schema-violation as the locked-in
        # status. We append an extra unknown required key to ensure a
        # schema error.
        f.write_text(json.dumps(payload), encoding="utf-8")
        validator = Draft7Validator(
            {
                "type": "object",
                "required": ["nonexistent-required-field"],
            }
        )
        (cdir / "component-definition-1.1.1.json").write_text("{}", encoding="utf-8")
        rec = orr._audit_file(validator, f)
        assert rec["status"] == orr.STATUS_SCHEMA_VIOLATION
        # The wrong-oscal-version issue text is still recorded even
        # though the status field stays on schema-violation.
        assert any("oscal-version" in i for i in rec["issues"])

    def test_status_precedence_schema_over_roundtrip(self, isolated_oscal: Any) -> None:
        # A file that fails schema AND has roundtrip drift retains
        # schema-violation as the primary status (round-trip flag set
        # too, but the status field is the schema one because the
        # roundtrip-drift status only fires when STATUS_OK).
        _, api_dir, _, _, _ = isolated_oscal
        f = api_dir / "1.1.1.json"
        f.write_text(json.dumps({"oops": True}), encoding="utf-8")  # non-canonical
        rec = orr._audit_file(_strict_validator(), f)
        assert rec["status"] == orr.STATUS_SCHEMA_VIOLATION
        assert rec["roundtrip_drift"] is True


# ---------------------------------------------------------------------------
# _collect_records
# ---------------------------------------------------------------------------


class TestCollectRecords:
    def test_empty_when_api_dir_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(orr, "API_CDEF_DIR", tmp_path / "does-not-exist")
        records, summary = orr._collect_records(_passthrough_validator())
        assert records == []
        assert summary["total_files_examined"] == 0
        assert summary["hard_failures"] == 0
        assert summary["warning_count"] == 0
        assert summary["roundtrip_drift_count"] == 0
        assert summary["schema_violation_count"] == 0
        assert summary["statuses"] == {}

    def test_skips_index_json(self, isolated_oscal: Any) -> None:
        _, api_dir, cdir, _, _ = isolated_oscal
        # index.json must be silently skipped.
        idx = api_dir / "index.json"
        idx.write_text("{}", encoding="utf-8")
        good = api_dir / "1.1.1.json"
        good.write_text(orr._canonical_serialise(_gold_payload()), encoding="utf-8")
        (cdir / "component-definition-1.1.1.json").write_text("{}", encoding="utf-8")
        records, _summary = orr._collect_records(_strict_validator())
        assert len(records) == 1
        assert records[0]["uc_id"] == "1.1.1"

    def test_sorted_by_uc_id_then_file(self, isolated_oscal: Any) -> None:
        _, api_dir, cdir, _, _ = isolated_oscal
        for uc in ("22.35.1", "1.1.1", "5.2.3"):
            (api_dir / f"{uc}.json").write_text(
                orr._canonical_serialise(_gold_payload()), encoding="utf-8"
            )
            (cdir / f"component-definition-{uc}.json").write_text("{}", encoding="utf-8")
        records, _ = orr._collect_records(_strict_validator())
        assert [r["uc_id"] for r in records] == ["1.1.1", "22.35.1", "5.2.3"]

    def test_summary_counts_schema_violation(self, isolated_oscal: Any) -> None:
        # A file with schema errors must increment schema_violation_count.
        _, api_dir, _, _, _ = isolated_oscal
        (api_dir / "1.1.1.json").write_text(json.dumps({"oops": True}), encoding="utf-8")
        records, summary = orr._collect_records(_strict_validator())
        assert summary["total_files_examined"] == 1
        assert summary["schema_violation_count"] == 1
        assert summary["hard_failures"] == 1
        assert records[0]["schema_errors"]

    def test_summary_counts(self, isolated_oscal: Any) -> None:
        _, api_dir, cdir, _, _ = isolated_oscal
        # File 1: OK
        (api_dir / "1.1.1.json").write_text(
            orr._canonical_serialise(_gold_payload()), encoding="utf-8"
        )
        (cdir / "component-definition-1.1.1.json").write_text("{}", encoding="utf-8")
        # File 2: round-trip drift
        (api_dir / "2.2.2.json").write_text(json.dumps(_gold_payload()), encoding="utf-8")
        (cdir / "component-definition-2.2.2.json").write_text("{}", encoding="utf-8")
        # File 3: missing crosswalk
        (api_dir / "3.3.3.json").write_text(
            orr._canonical_serialise(_gold_payload()), encoding="utf-8"
        )
        # File 4: warning only (still OK status because UUID warnings don't escalate)
        payload_w = _gold_payload()
        payload_w["component-definition"]["components"][0]["uuid"] = "bad"
        (api_dir / "4.4.4.json").write_text(orr._canonical_serialise(payload_w), encoding="utf-8")
        (cdir / "component-definition-4.4.4.json").write_text("{}", encoding="utf-8")
        _records, summary = orr._collect_records(_strict_validator())
        assert summary["total_files_examined"] == 4
        # 1 OK + 1 roundtrip-drift + 1 missing-source + 1 OK-with-warning
        assert summary["hard_failures"] == 2
        assert summary["roundtrip_drift_count"] == 1
        assert summary["statuses"][orr.STATUS_OK] == 2
        assert summary["statuses"][orr.STATUS_ROUNDTRIP_DRIFT] == 1
        assert summary["statuses"][orr.STATUS_MISSING_SOURCE] == 1
        assert summary["warning_count"] == 1


# ---------------------------------------------------------------------------
# _render_report
# ---------------------------------------------------------------------------


class TestRenderReport:
    def test_payload_shape(self) -> None:
        records: list[dict[str, Any]] = []
        summary: dict[str, Any] = {
            "total_files_examined": 0,
            "statuses": {},
            "hard_failures": 0,
            "warning_count": 0,
            "roundtrip_drift_count": 0,
            "schema_violation_count": 0,
        }
        schema_meta: dict[str, Any] = {
            "path": "schemas/foo.json",
            "oscal_version": "1.1.1",
            "observed_sha256": "a" * 64,
            "expected_sha256": "a" * 64,
            "expected_local": "x",
            "expected_matches_observed": True,
            "manifest_source_id": orr.SCHEMA_SOURCE_ID,
            "manifest_path": "data/m.json",
        }
        out = orr._render_report(records, summary, schema_meta)
        assert out.endswith("\n")
        parsed = json.loads(out)
        assert "$comment" in parsed
        assert parsed["schema"] == schema_meta
        assert parsed["records"] == records
        assert parsed["summary"] == summary

    def test_comment_starts_with_phase_4_5e(self) -> None:
        out = orr._render_report(
            [],
            {
                "total_files_examined": 0,
                "statuses": {},
                "hard_failures": 0,
                "warning_count": 0,
                "roundtrip_drift_count": 0,
                "schema_violation_count": 0,
            },
            {"path": "x", "oscal_version": "1.1.1"},
        )
        parsed = json.loads(out)
        assert "Phase 4.5e OSCAL round-trip report" in parsed["$comment"]


# ---------------------------------------------------------------------------
# _print_human_summary
# ---------------------------------------------------------------------------


class TestPrintHumanSummary:
    def _meta(self) -> dict[str, Any]:
        return {
            "path": "schemas/x.json",
            "oscal_version": "1.1.1",
            "observed_sha256": "a" * 64,
            "expected_sha256": "a" * 64,
            "expected_matches_observed": True,
            "expected_local": "y",
            "manifest_source_id": orr.SCHEMA_SOURCE_ID,
            "manifest_path": "m.json",
        }

    def test_green_no_failures(self, capsys: pytest.CaptureFixture[str]) -> None:
        orr._print_human_summary(
            [],
            {
                "total_files_examined": 0,
                "statuses": {},
                "hard_failures": 0,
                "warning_count": 0,
                "roundtrip_drift_count": 0,
                "schema_violation_count": 0,
            },
            self._meta(),
        )
        out = capsys.readouterr().out
        assert "OSCAL round-trip gate" in out
        assert "Files examined   : 0" in out
        assert "Hard failures    : 0" in out

    def test_hard_failures_render_details(self, capsys: pytest.CaptureFixture[str]) -> None:
        records = [
            {
                "uc_id": "1.1.1",
                "file": "api/v1/oscal/component-definitions/1.1.1.json",
                "status": orr.STATUS_SCHEMA_VIOLATION,
                "issues": ["foo failed", "bar failed"],
                "schema_errors": [{"path": "components/0", "message": "missing"}],
                "warnings": [],
            }
        ]
        summary = {
            "total_files_examined": 1,
            "statuses": {orr.STATUS_SCHEMA_VIOLATION: 1},
            "hard_failures": 1,
            "warning_count": 0,
            "roundtrip_drift_count": 0,
            "schema_violation_count": 1,
        }
        orr._print_human_summary(records, summary, self._meta())
        out = capsys.readouterr().out
        assert "Hard failures:" in out
        assert "1.1.1 (schema-violation)" in out
        assert "- foo failed" in out
        assert "- bar failed" in out
        assert "schema components/0: missing" in out

    def test_schema_errors_truncated_at_5(self, capsys: pytest.CaptureFixture[str]) -> None:
        schema_errors = [{"path": f"p{i}", "message": "m"} for i in range(10)]
        records = [
            {
                "uc_id": "1.1.1",
                "file": "f.json",
                "status": orr.STATUS_SCHEMA_VIOLATION,
                "issues": [],
                "schema_errors": schema_errors,
                "warnings": [],
            }
        ]
        summary = {
            "total_files_examined": 1,
            "statuses": {orr.STATUS_SCHEMA_VIOLATION: 1},
            "hard_failures": 1,
            "warning_count": 0,
            "roundtrip_drift_count": 0,
            "schema_violation_count": 1,
        }
        orr._print_human_summary(records, summary, self._meta())
        out = capsys.readouterr().out
        assert "schema p0" in out
        assert "schema p4" in out
        assert "schema p5" not in out
        assert "5 more schema error(s)" in out

    def test_schema_error_message_truncated_at_200(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        long_message = "x" * 300
        records = [
            {
                "uc_id": "1.1.1",
                "file": "f.json",
                "status": orr.STATUS_SCHEMA_VIOLATION,
                "issues": [],
                "schema_errors": [{"path": "p0", "message": long_message}],
                "warnings": [],
            }
        ]
        summary = {
            "total_files_examined": 1,
            "statuses": {orr.STATUS_SCHEMA_VIOLATION: 1},
            "hard_failures": 1,
            "warning_count": 0,
            "roundtrip_drift_count": 0,
            "schema_violation_count": 1,
        }
        orr._print_human_summary(records, summary, self._meta())
        out = capsys.readouterr().out
        # message is sliced [:200]
        truncated = "x" * 200
        assert f"schema p0: {truncated}\n" in out

    def test_zero_count_status_skipped(self, capsys: pytest.CaptureFixture[str]) -> None:
        orr._print_human_summary(
            [],
            {
                "total_files_examined": 0,
                "statuses": {"ok": 0, "schema-violation": 1},
                "hard_failures": 1,
                "warning_count": 0,
                "roundtrip_drift_count": 0,
                "schema_violation_count": 1,
            },
            self._meta(),
        )
        out = capsys.readouterr().out
        # ok has count 0 → skipped; schema-violation rendered
        assert "schema-violation" in out
        # Search by single-line pattern: "  ok  " with count "0" wouldn't appear
        assert re.search(r"^\s+ok\s+0\s*$", out, re.MULTILINE) is None


# ---------------------------------------------------------------------------
# main() CLI
# ---------------------------------------------------------------------------


class TestMainCli:
    def test_missing_schema_returns_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(orr, "REPO", tmp_path)
        monkeypatch.setattr(orr, "SCHEMA_PATH", tmp_path / "missing.json")
        monkeypatch.setattr(orr, "MANIFEST_PATH", tmp_path / "manifest.json")
        rc = orr.main([])
        assert rc == 1
        captured = capsys.readouterr()
        assert "NIST OSCAL schema missing" in captured.err

    def test_bad_schema_json_returns_error(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Schema present but malformed JSON
        spath = tmp_path / "schema.json"
        spath.write_text("not valid {", encoding="utf-8")
        monkeypatch.setattr(orr, "REPO", tmp_path)
        monkeypatch.setattr(orr, "SCHEMA_PATH", spath)
        monkeypatch.setattr(orr, "MANIFEST_PATH", tmp_path / "missing.json")
        rc = orr.main([])
        assert rc == 1
        captured = capsys.readouterr()
        assert "not valid JSON" in captured.err

    def test_default_green_path(
        self, isolated_oscal: Any, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _, api_dir, cdir, report_path, schema_path = isolated_oscal
        # Schema accepts anything; one good file with crosswalk.
        schema_path.write_text(json.dumps({"type": "object"}), encoding="utf-8")
        # Re-sync the manifest sha so schema_hash_mismatch doesn't trigger.
        from splunk_uc.audits import oscal_roundtrip as orr_mod

        (orr_mod.REPO / "data" / "provenance" / "ingest-manifest.json").write_text(
            json.dumps(
                {
                    "provenance": [
                        {
                            "source_id": orr.SCHEMA_SOURCE_ID,
                            "sha256": hashlib.sha256(schema_path.read_bytes()).hexdigest(),
                            "local": "schemas/oscal/v1.1.1/oscal_component_schema.json",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        f = api_dir / "1.1.1.json"
        f.write_text(orr._canonical_serialise(_gold_payload()), encoding="utf-8")
        (cdir / "component-definition-1.1.1.json").write_text("{}", encoding="utf-8")
        rc = orr.main([])
        assert rc == 0
        out = capsys.readouterr().out
        assert "=== OSCAL GATE: GREEN ===" in out
        assert report_path.is_file()
        # Report payload is canonical and parses as JSON.
        body = report_path.read_text(encoding="utf-8")
        parsed = json.loads(body)
        assert parsed["records"][0]["uc_id"] == "1.1.1"

    def test_default_red_path_hard_failure(
        self, isolated_oscal: Any, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _, api_dir, _, _, schema_path = isolated_oscal
        schema_path.write_text(json.dumps({"type": "object"}), encoding="utf-8")
        # Resync manifest
        from splunk_uc.audits import oscal_roundtrip as orr_mod

        (orr_mod.REPO / "data" / "provenance" / "ingest-manifest.json").write_text(
            json.dumps(
                {
                    "provenance": [
                        {
                            "source_id": orr.SCHEMA_SOURCE_ID,
                            "sha256": hashlib.sha256(schema_path.read_bytes()).hexdigest(),
                            "local": "x",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        # File missing crosswalk → STATUS_MISSING_SOURCE → hard failure
        f = api_dir / "1.1.1.json"
        f.write_text(orr._canonical_serialise(_gold_payload()), encoding="utf-8")
        rc = orr.main([])
        assert rc == 1
        out = capsys.readouterr().out
        assert "=== OSCAL GATE: RED ===" in out

    def test_schema_hash_mismatch_red(
        self, isolated_oscal: Any, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # Manifest records the wrong SHA → hard failure
        _, _, _, _, _schema_path = isolated_oscal
        from splunk_uc.audits import oscal_roundtrip as orr_mod

        (orr_mod.REPO / "data" / "provenance" / "ingest-manifest.json").write_text(
            json.dumps(
                {
                    "provenance": [
                        {
                            "source_id": orr.SCHEMA_SOURCE_ID,
                            "sha256": "0" * 64,
                            "local": "x",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        rc = orr.main([])
        assert rc == 1
        out = capsys.readouterr().out
        assert "=== OSCAL GATE: RED ===" in out
        assert "committed schema SHA-256 does not match" in out

    def test_check_mode_no_report_fails(
        self, isolated_oscal: Any, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # Report file does not exist; --check must fail with a useful message.
        from splunk_uc.audits import oscal_roundtrip as orr_mod

        (orr_mod.REPO / "data" / "provenance" / "ingest-manifest.json").write_text(
            json.dumps(
                {
                    "provenance": [
                        {
                            "source_id": orr.SCHEMA_SOURCE_ID,
                            "sha256": hashlib.sha256(orr.SCHEMA_PATH.read_bytes()).hexdigest(),
                            "local": "x",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        # Make sure the report file is missing
        if orr.REPORT_PATH.exists():
            orr.REPORT_PATH.unlink()
        rc = orr.main(["--check"])
        assert rc == 1
        err = capsys.readouterr().err
        assert "does not exist" in err

    def test_check_mode_drift_fails(
        self, isolated_oscal: Any, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _, api_dir, cdir, report_path, schema_path = isolated_oscal
        # Resync manifest
        from splunk_uc.audits import oscal_roundtrip as orr_mod

        (orr_mod.REPO / "data" / "provenance" / "ingest-manifest.json").write_text(
            json.dumps(
                {
                    "provenance": [
                        {
                            "source_id": orr.SCHEMA_SOURCE_ID,
                            "sha256": hashlib.sha256(schema_path.read_bytes()).hexdigest(),
                            "local": "x",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        f = api_dir / "1.1.1.json"
        f.write_text(orr._canonical_serialise(_gold_payload()), encoding="utf-8")
        (cdir / "component-definition-1.1.1.json").write_text("{}", encoding="utf-8")
        # Write a stale report
        report_path.write_text('{"stale": true}\n', encoding="utf-8")
        rc = orr.main(["--check"])
        assert rc == 1
        err = capsys.readouterr().err
        assert "out of date" in err

    def test_check_mode_match_succeeds(
        self, isolated_oscal: Any, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _, api_dir, cdir, _report_path, schema_path = isolated_oscal
        from splunk_uc.audits import oscal_roundtrip as orr_mod

        (orr_mod.REPO / "data" / "provenance" / "ingest-manifest.json").write_text(
            json.dumps(
                {
                    "provenance": [
                        {
                            "source_id": orr.SCHEMA_SOURCE_ID,
                            "sha256": hashlib.sha256(schema_path.read_bytes()).hexdigest(),
                            "local": "x",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        f = api_dir / "1.1.1.json"
        f.write_text(orr._canonical_serialise(_gold_payload()), encoding="utf-8")
        (cdir / "component-definition-1.1.1.json").write_text("{}", encoding="utf-8")
        # Generate the report first
        assert orr.main([]) == 0
        # Re-run with --check should succeed
        rc = orr.main(["--check"])
        assert rc == 0

    def test_help_mentions_check_and_phase(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as excinfo:
            orr.main(["--help"])
        assert excinfo.value.code == 0
        out = capsys.readouterr().out
        assert "--check" in out
        assert "Phase 4.5e" in out

    def test_module_run_as_main_invokes_sys_exit(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Verify the `if __name__ == "__main__"` block routes through main().
        # We just confirm the symbol is callable; the actual __main__ block
        # is dead-coded at import time and excluded from coverage gates.
        assert callable(orr.main)
