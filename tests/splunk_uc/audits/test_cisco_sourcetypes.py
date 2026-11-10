"""Official Cisco sourcetype list and the splStatus example exemption."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from splunk_uc.audits.cisco_sourcetypes import (
    collect,
    compare,
    is_cisco_sourcetype,
    load_backlog,
    load_official,
    unofficial_sourcetypes,
)
from splunk_uc.generators.api_surface import _recommender_uc_thin

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA = json.loads((REPO_ROOT / "schemas" / "uc.schema.json").read_text(encoding="utf-8"))


def test_official_list_contains_the_clear_rename_targets() -> None:
    official = load_official()
    for token in (
        "cisco:ios",
        "cisco:ise:syslog",
        "cisco:cybervision:flows",
        "cisco:cybervision:events",
        "cisco:ucs",
        "cisco:spaces:firehose",
    ):
        assert token in official
    assert "cisco:iosxe" not in official
    assert "cisco:sdwan:bfd" not in official


def test_unofficial_cisco_sourcetype_fails_unless_example_family() -> None:
    official = load_official()
    sidecar = {
        "id": "5.5.1",
        "spl": 'index=sdwan sourcetype="cisco:sdwan:bfd" | stats count',
    }
    assert unofficial_sourcetypes(sidecar, official) == ["cisco:sdwan:bfd"]
    sidecar["splStatus"] = "example"
    assert unofficial_sourcetypes(sidecar, official) == []
    # An example mark does not excuse a sourcetype outside the six products.
    sidecar["spl"] = 'index=net sourcetype="cisco:iosxe" | stats count'
    assert unofficial_sourcetypes(sidecar, official) == ["cisco:iosxe"]


def test_official_sourcetype_passes() -> None:
    official = load_official()
    sidecar = {"id": "1.1.1", "spl": 'sourcetype="cisco:ios" | stats count'}
    assert unofficial_sourcetypes(sidecar, official) == []
    assert is_cisco_sourcetype("cisco:ios", official) is True
    assert is_cisco_sourcetype("pan:traffic", official) is False


def test_compare_reports_new_and_stale() -> None:
    current = [
        {"id": "UC-5.1.1", "title": "A", "sourcetype": "cisco:ios:config"},
        {"id": "UC-5.1.2", "title": "B", "sourcetype": "snort:alert"},
    ]
    new, stale = compare(current, {("UC-5.1.2", "snort:alert"), ("UC-5.1.3", "cisco:ndfc:audit")})
    assert new == [("UC-5.1.1", "cisco:ios:config")]
    assert stale == [("UC-5.1.3", "cisco:ndfc:audit")]


def test_spl_status_schema_and_thin_key() -> None:
    assert SCHEMA["schemaVersion"] == "1.11.0"
    sidecar = {"id": "5.5.1", "title": "Tunnel Health Monitoring", "splStatus": "example"}
    jsonschema.validate(sidecar, SCHEMA)
    thin = _recommender_uc_thin({"i": "5.5.1"}, None, {"5.5.1": "example"})
    assert thin["ss"] == "example"
    bare = _recommender_uc_thin({"i": "1.1.1"})
    assert "ss" not in bare
