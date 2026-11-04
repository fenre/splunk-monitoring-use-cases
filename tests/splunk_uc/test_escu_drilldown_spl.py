"""CI gate: a UC search must not be the ESCU risk drill-down."""

from __future__ import annotations

from splunk_uc.audits import escu_drilldown_spl as audit

DRILLDOWN = (
    '| from datamodel Risk.All_Risk | search normalized_risk_object IN ("$user$") '
    "starthoursago=168 | stats count by normalized_risk_object"
)


def test_drilldown_in_spl_is_found() -> None:
    assert audit.drilldown_fields({"spl": DRILLDOWN}) == ["spl"]


def test_drilldown_in_variant_cimspl_is_found() -> None:
    uc = {"spl": "`cisco_asa` message_id=111008", "splVariants": [{"cimSpl": DRILLDOWN}]}
    assert audit.drilldown_fields(uc) == ["splVariants[0].cimSpl"]


def test_risk_datamodel_detection_is_not_a_drilldown() -> None:
    uc = {"spl": "| tstats count from datamodel=Risk.All_Risk by All_Risk.normalized_risk_object"}
    assert audit.drilldown_fields(uc) == []


def test_compare_reports_new_and_stale() -> None:
    hits = {"UC-10.1.1": ["spl"], "UC-10.1.2": ["spl"]}
    new, stale = audit.compare(hits, {"UC-10.1.2", "UC-10.1.3"})
    assert new == ["UC-10.1.1"]
    assert stale == ["UC-10.1.3"]


def test_catalogue_matches_backlog() -> None:
    new, stale = audit.compare(audit.collect(), audit.load_backlog())
    assert new == []
    assert stale == []
