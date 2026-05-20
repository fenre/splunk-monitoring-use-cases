"""Hermetic unit tests for loader / payload helpers in
``splunk_uc.generators.api_surface``.

This file complements ``test_api_surface_units.py``: the latter covers
pure string / sort-key / regex helpers, while this file targets the IO
and pure-payload-builder layers — every helper that reads JSON off
disk or shapes a dict the renderer eventually serialises to
``api/v1/``.

Every test redirects the module's repo-relative globals
(``REPO_ROOT``, ``CATALOG_PATH_*``, ``ATTACK_DIR``, ``D3FEND_DIR``,
``OSCAL_DIR``, ``VERSION_FILE``) at a ``tmp_path`` fixture so the
runtime never touches the real catalogue and stays deterministic.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
from typing import Any

import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from splunk_uc.generators import api_surface as M  # noqa: E402

# ---------------------------------------------------------------------------
# _resolve_catalog_path
# ---------------------------------------------------------------------------


class TestResolveCatalogPath:
    def test_prefers_primary_when_it_exists(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        primary = tmp_path / "dist" / "catalog.json"
        legacy = tmp_path / "catalog.json"
        primary.parent.mkdir(parents=True)
        primary.write_text("{}", encoding="utf-8")
        legacy.write_text("{}", encoding="utf-8")
        monkeypatch.setattr(M, "CATALOG_PATH_PRIMARY", primary)
        monkeypatch.setattr(M, "CATALOG_PATH_LEGACY", legacy)
        assert M._resolve_catalog_path() == primary

    def test_falls_back_to_legacy_when_primary_missing(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        primary = tmp_path / "dist" / "catalog.json"
        legacy = tmp_path / "catalog.json"
        legacy.write_text("{}", encoding="utf-8")
        monkeypatch.setattr(M, "CATALOG_PATH_PRIMARY", primary)
        monkeypatch.setattr(M, "CATALOG_PATH_LEGACY", legacy)
        assert M._resolve_catalog_path() == legacy

    def test_returns_none_when_neither_exists(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            M, "CATALOG_PATH_PRIMARY", tmp_path / "missing-1.json"
        )
        monkeypatch.setattr(
            M, "CATALOG_PATH_LEGACY", tmp_path / "missing-2.json"
        )
        assert M._resolve_catalog_path() is None


# ---------------------------------------------------------------------------
# _deterministic_timestamp
# ---------------------------------------------------------------------------


class TestDeterministicTimestamp:
    def test_uses_source_date_epoch_when_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
        out = M._deterministic_timestamp()
        # 1700000000 -> 2023-11-14T22:13:20Z
        assert out == "2023-11-14T22:13:20Z"

    def test_falls_back_to_git_log_when_no_epoch(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)

        class _R:
            stdout = "1700000050\n"

        def fake_run(*_a: Any, **_k: Any) -> Any:
            return _R()

        monkeypatch.setattr(M.subprocess, "run", fake_run)
        out = M._deterministic_timestamp()
        assert out == "2023-11-14T22:14:10Z"

    def test_falls_through_to_wall_clock_when_git_unavailable(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)

        def fake_run(*_a: Any, **_k: Any) -> Any:
            raise FileNotFoundError("no git")

        monkeypatch.setattr(M.subprocess, "run", fake_run)
        out = M._deterministic_timestamp()
        # Wall-clock fallback: just assert it looks like an ISO Z stamp.
        assert out.endswith("Z") and "T" in out and len(out) == 20

    def test_falls_through_when_git_returns_garbage(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """If ``git log`` succeeds but returns a non-numeric stdout we
        must fall through to the wall-clock branch instead of crashing
        — pins line 184's reachability."""
        monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)

        class _R:
            stdout = "not-a-number\n"

        monkeypatch.setattr(M.subprocess, "run", lambda *a, **k: _R())
        out = M._deterministic_timestamp()
        assert out.endswith("Z") and "T" in out

    def test_handles_called_process_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)

        def boom(*_a: Any, **_k: Any) -> Any:
            raise subprocess.CalledProcessError(1, ["git"])

        monkeypatch.setattr(M.subprocess, "run", boom)
        out = M._deterministic_timestamp()
        assert out.endswith("Z")

    def test_handles_timeout_expired(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)

        def boom(*_a: Any, **_k: Any) -> Any:
            raise subprocess.TimeoutExpired(cmd=["git"], timeout=3)

        monkeypatch.setattr(M.subprocess, "run", boom)
        out = M._deterministic_timestamp()
        assert out.endswith("Z")

    def test_ignores_blank_source_date_epoch(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An empty (or whitespace) ``SOURCE_DATE_EPOCH`` is treated as
        unset — pins the ``sde.isdigit()`` False branch."""
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "   ")

        class _R:
            stdout = "1700000100\n"

        monkeypatch.setattr(M.subprocess, "run", lambda *a, **k: _R())
        out = M._deterministic_timestamp()
        assert out == "2023-11-14T22:15:00Z"


# ---------------------------------------------------------------------------
# _read_version
# ---------------------------------------------------------------------------


class TestReadVersion:
    def test_reads_version_file_when_present(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        version = tmp_path / "VERSION"
        version.write_text("9.9.9\n", encoding="utf-8")
        monkeypatch.setattr(M, "VERSION_FILE", version)
        assert M._read_version() == "9.9.9"

    def test_returns_zeroes_when_version_file_missing(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(M, "VERSION_FILE", tmp_path / "missing")
        assert M._read_version() == "0.0.0"


# ---------------------------------------------------------------------------
# _write_json / _write_text / _load_json
# ---------------------------------------------------------------------------


class TestWriteAndLoad:
    def test_write_json_creates_parents_and_writes_sorted(
        self, tmp_path: pathlib.Path
    ) -> None:
        out = tmp_path / "a" / "b" / "c.json"
        M._write_json(out, {"b": 2, "a": 1})
        text = out.read_text(encoding="utf-8")
        assert text.endswith("\n")
        # sort_keys=True → "a" before "b"
        assert text.index('"a"') < text.index('"b"')

    def test_write_text_appends_newline_when_missing(
        self, tmp_path: pathlib.Path
    ) -> None:
        out = tmp_path / "x.txt"
        M._write_text(out, "hello world")
        assert out.read_text(encoding="utf-8") == "hello world\n"

    def test_write_text_does_not_double_newline(
        self, tmp_path: pathlib.Path
    ) -> None:
        out = tmp_path / "x.txt"
        M._write_text(out, "hello\n")
        assert out.read_text(encoding="utf-8") == "hello\n"

    def test_load_json_round_trips(self, tmp_path: pathlib.Path) -> None:
        path = tmp_path / "x.json"
        path.write_text('{"k": [1, 2, 3]}', encoding="utf-8")
        assert M._load_json(path) == {"k": [1, 2, 3]}


# ---------------------------------------------------------------------------
# _load_ucs
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_repo_with_ucs(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> pathlib.Path:
    """Re-root the api_surface globals at ``tmp_path`` and seed two
    cat-01 sidecars."""
    cat = tmp_path / "content" / "cat-01-test"
    cat.mkdir(parents=True)
    (cat / "UC-1.1.1.json").write_text(
        json.dumps({"id": "1.1.1", "title": "First"}), encoding="utf-8"
    )
    (cat / "UC-1.1.2.json").write_text(
        json.dumps({"id": "1.1.2", "title": "Second"}), encoding="utf-8"
    )
    monkeypatch.setattr(M, "REPO_ROOT", tmp_path)
    return tmp_path


class TestLoadUcs:
    def test_loads_sidecars_and_stamps_category(
        self, fake_repo_with_ucs: pathlib.Path
    ) -> None:
        ucs = M._load_ucs()
        assert [u["id"] for u in ucs] == ["1.1.1", "1.1.2"]
        assert all(u["_category"] == 1 for u in ucs)
        assert all(u["_sourcePath"].startswith("content/cat-01-test/") for u in ucs)

    def test_raises_systemexit_on_invalid_json(
        self,
        fake_repo_with_ucs: pathlib.Path,
    ) -> None:
        bad = (
            fake_repo_with_ucs
            / "content"
            / "cat-01-test"
            / "UC-1.1.3.json"
        )
        bad.write_text("{ not json", encoding="utf-8")
        with pytest.raises(SystemExit, match="invalid JSON"):
            M._load_ucs()

    def test_raises_systemexit_when_id_missing(
        self,
        fake_repo_with_ucs: pathlib.Path,
    ) -> None:
        bad = (
            fake_repo_with_ucs
            / "content"
            / "cat-01-test"
            / "UC-1.1.3.json"
        )
        bad.write_text(json.dumps({"title": "no id"}), encoding="utf-8")
        with pytest.raises(SystemExit, match="missing a string 'id'"):
            M._load_ucs()


# ---------------------------------------------------------------------------
# _regulations_index / _regulation_detail
# ---------------------------------------------------------------------------


class TestRegulationsIndex:
    def test_returns_sorted_frameworks_with_versions(self) -> None:
        regs = {
            "schemaVersion": "1.0.0",
            "frameworks": [
                {
                    "id": "gdpr",
                    "shortName": "GDPR",
                    "name": "General Data Protection Regulation",
                    "tier": 1,
                    "jurisdiction": ["EU"],
                    "tags": ["privacy"],
                    "aliases": ["dsgvo"],
                    "versions": [
                        {"version": "2018"},
                        {"version": "2020"},
                        {"version": None},  # skipped
                    ],
                },
                {
                    "id": "ccpa",
                    "shortName": "CCPA",
                    "name": "California CCPA",
                    "tier": 2,
                    "versions": [{"version": "v1"}],
                },
            ],
        }
        out = M._regulations_index(regs)
        assert out["apiVersion"] == M.API_VERSION
        assert out["schemaVersion"] == "1.0.0"
        assert out["frameworkCount"] == 2
        # Sort is alphabetical by id, lowercased.
        assert [fw["id"] for fw in out["frameworks"]] == ["ccpa", "gdpr"]
        gdpr = next(fw for fw in out["frameworks"] if fw["id"] == "gdpr")
        assert gdpr["versions"] == ["2018", "2020"]
        assert gdpr["endpoint"].endswith("/compliance/regulations/gdpr.json")

    def test_empty_frameworks_list_yields_zero_count(self) -> None:
        out = M._regulations_index({"frameworks": [], "schemaVersion": "1.0"})
        assert out["frameworkCount"] == 0
        assert out["frameworks"] == []


class TestRegulationDetail:
    def test_shapes_versions_with_clauses_and_ucs(self) -> None:
        fw = {
            "id": "gdpr",
            "shortName": "GDPR",
            "name": "GDPR",
            "tier": 1,
            "jurisdiction": ["EU"],
            "tags": ["privacy"],
            "aliases": [],
            "versions": [
                {
                    "version": "2018",
                    "authoritativeUrl": "https://eur-lex.europa.eu/",
                    "effectiveFrom": "2018-05-25",
                    "sunsetOn": None,
                    "clauseGrammar": "Article 5(1)(a)",
                    "clauseExamples": ["Article 5(1)(a)", "Article 32"],
                    "clauseUrlTemplate": "https://example/{clause}",
                    "commonClauses": [{"clause": "Article 5(1)(a)"}],
                    "pendingChanges": [],
                },
            ],
        }
        uc_index = {
            "gdpr@2018|clauses": ["Article 32", "Article 32"],
            "gdpr@2018|ucs": ["1.1.1"],
        }
        detail = M._regulation_detail(fw, uc_index)
        assert detail["shortName"] == "GDPR"
        v = detail["versions"][0]
        assert v["clausesReferencedByCatalogue"] == ["Article 32"]
        assert v["useCasesTaggingThisVersion"] == ["1.1.1"]
        assert v["endpoint"].endswith("regulations/gdpr@2018.json")

    def test_uses_id_when_short_name_missing(self) -> None:
        fw = {"id": "x", "name": "x", "versions": []}
        out = M._regulation_detail(fw, {})
        assert out["shortName"] == "x"


# ---------------------------------------------------------------------------
# _gaps_report
# ---------------------------------------------------------------------------


class TestGapsReport:
    def test_buckets_covered_and_uncovered_clauses(self) -> None:
        regs = {
            "frameworks": [
                {
                    "id": "gdpr",
                    "shortName": "GDPR",
                    "tier": 1,
                    "versions": [
                        {
                            "version": "2018",
                            "commonClauses": [
                                {"clause": "Article 5", "priorityWeight": 2.0},
                                {"clause": "Article 32", "priorityWeight": 1.5},
                            ],
                        },
                        {"version": "2020", "commonClauses": []},
                    ],
                }
            ]
        }
        bucket = {"gdpr@2018|clauses": ["Article 5"]}
        rep = M._gaps_report(regs, bucket)
        assert rep["summary"]["totalCommonClauses"] == 2
        assert rep["summary"]["totalCommonClausesCovered"] == 1
        assert rep["summary"]["totalCommonClausesUncovered"] == 1
        entry = rep["entries"][0]
        assert entry["commonClausesUncovered"] == ["Article 32"]
        assert entry["priorityWeightedUncovered"] == 1.5

    def test_skips_versions_without_common_clauses(self) -> None:
        regs = {
            "frameworks": [
                {
                    "id": "ccpa",
                    "shortName": "CCPA",
                    "versions": [{"version": "v1", "commonClauses": []}],
                }
            ]
        }
        rep = M._gaps_report(regs, {})
        assert rep["entries"] == []

    def test_entries_sort_by_uncovered_then_id(self) -> None:
        regs = {
            "frameworks": [
                {
                    "id": "zzz",
                    "shortName": "Z",
                    "versions": [
                        {
                            "version": "v1",
                            "commonClauses": [
                                {"clause": "a", "priorityWeight": 0},
                            ],
                        }
                    ],
                },
                {
                    "id": "aaa",
                    "shortName": "A",
                    "versions": [
                        {
                            "version": "v1",
                            "commonClauses": [
                                {"clause": "x", "priorityWeight": 0},
                                {"clause": "y", "priorityWeight": 0},
                            ],
                        }
                    ],
                },
            ]
        }
        rep = M._gaps_report(regs, {})
        # 2 uncovered for aaa beats 1 uncovered for zzz.
        assert rep["entries"][0]["regulationId"] == "aaa"
        assert rep["entries"][1]["regulationId"] == "zzz"


# ---------------------------------------------------------------------------
# _compliance_index / _coverage_payload / _ucs_index_payload / _uc_detail
# ---------------------------------------------------------------------------


class TestComplianceIndex:
    def test_counts_compliance_ucs_and_cat22(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
        ucs = [
            {"id": "1.1.1", "_category": 1, "compliance": [{}]},
            {"id": "22.1.1", "_category": 22, "compliance": []},
            {"id": "22.2.1", "_category": 22, "compliance": [{}]},
            {"id": "5.1.1", "_category": 5},
        ]
        regs = {"frameworks": [{}, {}]}
        coverage = {"regulationsVersion": "2026-01-01"}
        idx = M._compliance_index(ucs, regs, coverage)
        assert idx["counts"]["useCasesTotal"] == 4
        assert idx["counts"]["useCasesWithCompliance"] == 2
        assert idx["counts"]["cat22UseCases"] == 2
        assert idx["counts"]["regulationsTotal"] == 2
        assert idx["regulationsVersion"] == "2026-01-01"


class TestCoveragePayload:
    def test_passes_through_subkeys_and_stamps_meta(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
        cov = {
            "schemaVersion": "1.0.0",
            "regulationsVersion": "2026-01-01",
            "status": "green",
            "counts": {"foo": 1},
            "coverage": {"bar": 2},
        }
        out = M._coverage_payload(cov)
        assert out["status"] == "green"
        assert out["counts"] == {"foo": 1}
        assert out["coverage"] == {"bar": 2}
        assert out["methodology"] == "/docs/coverage-methodology.md"


class TestUcsIndexPayload:
    def test_includes_only_ucs_with_compliance(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
        ucs = [
            {"id": "1.1.1", "_category": 1, "compliance": [{}]},
            {"id": "2.1.1", "_category": 2},  # no compliance
        ]
        out = M._ucs_index_payload(ucs, {})
        assert out["count"] == 1
        assert out["items"][0]["id"] == "1.1.1"


class TestUcDetailPayload:
    def test_strips_private_fields_and_adds_meta(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
        uc = {
            "id": "3.1.1",
            "title": "T",
            "_category": 3,
            "_sourcePath": "content/cat-03/UC-3.1.1.json",
            "extra": {"k": "v"},
        }
        out = M._uc_detail_payload(uc)
        assert "_category" not in out and "_sourcePath" not in out
        assert out["extra"] == {"k": "v"}
        assert out["_meta"]["sidecarEndpoint"].endswith("/ucs/3.1.1.json")
        assert out["_meta"]["oscalEndpoint"].endswith(
            "/oscal/component-definitions/3.1.1.json"
        )
        assert out["_meta"]["sourcePath"] == "content/cat-03/UC-3.1.1.json"


# ---------------------------------------------------------------------------
# _load_attack_techniques / _load_d3fend_mappings
# ---------------------------------------------------------------------------


class TestLoadAttackTechniques:
    def test_returns_empty_when_dir_missing(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(M, "ATTACK_DIR", tmp_path / "missing")
        assert M._load_attack_techniques() == {}

    def test_loads_techniques_and_skips_deprecated(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        d = tmp_path / "attack"
        d.mkdir()
        (d / "enterprise.normalised.json").write_text(
            json.dumps(
                {
                    "domain": "enterprise",
                    "techniques": [
                        {
                            "attack_id": "T1001",
                            "name": "Data Obfuscation",
                            "is_subtechnique": False,
                            "tactics": ["command-and-control"],
                            "platforms": ["Windows"],
                            "url": "https://attack/T1001",
                        },
                        {
                            "attack_id": "T1002",
                            "name": "Old",
                            "deprecated": True,
                        },
                        {"name": "no id"},  # skipped
                    ],
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(M, "ATTACK_DIR", d)
        out = M._load_attack_techniques()
        assert list(out.keys()) == ["T1001"]
        assert out["T1001"]["domain"] == "enterprise"

    def test_first_domain_wins_for_overlapping_ids(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        d = tmp_path / "attack"
        d.mkdir()
        for name, domain in [("a-enterprise", "enterprise"), ("b-ics", "ics")]:
            (d / f"{name}.normalised.json").write_text(
                json.dumps(
                    {
                        "domain": domain,
                        "techniques": [
                            {"attack_id": "T9999", "name": f"X-{domain}"}
                        ],
                    }
                ),
                encoding="utf-8",
            )
        monkeypatch.setattr(M, "ATTACK_DIR", d)
        out = M._load_attack_techniques()
        # Sorted glob → enterprise file processed first, ics second.
        assert out["T9999"]["domain"] == "enterprise"


class TestLoadD3fendMappings:
    def test_returns_empty_when_file_missing(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(M, "D3FEND_DIR", tmp_path / "missing")
        assert M._load_d3fend_mappings() == {}

    def test_handles_dict_mappings(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        d = tmp_path / "d3fend"
        d.mkdir()
        (d / "d3fend-attack-mappings.normalised.json").write_text(
            json.dumps(
                {"mappings": {"T1001": ["D3-A", "D3-A", "D3-B"]}}
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(M, "D3FEND_DIR", d)
        out = M._load_d3fend_mappings()
        assert out == {"T1001": ["D3-A", "D3-B"]}

    def test_handles_list_of_pairs(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        d = tmp_path / "d3fend"
        d.mkdir()
        (d / "d3fend-attack-mappings.normalised.json").write_text(
            json.dumps(
                {
                    "mappings": [
                        {"attack_id": "T1001", "d3fend_id": "D3-A"},
                        {"attack_id": "T1001", "countermeasure": "D3-B"},
                        {"attack_id": None, "d3fend_id": "ignore"},
                        "not a dict",
                    ]
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(M, "D3FEND_DIR", d)
        out = M._load_d3fend_mappings()
        assert out == {"T1001": ["D3-A", "D3-B"]}

    def test_returns_empty_when_shape_unrecognised(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        d = tmp_path / "d3fend"
        d.mkdir()
        (d / "d3fend-attack-mappings.normalised.json").write_text(
            json.dumps({"mappings": 123}), encoding="utf-8"
        )
        monkeypatch.setattr(M, "D3FEND_DIR", d)
        assert M._load_d3fend_mappings() == {}


# ---------------------------------------------------------------------------
# _mitre_payloads
# ---------------------------------------------------------------------------


class TestMitrePayloads:
    def test_builds_index_techniques_coverage_d3fend(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
        # Wire ATTACK_DIR with one technique referenced by both UCs.
        atk = tmp_path / "attack"
        atk.mkdir()
        (atk / "enterprise.normalised.json").write_text(
            json.dumps(
                {
                    "domain": "enterprise",
                    "techniques": [
                        {
                            "attack_id": "T1001",
                            "name": "Data Obfuscation",
                            "tactics": ["command-and-control"],
                            "platforms": [],
                        },
                        {
                            "attack_id": "T9999",
                            "name": "Unused",
                            "tactics": ["impact"],
                            "platforms": [],
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )
        d3 = tmp_path / "d3fend"
        d3.mkdir()
        (d3 / "d3fend-attack-mappings.normalised.json").write_text(
            json.dumps({"mappings": {"T1001": ["D3-FOO"]}}),
            encoding="utf-8",
        )
        monkeypatch.setattr(M, "ATTACK_DIR", atk)
        monkeypatch.setattr(M, "D3FEND_DIR", d3)

        ucs = [
            {"id": "1.1.1", "mitreAttack": ["T1001"]},
            {"id": "1.1.2", "mitreAttack": ["T1001", "T-MISSING"]},
            {"id": "1.1.3"},
        ]
        idx, techs, cov, d3pay = M._mitre_payloads(ucs)
        assert idx["counts"]["techniquesTotal"] == 2
        assert idx["counts"]["ucsWithTechniques"] == 2
        assert idx["counts"]["distinctTechniquesReferencedByCatalogue"] == 2
        assert techs["count"] == 2
        assert techs["referencedByCatalogue"] == ["T-MISSING", "T1001"]
        # Coverage groups by tactic; T1001 → command-and-control, T-MISSING
        # missing from techniques dict so absent from tacticBuckets.
        assert cov["tacticBuckets"] == {"command-and-control": ["T1001"]}
        assert cov["techniquesToUcs"]["T1001"] == ["1.1.1", "1.1.2"]
        # d3fend payload exposes counts.
        assert d3pay["countermeasureCountsByAttackId"] == {"T1001": 1}


# ---------------------------------------------------------------------------
# _load_oscal_catalogs / _load_component_definitions / _oscal_payloads
# ---------------------------------------------------------------------------


class TestLoadOscalCatalogs:
    def test_returns_empty_when_dir_missing(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(M, "OSCAL_DIR", tmp_path / "missing")
        assert M._load_oscal_catalogs() == {}

    def test_loads_normalised_catalog_files(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        d = tmp_path / "oscal"
        d.mkdir()
        (d / "nist-800-53.normalised.json").write_text(
            json.dumps({"k": 1}), encoding="utf-8"
        )
        monkeypatch.setattr(M, "OSCAL_DIR", d)
        out = M._load_oscal_catalogs()
        # ``path.stem`` strips only the final suffix, so a
        # ``foo.normalised.json`` file lands under the key
        # ``foo.normalised`` (matches the production behaviour).
        assert out == {"nist-800-53.normalised": {"k": 1}}


class TestLoadComponentDefinitions:
    def test_returns_empty_when_dir_missing(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(M, "OSCAL_DIR", tmp_path / "missing")
        assert M._load_component_definitions() == {}

    def test_loads_both_filename_shapes_and_skips_unrelated(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        d = tmp_path / "oscal"
        d.mkdir()
        (d / "component-definition-1.1.1.json").write_text(
            json.dumps({"id": "1.1.1"}), encoding="utf-8"
        )
        (d / "component-definition-uc-1.1.2.json").write_text(
            json.dumps({"id": "1.1.2"}), encoding="utf-8"
        )
        # Garbage filename: shouldn't match the regex.
        (d / "component-definition-not-a-uc.json").write_text(
            "{}", encoding="utf-8"
        )
        monkeypatch.setattr(M, "OSCAL_DIR", d)
        out = M._load_component_definitions()
        assert sorted(out.keys()) == ["1.1.1", "1.1.2"]


class TestOscalPayloads:
    def test_emits_index_and_component_index(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
        d = tmp_path / "oscal"
        d.mkdir()
        (d / "nist.normalised.json").write_text(
            json.dumps({"k": 1}), encoding="utf-8"
        )
        (d / "component-definition-1.1.1.json").write_text(
            json.dumps({"id": "1.1.1"}), encoding="utf-8"
        )
        monkeypatch.setattr(M, "OSCAL_DIR", d)
        monkeypatch.setattr(M, "REPO_ROOT", tmp_path)

        idx, comp_idx, _payload = M._oscal_payloads()
        assert idx["catalogs"] == [
            {
                "id": "nist.normalised",
                "endpoint": (
                    f"/api/{M.API_VERSION}/oscal/catalogs/nist.normalised.json"
                ),
                "source": (
                    "data/crosswalks/oscal/nist.normalised.normalised.json"
                ),
            }
        ]
        assert comp_idx["count"] == 1
        assert comp_idx["items"][0]["ucId"] == "1.1.1"

    def test_handles_missing_oscal_dir(
        self,
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When OSCAL_DIR is absent the loaders short-circuit cleanly
        and the payload reports zero items — pins the early-return
        branch of ``_load_oscal_catalogs`` *and* the empty-glob branch
        of ``_oscal_payloads``."""
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
        monkeypatch.setattr(M, "OSCAL_DIR", tmp_path / "missing")
        idx, comp_idx, payload = M._oscal_payloads()
        assert idx["catalogs"] == []
        assert idx["componentDefinitions"] == []
        assert comp_idx["count"] == 0
        assert payload == {"catalogs": {}, "components": {}}


# ---------------------------------------------------------------------------
# _is_external / _strip_timestamp_lines
# ---------------------------------------------------------------------------


class TestIsExternal:
    def test_true_for_evidence_packs_subtree(self) -> None:
        assert M._is_external(pathlib.Path("evidence-packs/gdpr.json"))

    def test_false_for_owned_paths(self) -> None:
        assert not M._is_external(pathlib.Path("compliance/coverage.json"))

    def test_false_for_empty_path(self) -> None:
        assert not M._is_external(pathlib.Path(""))


class TestStripTimestampLines:
    def test_drops_generated_at_and_generated_prefix_lines(self) -> None:
        src = (
            b'{\n  "generatedAt": "2026-01-01",\n  "x": 1\n}\n'
            b"Generated: now\n"
            b"other\n"
        )
        out = M._strip_timestamp_lines(src)
        assert b"generatedAt" not in out
        assert b"Generated:" not in out
        assert b"other" in out
