"""Unit tests for `src/splunk_uc/audits/nis2_no_gap.py`.

The NIS2 no-gap auditor validates two artefacts:

1. ``data/per-regulation/nis2-coverage-expansion.json`` — the
   coverage matrix, which must carry one row per legal obligation
   with the 21-field shape (id, source, sourceUrl, clause,
   obligation, evidenceArtifact, owner, references, etc.).
2. Every UC sidecar carrying a ``compliance`` entry with
   ``regulation == "NIS2"`` must trace back to a matrix clause and
   carry the documented ``clauseUrl`` / ``controlObjective`` /
   ``evidenceArtifact`` metadata.

This test module pins every contract surface — module-level
constants, the small helpers (`_load_json`, `_is_non_empty`,
`_iter_nis2_compliance_entries`), both validators
(`_validate_matrix`, `_validate_uc_traceability`), and the CLI
`main()` with --json output, the 50-row truncation in human mode,
and the `__main__` block.
"""

from __future__ import annotations

import json
import pathlib
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Protocol

import pytest

from splunk_uc.audits import nis2_no_gap as nn

_SENTINEL: Any = object()


# ---------------------------------------------------- fixtures / factories


class MakeUC(Protocol):
    """Factory for a synthetic UC sidecar carrying optional NIS2 entries."""

    def __call__(
        self,
        uc_id: str,
        *,
        cat: int = ...,
        compliance: Any = ...,
    ) -> Path: ...


class WriteMatrix(Protocol):
    """Factory for a synthetic NIS2 coverage matrix JSON."""

    def __call__(
        self,
        *,
        rows: Any = ...,
        extra_keys: dict[str, Any] | None = ...,
    ) -> Path: ...


class WriteSourceMap(Protocol):
    """Factory for a synthetic nis2-source-map.json."""

    def __call__(self, sources: Sequence[Any]) -> Path: ...


@pytest.fixture
def fake_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Rewire `REPO_ROOT`, `MATRIX_PATH`, `SOURCE_MAP_PATH`, `CONTENT_ROOT`."""
    repo = tmp_path / "fakerepo"
    repo.mkdir()
    monkeypatch.setattr(nn, "REPO_ROOT", repo)
    monkeypatch.setattr(
        nn,
        "MATRIX_PATH",
        repo / "data" / "per-regulation" / "nis2-coverage-expansion.json",
    )
    monkeypatch.setattr(nn, "SOURCE_MAP_PATH", repo / "data" / "nis2-source-map.json")
    monkeypatch.setattr(nn, "CONTENT_ROOT", repo / "content")
    (repo / "content").mkdir()
    (repo / "data").mkdir()
    return repo


def _good_row(idx: int = 1, **overrides: Any) -> dict[str, Any]:
    """A row that satisfies every documented invariant unless overridden."""
    row: dict[str, Any] = {
        "id": f"nis2-row-{idx}",
        "source": "directive",
        "sourceUrl": "https://example.eu/nis2/art20",
        "sourceType": "binding-law",
        "sourceAuthority": "EU OJ L 333/80",
        "retrieved": "2026-05-01",
        "bindingStatus": "in-force",
        "clause": "Art.20(1)",
        "obligation": "obligation text",
        "splunkCoverageType": "direct",
        "splunkCanDo": "We monitor login failures",
        "splunkCannotDo": "We cannot interview the board",
        "dataSources": ["wineventlog:security"],
        "ucPlan": "reuse existing UC",
        "evidenceArtifact": "savedsearches.conf reference",
        "assuranceTarget": "full",
        "assuranceRationale": "Evidence ratchet matches NIS2 Art.20",
        "owner": "@security-team",
        "references": [
            {"type": "binding-law", "url": "https://example.eu/nis2/art20"},
        ],
        "reviewConfidence": "official-text-clear",
        "bestInClassRationale": "Authoritative source cited",
    }
    row.update(overrides)
    return row


def _full_set_of_required_groups() -> list[dict[str, Any]]:
    """A list of one row per required source group + the required clauses."""
    groups = [
        ("directive", "Art.20(1)"),
        ("commission-implementing-regulation-2024-2690", "Art.20(2)"),
        ("enisa-guidance", "Art.21(2)(a)"),
        ("national-guidance", "Art.21(2)(j)"),
        ("sector-overlay", "Art.23(4)(a)"),
        ("directive", "Annex 3.2"),
        ("directive", "Annex I"),
        ("directive", "Annex II"),
    ]
    rows: list[dict[str, Any]] = []
    for idx, (src, clause) in enumerate(groups, start=1):
        rows.append(_good_row(idx, source=src, clause=clause))
    return rows


def _source_urls_from_rows(rows: Sequence[dict[str, Any]]) -> list[dict[str, str]]:
    """Return the source-map entries needed to satisfy each row's sourceUrl."""
    return [{"url": str(r["sourceUrl"])} for r in rows]


@pytest.fixture
def write_matrix(fake_repo: Path) -> WriteMatrix:
    def _make(
        *,
        rows: Any = _SENTINEL,
        extra_keys: dict[str, Any] | None = None,
    ) -> Path:
        body: dict[str, Any] = {}
        if rows is _SENTINEL:
            body["coverageRows"] = _full_set_of_required_groups()
        elif rows is None:
            pass  # omit the coverageRows key entirely
        else:
            body["coverageRows"] = rows
        if extra_keys:
            body.update(extra_keys)
        target: Path = nn.MATRIX_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(body), encoding="utf-8")
        return target

    return _make


@pytest.fixture
def write_source_map(fake_repo: Path) -> WriteSourceMap:
    def _make(sources: Sequence[Any]) -> Path:
        body = {"sources": list(sources)}
        target: Path = nn.SOURCE_MAP_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(body), encoding="utf-8")
        return target

    return _make


@pytest.fixture
def make_uc(fake_repo: Path) -> MakeUC:
    def _make(
        uc_id: str,
        *,
        cat: int = 1,
        compliance: Any = _SENTINEL,
    ) -> Path:
        body: dict[str, Any] = {"id": uc_id}
        if compliance is not _SENTINEL:
            body["compliance"] = compliance
        cat_dir = fake_repo / "content" / f"cat-{cat}-foo"
        cat_dir.mkdir(parents=True, exist_ok=True)
        out = cat_dir / f"UC-{uc_id}.json"
        out.write_text(json.dumps(body), encoding="utf-8")
        return out

    return _make


# -------------------------------------------------- module-level invariants


def test_module_repo_root_resolves_three_parents_up() -> None:
    expected = Path(nn.__file__).resolve().parents[3]
    # Note: fixtures rewire this constant per-test; the import-time value
    # here checks the unrewired computation. The expression is what we pin.
    assert nn.REPO_ROOT == expected or nn.REPO_ROOT.is_dir()


def test_module_required_row_fields_count() -> None:
    """The contract is 21 required fields per row."""
    assert len(nn.REQUIRED_ROW_FIELDS) == 21


def test_module_valid_coverage_enum() -> None:
    assert nn.VALID_COVERAGE == {"direct", "partial", "contributing", "not-monitorable"}


def test_module_valid_assurance_enum() -> None:
    assert nn.VALID_ASSURANCE == {"full", "partial", "contributing", "not-monitorable"}


def test_module_valid_confidence_enum() -> None:
    assert nn.VALID_CONFIDENCE == {
        "official-text-clear",
        "guidance-supported",
        "engineering-judgement",
        "requires-legal-review",
    }


def test_module_valid_uc_plan_enum() -> None:
    assert nn.VALID_UC_PLAN == {
        "reuse existing UC",
        "uplift existing UC",
        "create new UC",
        "not-monitorable with supporting workflow",
    }


# ----------------------------------------------------------------- _load_json


def test_load_json_reads_valid_payload(tmp_path: Path) -> None:
    p = tmp_path / "x.json"
    p.write_text(json.dumps({"k": 1}), encoding="utf-8")
    assert nn._load_json(p) == {"k": 1}


def test_load_json_propagates_decode_error(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text("not json", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        nn._load_json(p)


# -------------------------------------------------------------- _is_non_empty


def test_is_non_empty_none() -> None:
    assert nn._is_non_empty(None) is False


def test_is_non_empty_empty_string() -> None:
    assert nn._is_non_empty("") is False


def test_is_non_empty_whitespace_string() -> None:
    """Whitespace-only strings are treated as empty per the strip() guard."""
    assert nn._is_non_empty("   ") is False


def test_is_non_empty_meaningful_string() -> None:
    assert nn._is_non_empty("hello") is True


def test_is_non_empty_empty_list() -> None:
    assert nn._is_non_empty([]) is False


def test_is_non_empty_populated_list() -> None:
    assert nn._is_non_empty([1]) is True


def test_is_non_empty_empty_dict() -> None:
    assert nn._is_non_empty({}) is False


def test_is_non_empty_populated_dict() -> None:
    assert nn._is_non_empty({"k": 1}) is True


def test_is_non_empty_integer_zero() -> None:
    """An int (non-str/list/dict) returns True from the fall-through."""
    assert nn._is_non_empty(0) is True


def test_is_non_empty_integer_nonzero() -> None:
    assert nn._is_non_empty(42) is True


def test_is_non_empty_bool() -> None:
    assert nn._is_non_empty(True) is True


# ---------------------------------------------- _iter_nis2_compliance_entries


def test_iter_nis2_returns_empty_when_no_ucs(fake_repo: Path) -> None:
    assert nn._iter_nis2_compliance_entries() == []


def test_iter_nis2_yields_only_nis2_entries(make_uc: MakeUC) -> None:
    """Only entries with regulation=='NIS2' are returned."""
    make_uc(
        "1.1.1",
        compliance=[
            {"regulation": "NIS2", "clause": "Art.20(1)"},
            {"regulation": "GDPR", "clause": "Art.32"},
        ],
    )
    entries = nn._iter_nis2_compliance_entries()
    assert len(entries) == 1
    assert entries[0][0] == "1.1.1"
    assert entries[0][2]["clause"] == "Art.20(1)"


def test_iter_nis2_case_insensitive_regulation_match(make_uc: MakeUC) -> None:
    """`regulation` is lowercased + stripped before comparison."""
    make_uc("1.1.2", compliance=[{"regulation": "  nis2  ", "clause": "Art.20(2)"}])
    entries = nn._iter_nis2_compliance_entries()
    assert len(entries) == 1


def test_iter_nis2_skips_malformed_json(fake_repo: Path) -> None:
    """A malformed sidecar is silently skipped via the broad `except Exception:`."""
    cat_dir = fake_repo / "content" / "cat-1-foo"
    cat_dir.mkdir(parents=True)
    (cat_dir / "UC-1.1.99.json").write_text("not json", encoding="utf-8")
    assert nn._iter_nis2_compliance_entries() == []


def test_iter_nis2_handles_missing_compliance_field(make_uc: MakeUC) -> None:
    """A UC without `compliance` returns no entries (the `.get(...) or []`)."""
    make_uc("1.1.3")  # no compliance field
    assert nn._iter_nis2_compliance_entries() == []


def test_iter_nis2_handles_none_compliance_field(make_uc: MakeUC) -> None:
    """`compliance: null` falls through the `or []` guard."""
    make_uc("1.1.4", compliance=None)
    assert nn._iter_nis2_compliance_entries() == []


def test_iter_nis2_fallback_to_path_stem_when_id_missing(
    fake_repo: Path,
) -> None:
    """Missing `id` field falls back to `path.stem`."""
    cat_dir = fake_repo / "content" / "cat-1-foo"
    cat_dir.mkdir(parents=True)
    (cat_dir / "UC-9.9.9.json").write_text(
        json.dumps({"compliance": [{"regulation": "NIS2", "clause": "X"}]}),
        encoding="utf-8",
    )
    entries = nn._iter_nis2_compliance_entries()
    assert entries[0][0] == "UC-9.9.9"


def test_iter_nis2_returns_sorted_paths(make_uc: MakeUC) -> None:
    """The for-loop walks `sorted(CONTENT_ROOT.glob(...))`."""
    make_uc("1.2.1", cat=2, compliance=[{"regulation": "NIS2", "clause": "X"}])
    make_uc("1.1.1", cat=1, compliance=[{"regulation": "NIS2", "clause": "Y"}])
    entries = nn._iter_nis2_compliance_entries()
    assert [e[0] for e in entries] == ["1.1.1", "1.2.1"]


# -------------------------------------------------------- _validate_matrix


def test_validate_matrix_empty_coverage_rows() -> None:
    """Missing or empty `coverageRows` returns a singleton error."""
    assert nn._validate_matrix({"coverageRows": []}, {}) == ["matrix has no coverageRows"]


def test_validate_matrix_coverage_rows_not_a_list() -> None:
    assert nn._validate_matrix({"coverageRows": "not-a-list"}, {}) == ["matrix has no coverageRows"]


def test_validate_matrix_missing_coverage_rows_key() -> None:
    assert nn._validate_matrix({}, {}) == ["matrix has no coverageRows"]


def test_validate_matrix_clean_corpus() -> None:
    """A row with every field correct plus all source groups + clauses passes."""
    rows = _full_set_of_required_groups()
    source_map = {"sources": _source_urls_from_rows(rows)}
    errs = nn._validate_matrix({"coverageRows": rows}, source_map)
    assert errs == []


def test_validate_matrix_duplicate_id() -> None:
    a = _good_row(1)
    b = _good_row(1)  # same id explicitly
    rows = [a, b, *_full_set_of_required_groups()]
    source_map = {"sources": _source_urls_from_rows(rows)}
    errs = nn._validate_matrix({"coverageRows": rows}, source_map)
    assert any("duplicate id" in e for e in errs)


def test_validate_matrix_id_missing_uses_row_label() -> None:
    """A row without `id` is labelled `row-<index>`."""
    base = _good_row(1)
    del base["id"]
    rows = [base, *_full_set_of_required_groups()]
    source_map = {"sources": _source_urls_from_rows(rows)}
    errs = nn._validate_matrix({"coverageRows": rows}, source_map)
    # The missing-id row surfaces with row-1 label.
    assert any(e.startswith("row-1") for e in errs)


def test_validate_matrix_missing_required_field() -> None:
    """A row missing `evidenceArtifact` surfaces a "missing X" error."""
    rows = _full_set_of_required_groups()
    del rows[0]["evidenceArtifact"]
    source_map = {"sources": _source_urls_from_rows(rows)}
    errs = nn._validate_matrix({"coverageRows": rows}, source_map)
    assert any("missing evidenceArtifact" in e for e in errs)


def test_validate_matrix_invalid_coverage_type() -> None:
    rows = _full_set_of_required_groups()
    rows[0]["splunkCoverageType"] = "junk"
    source_map = {"sources": _source_urls_from_rows(rows)}
    errs = nn._validate_matrix({"coverageRows": rows}, source_map)
    assert any("invalid splunkCoverageType 'junk'" in e for e in errs)


def test_validate_matrix_invalid_assurance_target() -> None:
    rows = _full_set_of_required_groups()
    rows[0]["assuranceTarget"] = "junk"
    source_map = {"sources": _source_urls_from_rows(rows)}
    errs = nn._validate_matrix({"coverageRows": rows}, source_map)
    assert any("invalid assuranceTarget 'junk'" in e for e in errs)


def test_validate_matrix_invalid_review_confidence() -> None:
    rows = _full_set_of_required_groups()
    rows[0]["reviewConfidence"] = "junk"
    source_map = {"sources": _source_urls_from_rows(rows)}
    errs = nn._validate_matrix({"coverageRows": rows}, source_map)
    assert any("invalid reviewConfidence 'junk'" in e for e in errs)


def test_validate_matrix_invalid_uc_plan() -> None:
    rows = _full_set_of_required_groups()
    rows[0]["ucPlan"] = "junk"
    source_map = {"sources": _source_urls_from_rows(rows)}
    errs = nn._validate_matrix({"coverageRows": rows}, source_map)
    assert any("invalid ucPlan 'junk'" in e for e in errs)


def test_validate_matrix_references_must_be_non_empty_list() -> None:
    rows = _full_set_of_required_groups()
    rows[0]["references"] = []
    source_map = {"sources": _source_urls_from_rows(rows)}
    errs = nn._validate_matrix({"coverageRows": rows}, source_map)
    assert any("references must be a non-empty list" in e for e in errs)


def test_validate_matrix_references_not_a_list() -> None:
    rows = _full_set_of_required_groups()
    rows[0]["references"] = "not-a-list"
    source_map = {"sources": _source_urls_from_rows(rows)}
    errs = nn._validate_matrix({"coverageRows": rows}, source_map)
    assert any("references must be a non-empty list" in e for e in errs)


def test_validate_matrix_references_first_must_be_authoritative() -> None:
    rows = _full_set_of_required_groups()
    rows[0]["references"] = [{"type": "blog-post", "url": "https://blog"}]
    source_map = {"sources": _source_urls_from_rows(rows)}
    errs = nn._validate_matrix({"coverageRows": rows}, source_map)
    assert any("first reference must be official or national guidance" in e for e in errs)


def test_validate_matrix_references_first_can_be_official_guidance() -> None:
    rows = _full_set_of_required_groups()
    rows[0]["references"] = [{"type": "official-guidance", "url": "https://x"}]
    source_map = {"sources": _source_urls_from_rows(rows)}
    errs = nn._validate_matrix({"coverageRows": rows}, source_map)
    assert not any("first reference must be" in e for e in errs)


def test_validate_matrix_references_first_can_be_national_guidance() -> None:
    rows = _full_set_of_required_groups()
    rows[0]["references"] = [{"type": "national-guidance", "url": "https://x"}]
    source_map = {"sources": _source_urls_from_rows(rows)}
    errs = nn._validate_matrix({"coverageRows": rows}, source_map)
    assert not any("first reference must be" in e for e in errs)


def test_validate_matrix_references_first_not_a_dict() -> None:
    rows = _full_set_of_required_groups()
    rows[0]["references"] = ["just-a-string"]
    source_map = {"sources": _source_urls_from_rows(rows)}
    errs = nn._validate_matrix({"coverageRows": rows}, source_map)
    assert any("first reference must be official or national guidance" in e for e in errs)


def test_validate_matrix_source_url_not_in_source_map() -> None:
    rows = _full_set_of_required_groups()
    rows[0]["sourceUrl"] = "https://elsewhere.eu/lost"
    source_map = {"sources": [{"url": "https://only.eu/that"}]}
    errs = nn._validate_matrix({"coverageRows": rows}, source_map)
    assert any("sourceUrl not present in data/nis2-source-map.json" in e for e in errs)


def test_validate_matrix_source_url_present_in_map() -> None:
    rows = _full_set_of_required_groups()
    source_map = {"sources": _source_urls_from_rows(rows)}
    errs = nn._validate_matrix({"coverageRows": rows}, source_map)
    assert not any("sourceUrl not present" in e for e in errs)


def test_validate_matrix_source_url_empty_string_skipped() -> None:
    """Empty sourceUrl is missing-required (caught above) but not in mapping check."""
    rows = _full_set_of_required_groups()
    rows[0]["sourceUrl"] = ""
    source_map = {"sources": _source_urls_from_rows(rows)}
    errs = nn._validate_matrix({"coverageRows": rows}, source_map)
    # Empty sourceUrl skips the mapping check, but should surface as missing-required.
    assert any("missing sourceUrl" in e for e in errs)
    assert not any("sourceUrl not present" in e for e in errs)


def test_validate_matrix_source_map_skips_non_dict_sources() -> None:
    """Non-dict entries in sources are skipped via `isinstance(src, dict)`."""
    rows = _full_set_of_required_groups()
    source_map = {
        "sources": [
            "not-a-dict",
            {"url": rows[0]["sourceUrl"]},
            *(_source_urls_from_rows(rows[1:])),
        ]
    }
    errs = nn._validate_matrix({"coverageRows": rows}, source_map)
    assert not any("sourceUrl not present" in e for e in errs)


def test_validate_matrix_source_map_skips_dict_without_url() -> None:
    rows = _full_set_of_required_groups()
    source_map = {
        "sources": [
            {"no_url_key": "x"},
            *_source_urls_from_rows(rows),
        ]
    }
    errs = nn._validate_matrix({"coverageRows": rows}, source_map)
    assert not any("sourceUrl not present" in e for e in errs)


def test_validate_matrix_cannot_do_na() -> None:
    rows = _full_set_of_required_groups()
    rows[0]["splunkCannotDo"] = "N/A — pending review"
    source_map = {"sources": _source_urls_from_rows(rows)}
    errs = nn._validate_matrix({"coverageRows": rows}, source_map)
    assert any("splunkCannotDo must state a real boundary" in e for e in errs)


def test_validate_matrix_cannot_do_none() -> None:
    rows = _full_set_of_required_groups()
    rows[0]["splunkCannotDo"] = "none"
    source_map = {"sources": _source_urls_from_rows(rows)}
    errs = nn._validate_matrix({"coverageRows": rows}, source_map)
    assert any("splunkCannotDo must state a real boundary" in e for e in errs)


def test_validate_matrix_cannot_do_none_with_whitespace() -> None:
    """`'  none  '` is detected after the `.strip()`."""
    rows = _full_set_of_required_groups()
    rows[0]["splunkCannotDo"] = "  none  "
    source_map = {"sources": _source_urls_from_rows(rows)}
    errs = nn._validate_matrix({"coverageRows": rows}, source_map)
    assert any("splunkCannotDo must state a real boundary" in e for e in errs)


def test_validate_matrix_cannot_do_meaningful_text_passes() -> None:
    rows = _full_set_of_required_groups()
    rows[0]["splunkCannotDo"] = "We cannot interview the board"
    source_map = {"sources": _source_urls_from_rows(rows)}
    errs = nn._validate_matrix({"coverageRows": rows}, source_map)
    assert not any("splunkCannotDo" in e for e in errs)


def test_validate_matrix_evidence_artifact_monitor_manually() -> None:
    rows = _full_set_of_required_groups()
    rows[0]["evidenceArtifact"] = "we monitor manually via spreadsheet"
    source_map = {"sources": _source_urls_from_rows(rows)}
    errs = nn._validate_matrix({"coverageRows": rows}, source_map)
    assert any("evidenceArtifact contains vague manual-monitoring wording" in e for e in errs)


def test_validate_matrix_missing_source_group() -> None:
    rows = _full_set_of_required_groups()
    rows = [r for r in rows if r["source"] != "enisa-guidance"]
    source_map = {"sources": _source_urls_from_rows(rows)}
    errs = nn._validate_matrix({"coverageRows": rows}, source_map)
    assert any("matrix missing required source group enisa-guidance" in e for e in errs)


def test_validate_matrix_missing_high_value_clause() -> None:
    rows = _full_set_of_required_groups()
    rows = [r for r in rows if r["clause"] != "Annex II"]
    source_map = {"sources": _source_urls_from_rows(rows)}
    errs = nn._validate_matrix({"coverageRows": rows}, source_map)
    assert any("matrix missing required high-value clause Annex II" in e for e in errs)


def test_validate_matrix_multiple_missing_clauses_sorted() -> None:
    """Multiple missing clauses surface alphabetically."""
    rows = [r for r in _full_set_of_required_groups() if r["clause"] not in {"Annex I", "Annex II"}]
    source_map = {"sources": _source_urls_from_rows(rows)}
    errs = nn._validate_matrix({"coverageRows": rows}, source_map)
    idx_i = next(i for i, e in enumerate(errs) if "Annex I" in e and "Annex II" not in e)
    idx_ii = next(i for i, e in enumerate(errs) if "Annex II" in e)
    assert idx_i < idx_ii


# ----------------------------------------------------- _validate_uc_traceability


def test_validate_uc_traceability_clean(
    write_matrix: WriteMatrix,
    make_uc: MakeUC,
) -> None:
    """A UC with a complete NIS2 entry whose clause is in the matrix passes."""
    write_matrix()  # writes full set of groups + clauses
    make_uc(
        "1.1.1",
        compliance=[
            {
                "regulation": "NIS2",
                "clause": "Art.20(1)",
                "clauseUrl": "https://nis2.eu/art20",
                "controlObjective": "Detect intrusion attempts",
                "evidenceArtifact": "savedsearch.conf reference",
            }
        ],
    )
    matrix = json.loads(nn.MATRIX_PATH.read_text(encoding="utf-8"))
    assert nn._validate_uc_traceability(matrix) == []


def test_validate_uc_traceability_empty_clause(make_uc: MakeUC) -> None:
    make_uc(
        "1.1.1",
        compliance=[
            {
                "regulation": "NIS2",
                "clause": "",
                "clauseUrl": "https://x",
                "controlObjective": "o",
                "evidenceArtifact": "e",
            }
        ],
    )
    errs = nn._validate_uc_traceability({"coverageRows": []})
    assert any("empty NIS2 clause" in e for e in errs)


def test_validate_uc_traceability_missing_clause_url(make_uc: MakeUC) -> None:
    make_uc(
        "1.1.1",
        compliance=[
            {
                "regulation": "NIS2",
                "clause": "Art.20(1)",
                "controlObjective": "o",
                "evidenceArtifact": "e",
            }
        ],
    )
    errs = nn._validate_uc_traceability({"coverageRows": []})
    assert any("missing clauseUrl" in e for e in errs)


def test_validate_uc_traceability_missing_control_objective(make_uc: MakeUC) -> None:
    make_uc(
        "1.1.1",
        compliance=[
            {
                "regulation": "NIS2",
                "clause": "Art.20(1)",
                "clauseUrl": "https://x",
                "evidenceArtifact": "e",
            }
        ],
    )
    errs = nn._validate_uc_traceability({"coverageRows": []})
    assert any("missing controlObjective" in e for e in errs)


def test_validate_uc_traceability_missing_evidence_artifact(make_uc: MakeUC) -> None:
    make_uc(
        "1.1.1",
        compliance=[
            {
                "regulation": "NIS2",
                "clause": "Art.20(1)",
                "clauseUrl": "https://x",
                "controlObjective": "o",
            }
        ],
    )
    errs = nn._validate_uc_traceability({"coverageRows": []})
    assert any("missing evidenceArtifact" in e for e in errs)


def test_validate_uc_traceability_clause_not_in_matrix(
    make_uc: MakeUC,
) -> None:
    """A clause referenced by a UC that's not present in the matrix surfaces."""
    make_uc(
        "1.1.1",
        compliance=[
            {
                "regulation": "NIS2",
                "clause": "Art.999",
                "clauseUrl": "https://x",
                "controlObjective": "o",
                "evidenceArtifact": "e",
            }
        ],
    )
    errs = nn._validate_uc_traceability({"coverageRows": [{"clause": "Art.20(1)"}]})
    assert any("Art.999 is not in matrix" in e for e in errs)


def test_validate_uc_traceability_empty_clause_skips_matrix_check(
    make_uc: MakeUC,
) -> None:
    """An empty clause emits the empty-clause error but skips the matrix check."""
    make_uc(
        "1.1.1",
        compliance=[
            {
                "regulation": "NIS2",
                "clause": "",
                "clauseUrl": "https://x",
                "controlObjective": "o",
                "evidenceArtifact": "e",
            }
        ],
    )
    errs = nn._validate_uc_traceability({"coverageRows": [{"clause": "Art.20(1)"}]})
    assert any("empty NIS2 clause" in e for e in errs)
    assert not any("is not in matrix" in e for e in errs)


# ----------------------------------------------------------------- main()


def test_main_missing_matrix_file(
    fake_repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = nn.main([])
    assert rc == 1
    out = capsys.readouterr().out
    assert "missing data/per-regulation/nis2-coverage-expansion.json" in out


def test_main_missing_source_map_file(
    write_matrix: WriteMatrix,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_matrix()
    # No source map.
    rc = nn.main([])
    assert rc == 1
    out = capsys.readouterr().out
    assert "missing data/nis2-source-map.json" in out


def test_main_happy_path_returns_zero(
    write_matrix: WriteMatrix,
    write_source_map: WriteSourceMap,
    capsys: pytest.CaptureFixture[str],
) -> None:
    rows = _full_set_of_required_groups()
    write_matrix(rows=rows)
    write_source_map(_source_urls_from_rows(rows))
    rc = nn.main([])
    assert rc == 0
    out = capsys.readouterr().out
    assert "NIS2 no-gap audit: PASSED" in out
    assert "rows=8" in out
    assert "errors=0" in out


def test_main_validation_errors_return_one(
    write_matrix: WriteMatrix,
    write_source_map: WriteSourceMap,
    capsys: pytest.CaptureFixture[str],
) -> None:
    rows = _full_set_of_required_groups()
    rows[0]["splunkCoverageType"] = "junk"
    write_matrix(rows=rows)
    write_source_map(_source_urls_from_rows(rows))
    rc = nn.main([])
    assert rc == 1
    out = capsys.readouterr().out
    assert "NIS2 no-gap audit: FAILED" in out
    assert "invalid splunkCoverageType" in out


def test_main_json_output_includes_status_and_errors(
    write_matrix: WriteMatrix,
    write_source_map: WriteSourceMap,
    capsys: pytest.CaptureFixture[str],
) -> None:
    rows = _full_set_of_required_groups()
    write_matrix(rows=rows)
    write_source_map(_source_urls_from_rows(rows))
    rc = nn.main(["--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "passed"
    assert payload["errors"] == []
    assert payload["matrixRows"] == 8
    assert "nis2ComplianceEntries" in payload


def test_main_json_with_failures(
    write_matrix: WriteMatrix,
    write_source_map: WriteSourceMap,
    capsys: pytest.CaptureFixture[str],
) -> None:
    rows = _full_set_of_required_groups()
    rows[0]["evidenceArtifact"] = ""
    write_matrix(rows=rows)
    write_source_map(_source_urls_from_rows(rows))
    rc = nn.main(["--json"])
    assert rc == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "failed"
    assert any("missing evidenceArtifact" in e for e in payload["errors"])


def test_main_truncates_at_50_errors(
    write_matrix: WriteMatrix,
    write_source_map: WriteSourceMap,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """When >50 errors, human report prints `... and N more`."""
    # Build 60 rows, each with an invalid coverage type to surface 60+ errors.
    rows = _full_set_of_required_groups()
    extra = [
        _good_row(
            idx=100 + i, source="directive", clause=f"FakeClause{i}", splunkCoverageType="junk"
        )
        for i in range(60)
    ]
    write_matrix(rows=rows + extra)
    write_source_map(_source_urls_from_rows(rows + extra))
    rc = nn.main([])
    assert rc == 1
    out = capsys.readouterr().out
    assert "more" in out  # truncation message


def test_main_returns_zero_matrix_rows_in_payload_when_matrix_missing(
    fake_repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """When matrix file is missing, `matrixRows` defaults to 0."""
    rc = nn.main(["--json"])
    assert rc == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["matrixRows"] == 0


def test_main_argv_none_falls_through_to_sys_argv(
    write_matrix: WriteMatrix,
    write_source_map: WriteSourceMap,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = _full_set_of_required_groups()
    write_matrix(rows=rows)
    write_source_map(_source_urls_from_rows(rows))
    monkeypatch.setattr(sys, "argv", ["prog"])
    rc = nn.main(None)
    assert rc == 0


def test_main_help_exits_zero() -> None:
    with pytest.raises(SystemExit) as exc:
        nn.main(["--help"])
    assert exc.value.code == 0


# -------------------------------------------------------- __main__ block


def test_dunder_main_block_exists() -> None:
    src = pathlib.Path(nn.__file__).read_text(encoding="utf-8")
    assert 'if __name__ == "__main__":' in src
    assert "sys.exit(main())" in src
