"""Tests for the audit-cisco-coverage ratchet gate."""

from __future__ import annotations

from splunk_uc.audits import cisco_coverage as audit
from splunk_uc.generators import cisco_coverage as cov

PORTFOLIO = {
    "products": [
        {
            "slug": "duo",
            "name": "Duo",
            "family": "identity",
            "tier": 1,
            "equipmentModel": "cisco_duo",
            "capabilities": [
                {"id": "authentication", "name": "Auth", "observable": True},
                {"id": "telephony", "name": "Tel", "observable": True},
            ],
        },
        {
            "slug": "hyperfabric",
            "name": "Hyperfabric",
            "family": "network",
            "tier": 4,
            "equipmentModel": "cisco_hyperfabric",
            "capabilities": [],
        },
    ]
}


def _uc(uc_id, caps, models=("cisco_duo",)):
    return {"id": uc_id, "equipmentModels": list(models), "capabilities": list(caps), "cimModels": [], "hasCimSpl": False}


def _matrix(ucs):
    return cov.build_matrix(PORTFOLIO, ucs)


def test_clean_when_backlog_matches():
    m = _matrix([_uc("UC-1.1.1", ["duo.authentication"])])
    base = {"waivers": [], "pendingGaps": ["duo.telephony:uncovered"], "emptyProducts": ["hyperfabric"]}
    assert audit.evaluate(m, base) == []


def test_new_gap_fails():
    m = _matrix([_uc("UC-1.1.1", ["duo.authentication"])])
    errs = audit.evaluate(m, {"waivers": [], "pendingGaps": [], "emptyProducts": ["hyperfabric"]})
    assert any("new coverage gap `duo.telephony:uncovered`" in e for e in errs)


def test_closed_backlog_entry_fails_until_ratcheted():
    m = _matrix([_uc("UC-1.1.1", ["duo.authentication", "duo.telephony"])])
    errs = audit.evaluate(m, {"waivers": [], "pendingGaps": ["duo.telephony:uncovered"], "emptyProducts": ["hyperfabric"]})
    assert any("is closed" in e for e in errs)


def test_waiver_needs_reason_and_known_capability():
    m = _matrix([_uc("UC-1.1.1", ["duo.authentication"])])
    base = {
        "waivers": [{"capability": "duo.telephony", "reason": ""}, {"capability": "duo.nope", "reason": "x"}],
        "pendingGaps": [],
        "emptyProducts": ["hyperfabric"],
    }
    errs = audit.evaluate(m, base)
    assert any("has no reason" in e for e in errs)
    assert any("unknown capability `duo.nope`" in e for e in errs)
    assert not any("new coverage gap" in e for e in errs)


def test_unknown_capability_ref_fails():
    m = _matrix([_uc("UC-1.1.1", ["duo.authentication", "duo.bogus"])])
    errs = audit.evaluate(m, {"waivers": [], "pendingGaps": ["duo.telephony:uncovered"], "emptyProducts": ["hyperfabric"]})
    assert any("UC-1.1.1: unknown capability `duo.bogus`" in e for e in errs)


def test_empty_product_must_be_in_backlog():
    m = _matrix([_uc("UC-1.1.1", ["duo.authentication"])])
    errs = audit.evaluate(m, {"waivers": [], "pendingGaps": ["duo.telephony:uncovered"], "emptyProducts": []})
    assert any("product `hyperfabric` has no tagged use cases" in e for e in errs)


def test_write_baseline_keeps_waivers(tmp_path):
    m = _matrix([_uc("UC-1.1.1", ["duo.authentication"])])
    path = tmp_path / "b.json"
    notes = [{"product": "hyperfabric", "reason": "Index without a sourcetype."}]
    audit.write_baseline(
        m,
        {"waivers": [{"capability": "duo.telephony", "reason": "r"}], "emptyProductNotes": notes},
        path,
    )
    data = audit.load_baseline(path)
    assert data["waivers"] == [{"capability": "duo.telephony", "reason": "r"}]
    assert data["pendingGaps"] == []
    assert data["emptyProducts"] == ["hyperfabric"]
    assert data["emptyProductNotes"] == notes


def test_repository_baseline_passes():
    assert audit.main(["--check"]) == 0
