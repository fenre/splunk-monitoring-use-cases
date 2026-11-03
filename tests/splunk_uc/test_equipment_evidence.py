"""Tests for evidence-gated Cisco tagging (``splunk_uc.equipment_evidence``).

The regression cases are real catalogue use cases that carried a Cisco tag
in 8.26.0 although their search reads no Cisco data.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from splunk_uc import equipment_evidence as ev
from splunk_uc.generators import equipment_tags as et

_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from equipment_lib import load_equipment  # noqa: E402


@pytest.fixture(scope="module")
def cisco() -> dict:
    return next(e for e in load_equipment() if e["id"] == "cisco")


def _tags(entry: dict, app: str, spl: str, variants: tuple[str, ...] = ()) -> tuple[bool, set[str]]:
    return ev.compute_gated_tags(entry, app, ev.extract_spl_evidence(spl), variants)


@pytest.mark.parametrize(
    ("haystack", "pattern", "expected"),
    [
        ("modacity practice app", "aci", False),
        ("ta-linux-process-capacity", "aci", False),
        ("facility_details", "aci", False),
        ("splunk_ta_cisco-aci", "aci", True),
        ("cisco aci fabric", "cisco aci", True),
        ("processorapicid", "apic", False),
        ('sourcetype="cisco:iosxe"', "cisco:ios", False),
        ("sourcetype=cisco:ios:config", "cisco:ios", True),
        ("splunk_ta_cisco_meraki", "cisco_meraki", True),
    ],
)
def test_token_contains(haystack: str, pattern: str, expected: bool) -> None:
    assert ev.token_contains(haystack, pattern) is expected


def test_extract_spl_evidence_forms() -> None:
    spl = (
        'index=fw (sourcetype="pan:threat" OR sourcetype=fgt_utm) '
        'sourcetype IN ("cisco:asa", cisco:ftd:syslog) `cisco_asa` '
        "| tstats count from datamodel=Network_Traffic"
    )
    got = ev.extract_spl_evidence(spl)
    assert got.sourcetypes == {"pan:threat", "fgt_utm", "cisco:asa", "cisco:ftd:syslog"}
    assert got.indexes == {"fw"}
    assert "cisco_asa" in got.macros
    assert got.uses_datamodel
    assert got.datamodels == {"Network_Traffic"}


def test_datamodel_name_forms() -> None:
    got = ev.extract_spl_evidence(
        "| from datamodel Risk.All_Risk | from datamodel:Authentication.Failed_Authentication "
        "| datamodel Change search"
    )
    assert got.datamodels == {"Risk.All_Risk", "Authentication.Failed_Authentication", "Change"}


def test_neutral_sourcetypes_are_not_specific() -> None:
    got = ev.extract_spl_evidence('sourcetype=syslog OR sourcetype="*" OR sourcetype=sc4snmp:metric')
    assert got.specific_sourcetypes == frozenset()


@pytest.mark.parametrize(
    ("uc", "app", "spl"),
    [
        ("25.45.1 Modacity", "Modacity export via HEC", "index=personal sourcetype=practice:session"),
        ("1.1.86 capacity TA", "TA-linux-process-capacity", "index=os sourcetype=linux:proc"),
        ("5.12.1 telco CDR", "Splunk Add-on for BroadWorks", 'index=voip sourcetype="cdr:voip"'),
        ("22.58.2 CERT-FR", "Splunk Add-on for ServiceNow", "index=itsm sourcetype=snow:incident"),
        ("23.7.5 Five9", "Splunk DB Connect", "index=business sourcetype=five9:agent_state"),
        (
            "22.60.10 ADS-B",
            "Splunk Add-on for Cisco Cyber Vision (Splunkbase 5748)",
            "index=aero_adsb sourcetype=adsb:audit",
        ),
    ],
)
def test_prose_and_unrelated_searches_get_no_cisco_tag(cisco: dict, uc: str, app: str, spl: str) -> None:
    vendor, models = _tags(cisco, app, spl)
    assert not vendor, uc
    assert models == set(), uc


def test_multi_vendor_search_without_cisco_sourcetype_drops_tag(cisco: dict) -> None:
    vendor, models = _tags(
        cisco,
        "Splunk_TA_paloalto, Cisco Secure Firewall Add-on",
        "index=firewall sourcetype=pan:threat | stats count by threat_name",
    )
    assert not vendor and models == set()


def test_variant_restores_model_tag(cisco: dict) -> None:
    vendor, models = _tags(
        cisco,
        "Splunk_TA_paloalto, Cisco Secure Firewall Add-on",
        "index=firewall sourcetype=pan:threat",
        variants=("cisco_firepower",),
    )
    assert vendor and models == {"cisco_firepower"}


def test_cim_search_keeps_app_named_model(cisco: dict) -> None:
    vendor, models = _tags(
        cisco,
        "Splunk_TA_paloalto, Cisco Secure Firewall Add-on",
        "| tstats `summariesonly` count from datamodel=Network_Traffic by All_Traffic.rule",
    )
    assert vendor and models == {"cisco_firepower"}


def test_search_evidence_picks_the_right_model(cisco: dict) -> None:
    _, models = _tags(cisco, "Cisco UCM", "index=voip sourcetype=cisco:imp:syslog")
    assert models == {"cisco_imp"}
    _, models = _tags(cisco, "Cisco ACI", "index=dc sourcetype=cisco:ndo:audit")
    assert models == {"cisco_ndo"}
    _, models = _tags(cisco, "Cisco UCS", "index=hci sourcetype=cisco:hyperflex:cluster")
    assert models == {"cisco_hyperflex"}


def test_apply_tags_replaces_gated_tags_and_applies_overrides() -> None:
    owned = frozenset({"cisco", "cisco_aci", "cisco_asa"})
    sidecar = {"id": "1.1.1", "equipment": ["cisco", "linux"], "equipmentModels": ["cisco_aci", "linux_rhel"]}
    out = et._apply_tags(sidecar, ["linux"], ["linux_rhel"], owned)
    assert out["equipment"] == ["linux"]
    assert out["equipmentModels"] == ["linux_rhel"]
    out = et._apply_tags(sidecar, ["linux"], ["linux_rhel"], owned, {"add": ["cisco_asa"], "remove": []})
    assert out["equipment"] == ["cisco", "linux"]
    assert out["equipmentModels"] == ["cisco_asa", "linux_rhel"]
