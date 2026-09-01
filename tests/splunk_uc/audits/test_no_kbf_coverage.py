"""Unit tests for `src/splunk_uc/audits/no_kbf_coverage.py`."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from splunk_uc.audits import no_kbf_coverage as nk


def _good_row(idx: int = 1, **overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "id": f"KBF-MX-{idx:03d}",
        "clause": f"§{idx}-1",
        "obligation": "obligation text",
        "controlFamily": "risk-assessment",
        "splunkCoverageType": "partial",
        "assuranceTarget": "partial",
        "assuranceRationale": "Splunk can correlate telemetry.",
        "owner": "CISO",
        "evidenceArtifact": "Saved search export",
        "dataSources": ["index=grc"],
        "splunkCanDo": "Measure freshness",
        "splunkCannotDo": "Cannot sign formal attestation",
        "reviewConfidence": "guidance-supported",
        "sourceUrl": "https://lovdata.no/dokument/SF/forskrift/2012-12-07-1157",
        "ucPlan": "UC-22.26.21",
        "targetUcIds": ["22.26.21"],
    }
    row.update(overrides)
    return row


@pytest.fixture
def fake_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    repo = tmp_path / "fakerepo"
    repo.mkdir()
    monkeypatch.setattr(nk, "REPO_ROOT", repo)
    monkeypatch.setattr(
        nk,
        "MATRIX_PATH",
        repo / "data" / "per-regulation" / "no-kbf-nve-coverage-expansion.json",
    )
    monkeypatch.setattr(nk, "SOURCE_MAP_PATH", repo / "data" / "no-kbf-nve-source-map.json")
    monkeypatch.setattr(nk, "REGULATIONS_PATH", repo / "data" / "regulations.json")
    monkeypatch.setattr(nk, "DUAL_MAP_PATH", repo / "data" / "no-kbf-nis2-dual-mapping.json")
    monkeypatch.setattr(nk, "CONTENT_ROOT", repo / "content")
    (repo / "content").mkdir()
    (repo / "data" / "per-regulation").mkdir(parents=True)
    return repo


def test_kbf_regulation_reads_frameworks_key(fake_repo: Path) -> None:
    reg_path = fake_repo / "data" / "regulations.json"
    reg_path.write_text(
        json.dumps(
            {
                "frameworks": [
                    {
                        "id": "no-kbf-nve",
                        "versions": [{"commonClauses": [{"clause": "§2-3"}]}],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    reg = nk._kbf_regulation()
    assert reg is not None
    assert reg["id"] == "no-kbf-nve"


def test_validate_matrix_rejects_duplicate_clause() -> None:
    rows = [_good_row(1, clause="§2-3"), _good_row(2, clause="§2-3")]
    source_map = {"sources": [{"url": rows[0]["sourceUrl"]}]}
    errs = nk._validate_matrix({"coverageRows": rows}, source_map)
    assert any("duplicate clause" in e for e in errs)


def test_validate_uc_traceability_flags_target_mismatch(
    fake_repo: Path,
) -> None:
    matrix = {"coverageRows": [_good_row(1, clause="§2-3", targetUcIds=["22.26.21"])]}
    cat = fake_repo / "content" / "cat-22-regulatory-compliance"
    cat.mkdir(parents=True)
    (cat / "UC-22.26.21.json").write_text(
        json.dumps(
            {
                "id": "22.26.21",
                "compliance": [
                    {
                        "regulation": "NO KBF",
                        "clause": "§2-5",
                        "controlObjective": "obj",
                        "evidenceArtifact": "artifact",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    errs = nk._validate_uc_traceability(matrix)
    assert any("§2-3: matrix targetUcIds missing compliance" in e for e in errs)
    assert any("§2-5: compliance mapped on UCs not in matrix" in e for e in errs)


def test_main_passes_on_real_repo() -> None:
    rc = nk.main([])
    assert rc == 0


def test_validate_dual_mapping_requires_assurance_review() -> None:
    errs = nk._validate_dual_mapping({"mappings": [{"kbfClause": "§2-3", "nis2Clause": "Art.21(2)(a)", "topic": "x", "rationale": "y", "primaryUcIds": ["1.1.1"]}]})
    assert any("assuranceReview" in e for e in errs)


def test_validate_dual_mapping_rejects_full_nis2_assurance(
    fake_repo: Path,
) -> None:
    dual = {
        "assuranceReview": {
            "reviewedOn": "2026-09-01",
            "reviewer": "SME",
            "policy": "contributing only",
            "outcome": "approved",
        },
        "mappings": [
            {
                "kbfClause": "§2-3",
                "nis2Clause": "Art.21(2)(a)",
                "topic": "Risk",
                "rationale": "test",
                "primaryUcIds": ["22.26.21"],
            }
        ],
    }
    cat = fake_repo / "content" / "cat-22-regulatory-compliance"
    cat.mkdir(parents=True)
    (cat / "UC-22.26.21.json").write_text(
        json.dumps(
            {
                "id": "22.26.21",
                "compliance": [
                    {"regulation": "NO KBF", "clause": "§2-3"},
                    {"regulation": "nis2", "clause": "Art.21(2)(a)", "assurance": "full"},
                ],
            }
        ),
        encoding="utf-8",
    )
    errs = nk._validate_dual_mapping(dual)
    assert any("must not claim full assurance" in e for e in errs)
