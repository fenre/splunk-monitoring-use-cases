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


def test_app_named_model_needs_a_listed_cim_model(cisco: dict) -> None:
    firepower = next(m for m in cisco["models"] if m["id"] == "firepower")
    app = "Cisco Secure Firewall"
    generic = ev.extract_spl_evidence("index=firewall sourcetype=syslog action=blocked")
    traffic = ev.extract_spl_evidence("| tstats count from datamodel=Network_Traffic.All_Traffic")
    risk = ev.extract_spl_evidence("| from datamodel Risk.All_Risk")
    entry = {**cisco, "models": [firepower]}
    assert ev.compute_gated_tags(entry, app, generic)[1] == set()
    assert ev.compute_gated_tags(entry, app, traffic)[1] == {"cisco_firepower"}
    assert ev.compute_gated_tags(entry, app, risk)[1] == set()


def test_thousandeyes_app_macros_back_the_model(cisco: dict) -> None:
    uc = {"spl": "`stream_index` thousandeyes.test.type=agent-to-server | stats avg(network.latency)"}
    assert audit._model_backed(uc, "cisco_thousandeyes", _block(cisco, "thousandeyes"))


def test_generic_sourcetype_with_listed_cim_model_classifies_as_e4(cisco: dict) -> None:
    uc = {
        "id": "0.0.1",
        "app": "Splunk Add-on for Cisco ISE",
        "spl": "index=network sourcetype=radius:accounting | stats count by user",
        "cimSpl": "| tstats count from datamodel=Authentication.Authentication by Authentication.user",
        "equipment": ["cisco"],
        "equipmentModels": ["cisco_ise"],
    }
    category, detail = audit.classify(uc, cisco)
    assert category == "E4"
    assert "cisco_ise" in detail


def test_documented_cim_models_for_duo_ucs_ios_and_nvm(cisco: dict) -> None:
    assert _block(cisco, "duo")["cimModels"] == ["Authentication"]
    assert set(_block(cisco, "ucs")["cimModels"]) == {"Inventory", "Performance"}
    assert set(_block(cisco, "ios")["cimModels"]) == {"Change", "Network_Traffic"}
    assert set(_block(cisco, "secure_client")["cimModels"]) == {"Endpoint", "Network_Traffic"}


def test_cucm_sourcetypes_back_ucm_not_unity(cisco: dict) -> None:
    syslog = {"spl": 'index=voip sourcetype="cisco:cucm:syslog" DeviceUnregistered'}
    cdr = {"spl": 'index=cisco_cdr sourcetype="cucm_cdr" | stats count by origDeviceName'}
    assert audit._model_backed(syslog, "cisco_ucm", _block(cisco, "ucm"))
    assert not audit._model_backed(syslog, "cisco_unity", _block(cisco, "unity"))
    assert audit._model_backed(cdr, "cisco_ucm", _block(cisco, "ucm"))


def _uc(uc_id: str, spl: str, models: list[str], app: str = "", **extra: object) -> dict:
    return {
        "id": uc_id,
        "title": f"T{uc_id}",
        "app": app,
        "spl": spl,
        "equipment": ["cisco"],
        "equipmentModels": models,
        **extra,
    }


_CORPUS = [
    _uc("1.1.1", 'index=firewall sourcetype="cisco:asa" action=blocked', ["cisco_asa"]),
    _uc("1.1.2", "index=cisco_ucs | stats count by host", ["cisco_ucs"]),
    _uc("1.1.3", 'index=network sourcetype="cisco:ios" %LINK', ["cisco_asa"]),
    _uc("1.1.4", 'index=firewall sourcetype="pan:traffic" action=deny', ["cisco_firepower"], app="Cisco Secure Firewall"),
    _uc("1.1.5", 'index=firewall sourcetype="pan:traffic" action=deny', ["cisco_asa"], app="Palo Alto Networks Add-on"),
    _uc("1.1.6", "index=network sourcetype=syslog failover", ["cisco_asa"], app="Cisco ASA"),
    _uc("1.1.7", "index=network failover", ["cisco_asa"], app="Cisco ASA"),
    _uc("1.1.8", "| makeresults | eval x=1", ["cisco_asa"], app="Cisco ASA"),
    _uc("1.1.9", "index=network sourcetype=snmp:interface", [], app="Cisco IOS"),
    _uc("1.1.10", "| inputlookup assets.csv", [], app="Generic"),
    _uc("1.1.11", "| from datamodel Risk.All_Risk | search source=x", ["cisco_asa"]),
]


@pytest.fixture()
def corpus(monkeypatch: pytest.MonkeyPatch, cisco: dict) -> None:
    monkeypatch.setattr(audit, "iter_uc_sidecars", lambda: ((Path(u["id"]), u) for u in _CORPUS))
    monkeypatch.setattr(audit, "_load_override_ids", lambda: {"1.1.11"})
    monkeypatch.setattr(audit, "_registry", lambda: cisco)


def test_build_rows_classifies_each_category(corpus: None) -> None:
    rows = {r.uc_id: r for r in audit.build_rows()}
    assert rows["UC-1.1.1"].category == "A"
    assert rows["UC-1.1.2"].category == "E1"
    assert rows["UC-1.1.3"].category == "G"
    assert rows["UC-1.1.4"].category == "B"
    assert rows["UC-1.1.5"].category == "C"
    assert rows["UC-1.1.6"].category == "D"
    assert rows["UC-1.1.7"].category == "E3"
    assert rows["UC-1.1.8"].category == "E5"
    assert rows["UC-1.1.9"].category == "F"
    assert rows["UC-1.1.9"].action == "keep vendor tag; no model claim"
    assert rows["UC-1.1.10"].action == "remove-tag (Cisco named only in prose)"
    assert rows["UC-1.1.11"].action == "keep via data/equipment-tag-overrides.json"
    assert [r.uc_id for r in audit.build_rows()][:2] == ["UC-1.1.1", "UC-1.1.2"]


def test_backing_failures_skip_overrides_and_backed_tags(corpus: None, cisco: dict) -> None:
    failures = audit.backing_failures(cisco)
    assert "UC-1.1.1 cisco_asa" not in failures
    assert "UC-1.1.11 cisco_asa" not in failures
    assert "UC-1.1.3 cisco_asa" in failures
    assert failures == sorted(failures, key=audit._line_sort_key)


def test_main_check_fails_and_writes_csv(corpus: None, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out = tmp_path / "audit.csv"
    assert audit.main(["--check", "--write-csv", str(out), "--summary"]) == 1
    text = capsys.readouterr().out
    assert "model tags have no producible evidence" in text
    assert "Cisco-tagged use cases: 11" in text
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0].startswith("uc_id,title,equipment")
    assert len(lines) == 12


def test_main_check_passes_on_backed_corpus(
    monkeypatch: pytest.MonkeyPatch, cisco: dict, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(audit, "iter_uc_sidecars", lambda: iter([(Path("a"), _CORPUS[0])]))
    monkeypatch.setattr(audit, "_load_override_ids", set)
    monkeypatch.setattr(audit, "_registry", lambda: cisco)
    assert audit.main(["--check"]) == 0
    assert "Cisco tag evidence check passed." in capsys.readouterr().out
