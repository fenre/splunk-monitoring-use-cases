"""Tests for ``splunk_uc.generators.cisco_coverage``."""

from __future__ import annotations

from typing import Any

from splunk_uc.generators import cisco_coverage as cc


def _portfolio() -> dict[str, Any]:
    return {
        "version": "test",
        "requestCoverageUrl": "https://example.invalid/issues/new",
        "products": [
            {
                "slug": "duo",
                "name": "Cisco Duo",
                "family": "identity",
                "tier": 1,
                "equipmentModel": "cisco_duo",
                "capabilityMap": "mapped",
                "capabilities": [
                    {"id": "authentication", "name": "Auth", "observable": True},
                    {"id": "telephony", "name": "Telephony", "observable": True},
                ],
            },
            {
                "slug": "secure_access",
                "name": "Cisco Secure Access",
                "family": "security",
                "tier": 1,
                "equipmentModel": "cisco_secure_access",
                "capabilityMap": "mapped",
                "capabilities": [
                    {"id": "dns_security", "name": "DNS", "observable": True, "cimModels": ["Network_Resolution"]},
                    {"id": "secure_web_gateway", "name": "SWG", "observable": True, "cimModels": ["Web"]},
                ],
            },
            {
                "slug": "hypershield",
                "name": "Cisco Hypershield",
                "family": "security",
                "tier": 3,
                "equipmentModel": "cisco_hypershield",
                "capabilityMap": "mapped",
                "capabilities": [
                    {"id": "management_history", "name": "History", "observable": False, "notObservableReason": "Not exported."},
                ],
            },
            {
                "slug": "ise",
                "name": "Cisco ISE",
                "family": "identity",
                "equipmentModel": "cisco_ise",
                "capabilityMap": "pending",
                "capabilities": [],
            },
        ],
    }


def _uc(uid: str, models: list[str], caps: list[str], cim: list[str] | None = None, cim_spl: bool = False) -> dict[str, Any]:
    return {"id": uid, "equipmentModels": models, "capabilities": caps, "cimModels": cim or [], "hasCimSpl": cim_spl}


def _cap(matrix: dict[str, Any], ref: str) -> dict[str, Any]:
    for prod in matrix["products"]:
        for cap in prod["capabilities"]:
            if cap["ref"] == ref:
                return cap
    raise KeyError(ref)


def test_statuses_cover_each_case() -> None:
    ucs = [
        _uc("UC-9.5.7", ["cisco_duo"], ["duo.authentication"]),
        _uc("UC-10.5.5", ["cisco_secure_access"], ["secure_access.dns_security"]),
        _uc("UC-10.5.1", ["cisco_secure_access"], ["secure_access.secure_web_gateway"], ["Web"], cim_spl=True),
    ]
    m = cc.build_matrix(_portfolio(), ucs)
    assert _cap(m, "duo.authentication")["status"] == cc.STATUS_COVERED
    assert _cap(m, "duo.telephony")["status"] == cc.STATUS_UNCOVERED
    assert _cap(m, "secure_access.dns_security")["status"] == cc.STATUS_CIM_GAP
    assert _cap(m, "secure_access.secure_web_gateway")["status"] == cc.STATUS_COVERED
    assert _cap(m, "secure_access.secure_web_gateway")["cimUseCases"] == ["UC-10.5.1"]
    assert _cap(m, "hypershield.management_history")["status"] == cc.STATUS_NOT_OBSERVABLE


def test_cim_requires_matching_model_and_cim_spl() -> None:
    ucs = [
        _uc("UC-1.1.1", [], ["secure_access.secure_web_gateway"], ["Web"], cim_spl=False),
        _uc("UC-1.1.2", [], ["secure_access.secure_web_gateway"], ["Network_Traffic"], cim_spl=True),
    ]
    cap = _cap(cc.build_matrix(_portfolio(), ucs), "secure_access.secure_web_gateway")
    assert cap["status"] == cc.STATUS_CIM_GAP
    assert cap["cimUseCases"] == []


def test_summary_counts_and_tagged_use_cases() -> None:
    ucs = [
        _uc("UC-9.5.14", ["cisco_duo"], ["duo.authentication"]),
        _uc("UC-9.5.7", ["cisco_duo"], []),
    ]
    m = cc.build_matrix(_portfolio(), ucs)
    s = m["summary"]
    assert s["products"] == 4
    assert s["productsWithUseCases"] == 1
    assert s["observableCapabilities"] == 4
    assert s["coveredCapabilities"] == 1
    assert s["cimCapabilities"] == 2
    duo = next(p for p in m["products"] if p["slug"] == "duo")
    assert duo["useCases"] == ["UC-9.5.7", "UC-9.5.14"]
    assert duo["uncovered"] == ["duo.telephony"]


def test_gaps_are_ordered_by_tier_and_skip_not_observable() -> None:
    m = cc.build_matrix(_portfolio(), [])
    refs = [g["capability"] for g in m["gaps"]]
    assert refs == [
        "duo.authentication",
        "duo.telephony",
        "secure_access.dns_security",
        "secure_access.secure_web_gateway",
    ]


def test_unknown_capability_refs_are_reported() -> None:
    m = cc.build_matrix(_portfolio(), [_uc("UC-1.2.3", [], ["duo.nonexistent", "duo.authentication"])])
    assert m["unknownCapabilityRefs"] == [{"useCase": "UC-1.2.3", "capability": "duo.nonexistent"}]
    assert _cap(m, "duo.authentication")["useCases"] == ["UC-1.2.3"]


def test_markdown_has_provenance_banner_and_gap_list() -> None:
    out = cc.render(_portfolio(), [])
    md = out["matrix.md"]
    assert md.startswith("<!-- Generated by `python -m splunk_uc generate-cisco-coverage`")
    assert "## Gap list" in md
    assert "`duo.telephony`" in md
    assert out["matrix.json"].endswith("\n")


def test_repository_reports_are_current() -> None:
    outputs = cc.render(cc.load_portfolio(), cc.collect_ucs())
    for name, text in outputs.items():
        assert (cc.OUT_DIR / name).read_text(encoding="utf-8") == text, f"run {cc.GENERATOR}"
