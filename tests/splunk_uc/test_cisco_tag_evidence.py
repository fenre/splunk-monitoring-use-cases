"""CI gate: a cisco_<model> tag needs a sourcetype or a listed CIM model."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from splunk_uc.audits import cisco_tag_evidence as audit
from splunk_uc import equipment_evidence as ev

_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from equipment_lib import load_equipment  # noqa: E402


@pytest.fixture(scope="module")
def cisco() -> dict:
    return next(entry for entry in load_equipment() if entry["id"] == "cisco")


def _block(cisco: dict, model_id: str) -> dict:
    model = next(item for item in cisco["models"] if item["id"] == model_id)
    return ev.evidence_block(model)


def test_sidecar_variant_spl_backs_the_model(cisco: dict) -> None:
    uc = {
        "spl": 'index=firewall sourcetype="pan:config"',
        "splVariants": [
            {"model": "cisco_firepower", "spl": 'sourcetype="cisco:ftd" eventtype=cisco_authentication'}
        ],
    }
    assert audit._model_backed(uc, "cisco_firepower", _block(cisco, "firepower"))


def test_catalog_q_key_backs_the_model(cisco: dict) -> None:
    uc = {
        "spl": "sourcetype=pan:traffic",
        "splVariants": [{"model": "cisco_firepower", "q": 'sourcetype="cisco:sfw:estreamer"'}],
    }
    assert audit._model_backed(uc, "cisco_firepower", _block(cisco, "firepower"))


def test_listed_cim_model_backs_asa_and_risk_does_not(cisco: dict) -> None:
    asa = _block(cisco, "asa")
    traffic = {"spl": "| tstats count from datamodel=Network_Traffic.All_Traffic"}
    risk = {"spl": "| from datamodel Risk.All_Risk | search source=cisco"}
    assert audit._model_backed(traffic, "cisco_asa", asa)
    assert not audit._model_backed(risk, "cisco_asa", asa)


def test_meraki_published_models_omit_network_traffic(cisco: dict) -> None:
    meraki = _block(cisco, "meraki")
    assert "Network_Traffic" not in meraki["cimModels"]
    assert "Change" in meraki["cimModels"]
    uc = {"cimSpl": "| tstats count from datamodel=Network_Traffic where action=allowed"}
    assert not audit._model_backed(uc, "cisco_meraki", meraki)
    change = {"spl": "| tstats count from datamodel=Change.All_Changes"}
    assert audit._model_backed(change, "cisco_meraki", meraki)


def test_generic_search_does_not_back_an_app_named_model(cisco: dict) -> None:
    uc = {"spl": "index=firewall action=blocked dest_port=443", "app": "Cisco Secure Firewall"}
    assert not audit._model_backed(uc, "cisco_firepower", _block(cisco, "firepower"))


def test_diff_baseline_reports_new_and_fixed() -> None:
    new, fixed = audit.diff_baseline(
        ["UC-1.2.3 cisco_asa", "UC-2.0.1 cisco_ise"],
        {"UC-1.2.3 cisco_asa", "UC-9.9.9 cisco_ios"},
    )
    assert new == ["UC-2.0.1 cisco_ise"]
    assert fixed == ["UC-9.9.9 cisco_ios"]


def test_load_baseline_skips_comments(tmp_path: Path) -> None:
    path = tmp_path / "baseline.txt"
    path.write_text("# comment\n\nUC-1.0.1 cisco_asa\n", encoding="utf-8")
    assert audit.load_baseline(path) == {"UC-1.0.1 cisco_asa"}
