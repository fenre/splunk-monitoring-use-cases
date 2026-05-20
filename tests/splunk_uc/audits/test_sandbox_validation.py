"""Tests for ``splunk_uc.audits.sandbox_validation``.

Coverage lift for the Phase 4.5c sandbox validation gate. The audit
classifies every UC fixture into one of six statuses (missing,
bad-json, malformed, empty, half-empty, populated), cross-checks
``assurance: full`` claims against fixture population, and writes a
deterministic JSON report.

The existing suite carried zero direct tests of this module (10.8%
coverage from incidental imports). This file walks every documented
status path through ``_classify_fixture``, then end-to-end through
``_collect_records`` and ``main()`` with a hermetic synthetic
catalogue rooted at ``tmp_path``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from splunk_uc.audits import sandbox_validation as audit


# --------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------- #


def _write_fixture(path: Path, payload: dict | list | str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
    else:
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _phase2(pos: int = 1, neg: int = 1) -> dict:
    return {
        "uc_id": "1.1.1",
        "description": "phase2 fixture",
        "events_positive": [{"_raw": "good"} for _ in range(pos)],
        "events_negative": [{"_raw": "bad"} for _ in range(neg)],
    }


def _phase3(pos: int = 1, neg: int = 1) -> dict:
    return {
        "uc": "UC-1.1.1",
        "positive": [
            {"evidence_id": f"E{i}", "owner": "x", "status": "complete"}
            for i in range(pos)
        ],
        "negative": [
            {"evidence_id": f"E{i}", "owner": "x", "status": "gap"}
            for i in range(neg)
        ],
    }


def _legacy(pos: int = 1, neg: int = 1) -> dict:
    return {
        "description": "legacy fixture",
        "positiveCase": {
            "events": [{"_raw": "good"} for _ in range(pos)],
            "expectedFire": True,
        },
        "negativeCase": {
            "events": [{"_raw": "bad"} for _ in range(neg)],
            "expectedFire": False,
        },
    }


# --------------------------------------------------------------------- #
# _classify_fixture
# --------------------------------------------------------------------- #


def test_classify_missing_returns_missing(tmp_path: Path) -> None:
    status, shape, pos, neg, issues = audit._classify_fixture(
        tmp_path / "nope.json"
    )
    assert (status, shape, pos, neg, issues) == (
        audit.STATUS_MISSING,
        None,
        0,
        0,
        [],
    )


def test_classify_bad_json_returns_bad_json(tmp_path: Path) -> None:
    p = _write_fixture(tmp_path / "x.json", "{ not valid")
    status, shape, _, _, issues = audit._classify_fixture(p)
    assert status == audit.STATUS_BAD_JSON
    assert shape is None
    assert any("parse error" in i for i in issues)


def test_classify_non_object_top_level_is_malformed(tmp_path: Path) -> None:
    p = _write_fixture(tmp_path / "x.json", [1, 2, 3])
    status, shape, _, _, issues = audit._classify_fixture(p)
    assert status == audit.STATUS_MALFORMED
    assert shape is None
    assert any("expected object" in i for i in issues)


def test_classify_phase2_populated(tmp_path: Path) -> None:
    p = _write_fixture(tmp_path / "x.json", _phase2(2, 3))
    status, shape, pos, neg, issues = audit._classify_fixture(p)
    assert (status, shape, pos, neg, issues) == (
        audit.STATUS_POPULATED,
        audit.FIXTURE_SHAPE_PHASE2,
        2,
        3,
        [],
    )


def test_classify_phase2_empty(tmp_path: Path) -> None:
    p = _write_fixture(tmp_path / "x.json", _phase2(0, 0))
    status, shape, pos, neg, _ = audit._classify_fixture(p)
    assert (status, shape, pos, neg) == (
        audit.STATUS_EMPTY,
        audit.FIXTURE_SHAPE_PHASE2,
        0,
        0,
    )


def test_classify_phase2_half_empty(tmp_path: Path) -> None:
    p = _write_fixture(tmp_path / "x.json", _phase2(0, 1))
    status, shape, pos, neg, _ = audit._classify_fixture(p)
    assert (status, shape, pos, neg) == (
        audit.STATUS_HALF_EMPTY,
        audit.FIXTURE_SHAPE_PHASE2,
        0,
        1,
    )


def test_classify_phase2_non_list_events_is_malformed(tmp_path: Path) -> None:
    payload = _phase2()
    payload["events_positive"] = "not-a-list"
    p = _write_fixture(tmp_path / "x.json", payload)
    status, shape, _, _, issues = audit._classify_fixture(p)
    assert status == audit.STATUS_MALFORMED
    assert shape == audit.FIXTURE_SHAPE_PHASE2
    assert any("'events_positive'" in i for i in issues)


def test_classify_phase2_non_list_events_negative_is_malformed(tmp_path: Path) -> None:
    """Mirror of the above for the negative axis (covers line 151
    of ``sandbox_validation.py``)."""

    payload = _phase2()
    payload["events_negative"] = "still-not-a-list"
    p = _write_fixture(tmp_path / "x.json", payload)
    status, shape, _, _, issues = audit._classify_fixture(p)
    assert status == audit.STATUS_MALFORMED
    assert shape == audit.FIXTURE_SHAPE_PHASE2
    assert any("'events_negative' is not a list" in i for i in issues)


def test_classify_phase3_populated(tmp_path: Path) -> None:
    p = _write_fixture(tmp_path / "x.json", _phase3(1, 1))
    status, shape, _, _, _ = audit._classify_fixture(p)
    assert (status, shape) == (
        audit.STATUS_POPULATED,
        audit.FIXTURE_SHAPE_PHASE3,
    )


def test_classify_phase3_non_list_evidence_is_malformed(tmp_path: Path) -> None:
    payload = _phase3()
    payload["negative"] = "not-a-list"
    p = _write_fixture(tmp_path / "x.json", payload)
    status, shape, _, _, issues = audit._classify_fixture(p)
    assert status == audit.STATUS_MALFORMED
    assert shape == audit.FIXTURE_SHAPE_PHASE3
    assert any("'negative'" in i for i in issues)


def test_classify_phase3_non_list_positive_is_malformed(tmp_path: Path) -> None:
    """Mirror of the above for the positive axis (covers line 169
    of ``sandbox_validation.py``)."""

    payload = _phase3()
    payload["positive"] = 42  # not a list
    p = _write_fixture(tmp_path / "x.json", payload)
    status, shape, _, _, issues = audit._classify_fixture(p)
    assert status == audit.STATUS_MALFORMED
    assert shape == audit.FIXTURE_SHAPE_PHASE3
    assert any("'positive' is not a list" in i for i in issues)


def test_classify_legacy_populated(tmp_path: Path) -> None:
    p = _write_fixture(tmp_path / "x.json", _legacy(1, 1))
    status, shape, _, _, _ = audit._classify_fixture(p)
    assert (status, shape) == (
        audit.STATUS_POPULATED,
        audit.FIXTURE_SHAPE_LEGACY,
    )


def test_classify_legacy_wrong_polarity_is_malformed(tmp_path: Path) -> None:
    payload = _legacy()
    payload["positiveCase"]["expectedFire"] = False
    p = _write_fixture(tmp_path / "x.json", payload)
    status, _, _, _, issues = audit._classify_fixture(p)
    assert status == audit.STATUS_MALFORMED
    assert any("positiveCase.expectedFire" in i for i in issues)


def test_classify_legacy_case_not_object_is_malformed(tmp_path: Path) -> None:
    payload = _legacy()
    payload["positiveCase"] = "string-instead-of-object"
    p = _write_fixture(tmp_path / "x.json", payload)
    status, _, _, _, issues = audit._classify_fixture(p)
    assert status == audit.STATUS_MALFORMED
    assert any("must be objects" in i for i in issues)


def test_classify_legacy_positive_case_events_not_list_is_malformed(
    tmp_path: Path,
) -> None:
    """``positiveCase.events`` must be a list (covers line 186 of
    ``sandbox_validation.py``)."""

    payload = _legacy()
    payload["positiveCase"]["events"] = "should-be-list"
    p = _write_fixture(tmp_path / "x.json", payload)
    status, _, _, _, issues = audit._classify_fixture(p)
    assert status == audit.STATUS_MALFORMED
    assert any("'positiveCase.events' is not a list" in i for i in issues)


def test_classify_legacy_negative_case_events_not_list_is_malformed(
    tmp_path: Path,
) -> None:
    """``negativeCase.events`` must be a list (covers line 188 of
    ``sandbox_validation.py``)."""

    payload = _legacy()
    payload["negativeCase"]["events"] = 0  # not a list
    p = _write_fixture(tmp_path / "x.json", payload)
    status, _, _, _, issues = audit._classify_fixture(p)
    assert status == audit.STATUS_MALFORMED
    assert any("'negativeCase.events' is not a list" in i for i in issues)


def test_classify_legacy_negative_case_wrong_polarity_is_malformed(
    tmp_path: Path,
) -> None:
    """A negativeCase whose ``expectedFire`` is anything but ``False``
    (e.g. ``True`` or ``None``) is rejected (covers line 194 of
    ``sandbox_validation.py``)."""

    payload = _legacy()
    payload["negativeCase"]["expectedFire"] = True  # wrong polarity
    p = _write_fixture(tmp_path / "x.json", payload)
    status, _, _, _, issues = audit._classify_fixture(p)
    assert status == audit.STATUS_MALFORMED
    assert any("'negativeCase.expectedFire' must be false" in i for i in issues)


def test_classify_unknown_shape_is_malformed(tmp_path: Path) -> None:
    p = _write_fixture(tmp_path / "x.json", {"random": "junk"})
    status, shape, _, _, issues = audit._classify_fixture(p)
    assert status == audit.STATUS_MALFORMED
    assert shape is None
    assert any("does not match any accepted shape" in i for i in issues)


# --------------------------------------------------------------------- #
# _collect_records — end-to-end with hermetic corpus
# --------------------------------------------------------------------- #


@pytest.fixture
def fake_corpus(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    """Build a temporary ``content/cat-99-fixture/`` + ``sample-data/``
    corpus and re-point the audit's module-level paths at it. Returns
    the ``content/cat-99-fixture`` directory so tests can drop UC
    sidecars in directly.
    """

    content = tmp_path / "content" / "cat-99-fixture"
    content.mkdir(parents=True)
    sample = tmp_path / "sample-data"
    sample.mkdir(parents=True)
    reports = tmp_path / "reports"
    reports.mkdir(parents=True)

    monkeypatch.setattr(audit, "REPO", tmp_path)
    monkeypatch.setattr(audit, "CONTENT", tmp_path / "content")
    monkeypatch.setattr(audit, "SAMPLE_DATA", sample)
    monkeypatch.setattr(
        audit, "REPORT_PATH", reports / "sandbox-validation.json"
    )
    return content


def _uc_sidecar(uc_id: str, **overrides) -> dict:
    base = {
        "id": uc_id,
        "title": f"UC {uc_id}",
        "controlTest": None,
        "compliance": [],
    }
    base.update(overrides)
    return base


def _write_uc(corpus_root: Path, uc_id: str, payload: dict) -> Path:
    p = corpus_root / f"UC-{uc_id}.json"
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return p


def test_collect_records_skips_uc_with_no_fixture_and_no_full(
    fake_corpus: Path,
) -> None:
    _write_uc(fake_corpus, "1.1.1", _uc_sidecar("1.1.1"))
    records, summary = audit._collect_records()
    assert records == []
    assert summary["total_ucs_examined"] == 1
    assert summary["with_fixture_ref"] == 0


def test_collect_records_emits_no_fixture_for_full_claim_without_fixture(
    fake_corpus: Path,
) -> None:
    sidecar = _uc_sidecar(
        "1.1.1",
        compliance=[
            {"regulation": "nis2", "clause": "21.1", "assurance": "full"}
        ],
    )
    _write_uc(fake_corpus, "1.1.1", sidecar)
    records, summary = audit._collect_records()

    assert len(records) == 1
    r = records[0]
    assert r["uc_id"] == "1.1.1"
    assert r["status"] == "no-fixture"
    assert r["full_assurance"] is True
    assert r["full_assurance_clauses"] == ["nis2:21.1"]
    assert summary["statuses"]["no-fixture"] == 1
    assert summary["full_assurance_with_gap"] == 1


def test_collect_records_populated_fixture_counted_and_clean(
    fake_corpus: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = audit.SAMPLE_DATA / "phase2" / "UC-1.1.1.json"
    _write_fixture(fixture, _phase2(2, 2))

    sidecar = _uc_sidecar(
        "1.1.1",
        controlTest={
            "fixtureRef": str(fixture.relative_to(audit.REPO)),
        },
    )
    _write_uc(fake_corpus, "1.1.1", sidecar)

    records, summary = audit._collect_records()
    assert len(records) == 1
    r = records[0]
    assert r["status"] == audit.STATUS_POPULATED
    assert r["shape"] == audit.FIXTURE_SHAPE_PHASE2
    assert r["pos_events"] == 2 and r["neg_events"] == 2
    assert summary["statuses"][audit.STATUS_POPULATED] == 1
    assert summary["hard_failures"] == 0


def test_collect_records_bad_json_fixture_counts_as_hard_failure(
    fake_corpus: Path,
) -> None:
    fixture = audit.SAMPLE_DATA / "bad.json"
    _write_fixture(fixture, "{ not json")

    sidecar = _uc_sidecar(
        "1.1.1",
        controlTest={"fixtureRef": str(fixture.relative_to(audit.REPO))},
    )
    _write_uc(fake_corpus, "1.1.1", sidecar)

    records, summary = audit._collect_records()
    assert summary["hard_failures"] == 1
    assert records[0]["status"] == audit.STATUS_BAD_JSON
    assert any("parse error" in i for i in records[0]["issues"])


def test_collect_records_full_assurance_on_empty_fixture_is_gap(
    fake_corpus: Path,
) -> None:
    fixture = audit.SAMPLE_DATA / "empty.json"
    _write_fixture(fixture, _phase2(0, 0))

    sidecar = _uc_sidecar(
        "1.1.1",
        controlTest={"fixtureRef": str(fixture.relative_to(audit.REPO))},
        compliance=[
            {"regulation": "iso27001", "clause": "A.5.1", "assurance": "full"}
        ],
    )
    _write_uc(fake_corpus, "1.1.1", sidecar)

    _, summary = audit._collect_records()
    assert summary["full_assurance_with_gap"] == 1
    assert summary["statuses"][audit.STATUS_EMPTY] == 1
    assert summary["hard_failures"] == 0


def test_collect_records_drops_broken_sidecar_silently(
    fake_corpus: Path,
) -> None:
    """Broken sidecars are owned by audit_compliance_mappings; this
    audit must skip them silently and continue."""

    (fake_corpus / "UC-1.1.1.json").write_text(
        "{ not valid json", encoding="utf-8"
    )
    _write_uc(fake_corpus, "1.1.2", _uc_sidecar("1.1.2"))

    records, summary = audit._collect_records()
    assert summary["total_ucs_examined"] == 1
    assert records == []


# --------------------------------------------------------------------- #
# main — CLI contract
# --------------------------------------------------------------------- #


def test_main_writes_report_and_exits_green_when_clean(
    fake_corpus: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _write_uc(fake_corpus, "1.1.1", _uc_sidecar("1.1.1"))
    rc = audit.main([])
    out = capsys.readouterr().out
    assert rc == 0
    assert "SANDBOX GATE: GREEN" in out
    assert audit.REPORT_PATH.exists()
    payload = json.loads(audit.REPORT_PATH.read_text(encoding="utf-8"))
    assert "records" in payload and "summary" in payload


def test_main_exits_red_on_hard_failure(
    fake_corpus: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fixture = audit.SAMPLE_DATA / "bad.json"
    _write_fixture(fixture, "{ not json")
    sidecar = _uc_sidecar(
        "1.1.1",
        controlTest={"fixtureRef": str(fixture.relative_to(audit.REPO))},
    )
    _write_uc(fake_corpus, "1.1.1", sidecar)

    rc = audit.main([])
    out = capsys.readouterr().out
    assert rc == 1
    assert "SANDBOX GATE: RED" in out
    assert "Hard failures:" in out


def test_main_check_mode_passes_when_committed_report_matches(
    fake_corpus: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _write_uc(fake_corpus, "1.1.1", _uc_sidecar("1.1.1"))

    # First run writes the report.
    assert audit.main([]) == 0
    capsys.readouterr()  # discard

    # --check on the same corpus must be a no-op exit-0.
    assert audit.main(["--check"]) == 0


def test_main_check_mode_fails_when_report_missing(
    fake_corpus: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _write_uc(fake_corpus, "1.1.1", _uc_sidecar("1.1.1"))
    # Report never written → --check should refuse.
    rc = audit.main(["--check"])
    err = capsys.readouterr().err
    assert rc == 1
    assert "does not exist" in err


def test_main_check_mode_fails_on_drift(
    fake_corpus: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _write_uc(fake_corpus, "1.1.1", _uc_sidecar("1.1.1"))
    audit.main([])  # write baseline
    capsys.readouterr()

    # Mutate corpus so the regenerated report differs.
    _write_uc(fake_corpus, "1.1.2", _uc_sidecar("1.1.2"))
    rc = audit.main(["--check"])
    err = capsys.readouterr().err
    assert rc == 1
    assert "out of date" in err
