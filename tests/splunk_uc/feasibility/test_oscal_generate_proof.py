"""Hermetic coverage suite for ``splunk_uc.feasibility.oscal_generate_proof``.

Brings coverage from 23.5% to 100%.

The Phase 0.5b spike takes one UC sidecar and emits a minimal NIST
OSCAL v1.1.1 Component Definition. All tests redirect ``REPO`` and
the four path constants (``EXEMPLAR``, ``OSCAL_SCHEMA``, ``OUTPUT``,
``NODE_VALIDATOR``) via ``monkeypatch`` and stub ``subprocess.run`` /
``shutil.which`` so neither the live filesystem nor a real Node
binary is required.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import uuid
from typing import Any

import pytest

from splunk_uc.feasibility import oscal_generate_proof as og

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_uc(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a complete exemplar UC payload covering every code path."""
    payload: dict[str, Any] = {
        "id": "22.35.1",
        "title": "Exemplar UC",
        "description": "Description text.",
        "value": "Why this UC matters.",
        "controlFamily": "audit",
        "owner": "compliance team",
        "criticality": "High",
        "compliance": [
            {
                "regulation": "GDPR",
                "version": "2016/679",
                "clause": "Art.32(1)(d)",
                "mode": "detective",
                "assurance": "evidence",
                "assurance_rationale": "Continuous log-based detection.",
                "clauseUrl": "https://example.com/gdpr/art-32",
            },
            {
                "regulation": "HIPAA",
                "version": "2013",
                "clause": "§164.312(b)",
                "mode": "preventive",
                "assurance": "control",
                "assurance_rationale": "Direct config enforcement.",
                # NO clauseUrl → pins the False branch of the clause_url
                # guard inside build_implemented_requirements.
            },
        ],
        "references": [
            {"url": "https://example.com/ref1", "title": "Ref 1"},
            # No ``title`` → pins the ``ref.get("title", url)`` fallback.
            {"url": "https://example.com/ref2"},
        ],
    }
    if extra:
        payload.update(extra)
    return payload


@pytest.fixture
def fake_repo(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> pathlib.Path:
    """Construct a hermetic repo skeleton and redirect every module path."""
    exemplar = tmp_path / "content" / "cat-22-x" / "UC-22.35.1.json"
    schema = tmp_path / "vendor" / "oscal" / "oscal_component_schema_v1.1.1.json"
    out = tmp_path / "data" / "crosswalks" / "oscal" / "component-definition.json"
    validator = tmp_path / "scripts" / "feasibility" / "oscal_validate.mjs"

    monkeypatch.setattr(og, "REPO", tmp_path)
    monkeypatch.setattr(og, "EXEMPLAR", exemplar)
    monkeypatch.setattr(og, "OSCAL_SCHEMA", schema)
    monkeypatch.setattr(og, "OUTPUT", out)
    monkeypatch.setattr(og, "NODE_VALIDATOR", validator)
    return tmp_path


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


class TestPureHelpers:
    def test_stable_uuid_is_deterministic_v5(self) -> None:
        first = og.stable_uuid("seed-A")
        second = og.stable_uuid("seed-A")
        third = og.stable_uuid("seed-B")
        assert first == second
        assert first != third
        # Parses as a valid UUID.
        assert uuid.UUID(first).version == 5

    def test_iso_timestamp_is_fixed_for_reproducibility(self) -> None:
        # The spike deliberately uses a fixed timestamp so generated
        # output is byte-stable across runs.
        ts = og.iso_timestamp()
        assert ts.startswith("2026-04-16T00:00:00")
        assert ts.endswith("+00:00")

    def test_slugify_control_id_applies_every_substitution(self) -> None:
        # Cover every character substitution at once.
        assert (
            og.slugify_control_id("GDPR (EU)", "Art.32:1/d")
            == "gdpr-eu-art-32-1-d"
        )

    def test_slugify_control_id_handles_section_symbol(self) -> None:
        # The U+00A7 section sign maps to "sec".
        out = og.slugify_control_id("HIPAA", "\u00a7 164.312")
        assert "sec" in out

    def test_slugify_control_id_lowercases(self) -> None:
        assert og.slugify_control_id("PCI-DSS", "REQ.1") == "pci-dss-req-1"


# ---------------------------------------------------------------------------
# build_implemented_requirements
# ---------------------------------------------------------------------------


class TestBuildImplementedRequirements:
    def test_each_compliance_entry_emits_a_full_block(self) -> None:
        uc = _make_uc()
        reqs = og.build_implemented_requirements("UC-22.35.1", uc["compliance"])
        assert len(reqs) == 2

        gdpr_req = next(r for r in reqs if r["control-id"].startswith("gdpr"))
        # uuid deterministically derived.
        assert uuid.UUID(gdpr_req["uuid"]).version == 5
        # Description embeds the UC ID + clause.
        assert "UC-22.35.1" in gdpr_req["description"]
        assert "GDPR" in gdpr_req["description"]
        # 5 props per entry: assurance, mode, regulation, regulation-version, clause.
        assert {p["name"] for p in gdpr_req["props"]} == {
            "assurance",
            "mode",
            "regulation",
            "regulation-version",
            "clause",
        }
        # Has links because clauseUrl is set.
        assert gdpr_req["links"] == [
            {"href": "https://example.com/gdpr/art-32", "rel": "reference"}
        ]

    def test_skips_links_when_clause_url_missing(self) -> None:
        uc = _make_uc()
        reqs = og.build_implemented_requirements("UC-22.35.1", uc["compliance"])
        hipaa_req = next(r for r in reqs if r["control-id"].startswith("hipaa"))
        assert "links" not in hipaa_req


# ---------------------------------------------------------------------------
# build_component_definition
# ---------------------------------------------------------------------------


class TestBuildComponentDefinition:
    def test_full_payload_round_trips_to_json(self) -> None:
        uc = _make_uc()
        cd = og.build_component_definition(uc)
        # Round-trips through json — no datetime, Path, or other
        # non-serialisable objects.
        json.dumps(cd)

        cdef = cd["component-definition"]
        assert cdef["metadata"]["oscal-version"] == "1.1.1"
        # Two unique regulations → two import sources.
        comp = cdef["components"][0]
        impl = comp["control-implementations"][0]
        # source = the first import-source's href (sorted lexically).
        # Sorted regs are [GDPR, HIPAA] → GDPR is first.
        assert impl["source"] == og.REGULATION_TO_SOURCE_HREF["GDPR"]
        # 2 references → back-matter is present.
        assert "back-matter" in cdef
        assert len(cdef["back-matter"]["resources"]) == 2

    def test_unknown_regulation_falls_back_to_urn(self) -> None:
        uc = _make_uc(
            extra={
                "compliance": [
                    {
                        "regulation": "MYSTERY-REG",
                        "version": "1",
                        "clause": "1",
                        "mode": "preventive",
                        "assurance": "control",
                        "assurance_rationale": "x",
                    }
                ]
            }
        )
        cd = og.build_component_definition(uc)
        impl = cd["component-definition"]["components"][0][
            "control-implementations"
        ][0]
        # Unknown regulation → ``urn:regulation:MYSTERY-REG``.
        assert impl["source"] == "urn:regulation:MYSTERY-REG"

    def test_empty_references_omits_back_matter(self) -> None:
        # Pin the ``if back_matter is not None`` False branch.
        uc = _make_uc(extra={"references": []})
        cd = og.build_component_definition(uc)
        assert "back-matter" not in cd["component-definition"]

    def test_empty_compliance_falls_back_to_unknown_source(self) -> None:
        # Pin the ``import_sources[0] if import_sources else "urn:unknown"``
        # False branch.
        uc = _make_uc(extra={"compliance": []})
        cd = og.build_component_definition(uc)
        impl = cd["component-definition"]["components"][0][
            "control-implementations"
        ][0]
        assert impl["source"] == "urn:unknown"


# ---------------------------------------------------------------------------
# run_ajv_validation
# ---------------------------------------------------------------------------


class TestRunAjvValidation:
    def test_returns_2_when_node_not_on_path(
        self,
        fake_repo: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(og.shutil, "which", lambda name: None)
        rc = og.run_ajv_validation(fake_repo / "out.json")
        assert rc == 2
        assert "FAIL" in capsys.readouterr().err

    def test_returns_subprocess_exit_code(
        self,
        fake_repo: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(og.shutil, "which", lambda name: "/usr/bin/node")
        # Fake CompletedProcess with non-empty stdout AND stderr to
        # pin both write branches.
        fake_proc = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="OK\n",
            stderr="warning\n",
        )
        monkeypatch.setattr(
            og.subprocess, "run", lambda *args, **kwargs: fake_proc
        )
        rc = og.run_ajv_validation(fake_repo / "out.json")
        assert rc == 0
        captured = capsys.readouterr()
        assert "OK" in captured.out
        assert "warning" in captured.err

    def test_returns_subprocess_returncode_on_failure(
        self,
        fake_repo: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(og.shutil, "which", lambda name: "/usr/bin/node")
        # No stdout/stderr → pins the False branches of the two
        # ``if proc.stdout:`` / ``if proc.stderr:`` guards.
        fake_proc = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="",
            stderr="",
        )
        monkeypatch.setattr(
            og.subprocess, "run", lambda *args, **kwargs: fake_proc
        )
        assert og.run_ajv_validation(fake_repo / "out.json") == 1


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def _write_exemplar(fake_repo: pathlib.Path, payload: dict[str, Any]) -> None:
    og.EXEMPLAR.parent.mkdir(parents=True, exist_ok=True)
    og.EXEMPLAR.write_text(json.dumps(payload), encoding="utf-8")


def _materialise_schema_and_validator(fake_repo: pathlib.Path) -> None:
    og.OSCAL_SCHEMA.parent.mkdir(parents=True, exist_ok=True)
    og.OSCAL_SCHEMA.write_text("{}", encoding="utf-8")
    og.NODE_VALIDATOR.parent.mkdir(parents=True, exist_ok=True)
    og.NODE_VALIDATOR.write_text("// stub", encoding="utf-8")


class TestMain:
    def test_returns_2_when_schema_missing(
        self,
        fake_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        rc = og.main([])
        assert rc == 2
        assert "missing OSCAL schema" in capsys.readouterr().err

    def test_returns_2_when_node_validator_missing(
        self,
        fake_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Schema present, but validator absent.
        og.OSCAL_SCHEMA.parent.mkdir(parents=True, exist_ok=True)
        og.OSCAL_SCHEMA.write_text("{}", encoding="utf-8")
        rc = og.main([])
        assert rc == 2
        assert "missing Node validator" in capsys.readouterr().err

    def test_propagates_ajv_validation_failure(
        self,
        fake_repo: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _materialise_schema_and_validator(fake_repo)
        _write_exemplar(fake_repo, _make_uc())
        # Ajv returns 9.
        monkeypatch.setattr(og, "run_ajv_validation", lambda path: 9)
        assert og.main([]) == 9

    def test_happy_path_writes_output_and_returns_0(
        self,
        fake_repo: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _materialise_schema_and_validator(fake_repo)
        _write_exemplar(fake_repo, _make_uc())
        monkeypatch.setattr(og, "run_ajv_validation", lambda path: 0)

        rc = og.main([])
        assert rc == 0
        # Output file written.
        assert og.OUTPUT.is_file()
        payload = json.loads(og.OUTPUT.read_text(encoding="utf-8"))
        assert payload["component-definition"]["metadata"]["oscal-version"] == "1.1.1"
        # Stdout summarises file + sha256.
        out = capsys.readouterr().out
        assert "generator output" in out
        assert "sha256 (on-disk)" in out

    def test_accepts_none_argv_through_dispatcher_contract(
        self,
        fake_repo: pathlib.Path,
    ) -> None:
        # Pin ``argv | None``: early-exit ensures the call is fast.
        assert og.main(None) == 2
