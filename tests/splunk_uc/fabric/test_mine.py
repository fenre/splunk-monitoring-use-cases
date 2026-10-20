"""Registry mining keeps aliases and refuses to guess conflicts."""

from __future__ import annotations

import json
from pathlib import Path

from splunk_uc.fabric.extract import sourcetype_candidates
from splunk_uc.fabric.mine import PERSONAS, build_payloads


def test_addresses_and_wildcards_are_not_sourcetypes() -> None:
    kept, ambiguous = sourcetype_candidates(
        'search sourcetype=pan:* sourcetype=aa:bb:cc:dd:ee:ff sourcetype="cisco:ios"'
    )
    assert kept == ["cisco:ios"]
    reasons = {token: reason for token, reason in ambiguous}
    assert reasons["pan:*"] == "wildcard"
    assert reasons["aa:bb:cc:dd:ee:ff"] == "looks-like-address"


def test_personas_are_not_the_owner_enum() -> None:
    owner = {
        "ciso",
        "dpo",
        "cfo",
        "head of ir",
        "head of ot security",
        "head of it operations",
        "head of platform",
        "procurement",
        "legal",
        "hr",
        "board / audit committee",
    }
    for persona in PERSONAS:
        assert persona["id"].replace("_", " ") not in owner
        assert persona["label"].casefold() not in owner


def _write_uc(root: Path, uc_id: str, equipment: list[str], spl: str) -> None:
    category = root / "cat-05-network"
    category.mkdir(parents=True, exist_ok=True)
    payload = {
        "id": uc_id,
        "title": f"Use case {uc_id} title",
        "spl": spl,
        "dataSources": "",
        "cimSpl": "",
        "app": "",
        "equipment": equipment,
    }
    (category / f"UC-{uc_id}.json").write_text(json.dumps(payload), encoding="utf-8")


def test_conflicting_vendor_is_listed_not_linked(tmp_path: Path) -> None:
    _write_uc(tmp_path, "5.2.1", ["paloalto"], 'index=net sourcetype="pan:traffic"')
    _write_uc(tmp_path, "5.2.2", ["cisco"], 'index=net sourcetype="pan:traffic"')
    _write_uc(tmp_path, "5.1.1", ["cisco"], 'index=net sourcetype="cisco:ios"')
    _write_uc(tmp_path, "5.1.2", ["cisco"], "index=net sourcetype=cisco:ios")

    payloads = build_payloads(tmp_path)
    by_canonical = {entry["canonical"]: entry for entry in payloads["sourcetypes"]["entries"]}
    assert by_canonical["pan:traffic"]["vendorProduct"] is None
    assert by_canonical["cisco:ios"]["vendorProduct"] == "cisco"
    assert by_canonical["cisco:ios"]["aliases"] == []
    conflicts = [
        item
        for item in payloads["ambiguous"]["values"]
        if item["kind"] == "sourcetype" and item["reason"] == "vendor-conflict"
    ]
    assert any(item["value"] == "pan:traffic" for item in conflicts)
