"""Schema v1.10.0 ``splVariants``: sidecar names, catalogue abbreviations, thin API."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "tools"))

from build.parse_content import _canonical_uc_to_legacy  # noqa: E402
from build.templates import _helpers, uc as uc_template  # noqa: E402
from splunk_uc.generators.api_surface import _recommender_uc_thin  # noqa: E402

SCHEMA = json.loads((REPO_ROOT / "schemas" / "uc.schema.json").read_text(encoding="utf-8"))

VARIANT = {
    "model": "cisco_firepower",
    "sourcetypes": ["cisco:ftd:syslog"],
    "splunkbaseAppId": 7404,
    "spl": 'index=firewall sourcetype="cisco:ftd:syslog" | stats count',
    "cimSpl": "| tstats count from datamodel=Network_Traffic",
    "notes": "Field names from the Cisco Secure Firewall add-on.",
    "status": "draft",
    "requiresSmeReview": True,
}


def _sidecar() -> dict:
    return {
        "id": "5.2.2",
        "title": "Policy Change Audit",
        "spl": 'index=firewall sourcetype="pan:config"',
        "splVariants": [dict(VARIANT)],
    }


def test_schema_version_and_valid_variant() -> None:
    assert SCHEMA["schemaVersion"] == "1.11.0"
    jsonschema.validate(_sidecar(), SCHEMA)


@pytest.mark.parametrize(
    "patch",
    [
        {"spl": ""},
        {"model": "Firepower"},
        {"splunkbaseAppId": "7404"},
        {"sourcetypes": []},
        {"status": "proposed"},
        {"extra": True},
    ],
)
def test_schema_rejects_a_malformed_variant(patch: dict) -> None:
    item = dict(VARIANT)
    item.update(patch)
    if "spl" in patch and patch["spl"] == "":
        item.pop("spl")
    sidecar = _sidecar()
    sidecar["splVariants"] = [item]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(sidecar, SCHEMA)


def test_catalogue_abbreviates_only_the_searches() -> None:
    legacy = _canonical_uc_to_legacy(_sidecar())
    assert legacy["q"] == 'index=firewall sourcetype="pan:config"'
    assert legacy["qv"] == [
        {
            "model": "cisco_firepower",
            "sourcetypes": ["cisco:ftd:syslog"],
            "splunkbaseAppId": 7404,
            "q": VARIANT["spl"],
            "qs": VARIANT["cimSpl"],
            "notes": VARIANT["notes"],
            "status": "draft",
            "requiresSmeReview": True,
        }
    ]


def test_thin_record_lists_models_and_omits_the_search() -> None:
    thin = _recommender_uc_thin({"i": "5.2.2", "qv": _canonical_uc_to_legacy(_sidecar())["qv"]})
    assert thin["variantModels"] == ["cisco_firepower"]
    assert "q" not in thin
    bare = _recommender_uc_thin({"i": "1.1.1"})
    assert "variantModels" not in bare


def test_markdown_and_html_twins_render_the_variant() -> None:
    legacy = _canonical_uc_to_legacy(_sidecar())
    legacy["n"] = "Policy Change Audit"
    cat = {"i": 5, "n": "Network"}
    sub = {"i": "5.2", "n": "Firewall"}
    ctx = _helpers.RenderContext(
        asset_styles="s.css",
        asset_app_js="a.js",
        build_id="abcd",
        generated_at="2026-11-03T00:00:00Z",
        version="8.26.0",
        uc_reverse_prereq={},
        uc_title_index={},
    )
    md = uc_template.render_markdown_twin(legacy, cat, sub, "network", ctx=ctx)
    assert "## SPL variant: cisco_firepower" in md
    assert 'sourcetype="cisco:ftd:syslog"' in md
    assert "requires SME review" in md
    assert "## CIM SPL variant: cisco_firepower" in md
    html = uc_template.render_html(legacy, cat, sub, "network", ctx=ctx)
    assert "SPL variants" in html
    assert "cisco:ftd:syslog" in html
    page = uc_template.render_index_json(legacy, cat, sub, "network", ctx=ctx)
    assert page["fields"]["qv"][0]["model"] == "cisco_firepower"
