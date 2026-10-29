"""Splunk product registry (ADR-0017) — registry contract and consumer invariants.

One fixture UC per registered product runs through every consumer that reads
the registry: structure audit, gold tiers, build loader and quality score,
UC templates, identity fingerprint, exports, lift prompt, and the MCP
``get_use_case`` output schema.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
for extra in (REPO_ROOT / "src", REPO_ROOT / "tools", REPO_ROOT / "mcp" / "src"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

from splunk_uc import id_ledger, products  # noqa: E402
from splunk_uc.audits import gold_profile, gold_profile_v2, uc_structure  # noqa: E402

REGISTRY = json.loads((REPO_ROOT / "data" / "splunk-products.json").read_text(encoding="utf-8"))
REGISTRY_SCHEMA = json.loads(
    (REPO_ROOT / "schemas" / "splunk-products.schema.json").read_text(encoding="utf-8")
)
UC_SCHEMA = json.loads((REPO_ROOT / "schemas" / "uc.schema.json").read_text(encoding="utf-8"))
PRODUCT_IDS = [row["id"] for row in REGISTRY["products"]]
DEFAULT = REGISTRY["defaultProduct"]
NON_DEFAULT = [pid for pid in PRODUCT_IDS if pid != DEFAULT]

_ARTIFACT_BODIES = {
    "signalflow": "detect(when(data('cpu.utilization').mean(by=['host.name']) > 90, '5m')).publish('CPU high')",
    "text": "Open the product UI, create the object below, and save it.",
}


# ---------------------------------------------------------------------------
# Registry contract
# ---------------------------------------------------------------------------


def test_registry_validates_against_schema() -> None:
    jsonschema.validate(REGISTRY, REGISTRY_SCHEMA)


def test_registry_ids_unique_and_default_registered() -> None:
    assert len(PRODUCT_IDS) == len(set(PRODUCT_IDS))
    assert DEFAULT in PRODUCT_IDS


def test_uc_schema_products_enum_matches_registry() -> None:
    enum = UC_SCHEMA["properties"]["products"]["items"]["enum"]
    assert enum == PRODUCT_IDS


def test_registry_requires_are_uc_schema_fields() -> None:
    props = set(UC_SCHEMA["properties"])
    for row in REGISTRY["products"]:
        assert set(row["requires"]) <= props, row["id"]
        assert set(row["fingerprintFields"]) <= props, row["id"]


def test_default_product_fingerprint_is_title_plus_spl() -> None:
    row = products.product(DEFAULT)
    assert ("title", *row["fingerprintFields"]) == id_ledger.DEFAULT_FINGERPRINT_FIELDS


def test_absent_products_means_default() -> None:
    assert products.products_of({"id": "1.1.1"}) == [DEFAULT]
    assert products.is_default({"id": "1.1.1"})
    assert products.non_default_products({"id": "1.1.1"}) is None
    assert products.products_of({"prd": [NON_DEFAULT[0]]}) == [NON_DEFAULT[0]]


# ---------------------------------------------------------------------------
# No consumer branches on a product id
# ---------------------------------------------------------------------------

_CONSUMER_ROOTS = (
    REPO_ROOT / "src" / "splunk_uc",
    REPO_ROOT / "tools" / "build",
    REPO_ROOT / "mcp" / "src" / "splunk_uc_mcp",
)
_REGISTRY_IMPORT = re.compile(r"from splunk_uc import products|import splunk_uc\.products")


def _consumer_files() -> list[Path]:
    files: list[Path] = []
    for root in _CONSUMER_ROOTS:
        for path in root.rglob("*.py"):
            if "__pycache__" in path.parts or path.name == "products.py":
                continue
            text = path.read_text(encoding="utf-8")
            if _REGISTRY_IMPORT.search(text) or "splunk_uc_mcp" in path.parts:
                files.append(path)
    files.extend(sorted((REPO_ROOT / "src" / "scripts").glob("*.js")))
    return files


def test_consumers_never_hard_code_a_product_id() -> None:
    pattern = re.compile(r"[\"'`](" + "|".join(re.escape(p) for p in PRODUCT_IDS) + r")[\"'`]")
    offenders = [
        f"{path.relative_to(REPO_ROOT)}: {m.group(1)}"
        for path in _consumer_files()
        for m in pattern.finditer(path.read_text(encoding="utf-8"))
    ]
    assert not offenders, offenders


# ---------------------------------------------------------------------------
# Fixture UC per product
# ---------------------------------------------------------------------------


def _fixture(pid: str, index: int) -> dict[str, Any]:
    row = products.product(pid)
    uc: dict[str, Any] = {
        "id": f"99.1.{index}",
        "title": f"Fixture use case implemented in {row['name']}",
        "criticality": "medium",
        "difficulty": "intermediate",
        "monitoringType": ["Performance"],
        "value": "Gives operators an early warning before the monitored service degrades for users.",
        "description": "Detects sustained resource saturation on monitored hosts and raises an alert for the owning team.",
        "app": row["name"],
        "dataSources": f"{row['name']} host metrics for every monitored host.",
        "implementation": "Configure the detection described below and route it to the owning team.",
        "visualization": "Single value and line chart per host.",
        "grandmaExplanation": "We watch the machines and tell someone when one is working too hard.",
    }
    if pid != DEFAULT:
        uc["products"] = [pid]
    if "spl" in row["requires"]:
        uc["spl"] = "index=os sourcetype=cpu | stats avg(pctCPU) AS cpu BY host | where cpu > 90"
    if "cimModels" in row["requires"]:
        uc["cimModels"] = ["Performance"]
    if row["artifactTypes"]:
        lang = "signalflow" if row["artifactTypes"][0] == "detector" else "text"
        uc["productArtifacts"] = [
            {
                "product": pid,
                "type": row["artifactTypes"][0],
                "language": lang,
                "title": "Sustained CPU saturation",
                "body": _ARTIFACT_BODIES[lang],
                "docsUrl": row["docsUrl"],
            }
        ]
    return uc


FIXTURES = {pid: _fixture(pid, i + 1) for i, pid in enumerate(PRODUCT_IDS)}


@pytest.mark.parametrize("pid", PRODUCT_IDS)
def test_fixture_validates_against_uc_schema(pid: str) -> None:
    jsonschema.validate(FIXTURES[pid], UC_SCHEMA)


@pytest.mark.parametrize("pid", PRODUCT_IDS)
def test_fixture_passes_structure_audit(pid: str, tmp_path: Path) -> None:
    uc = FIXTURES[pid]
    path = tmp_path / f"UC-{uc['id']}.json"
    issues = uc_structure.audit_uc_json(str(path), uc)
    assert issues == []


@pytest.mark.parametrize("pid", NON_DEFAULT)
def test_structure_audit_requires_the_products_fields(pid: str, tmp_path: Path) -> None:
    uc = dict(FIXTURES[pid])
    for field in products.requires(uc):
        uc.pop(field, None)
    path = tmp_path / f"UC-{uc['id']}.json"
    issues = uc_structure.audit_uc_json(str(path), uc)
    for field in products.requires(FIXTURES[pid]):
        assert any(f"missing required field {field!r}" in i for i in issues), issues
    if "spl" not in products.requires(FIXTURES[pid]):
        assert not any("'spl'" in i for i in issues), issues


def test_structure_audit_rejects_unregistered_artifact_type(tmp_path: Path) -> None:
    pid = next(p for p in NON_DEFAULT if products.product(p)["artifactTypes"])
    uc = json.loads(json.dumps(FIXTURES[pid]))
    uc["productArtifacts"][0]["type"] = "not-a-real-type"
    issues = uc_structure.audit_uc_json(str(tmp_path / f"UC-{uc['id']}.json"), uc)
    assert any("is not an artifact type" in i for i in issues), issues


def test_structure_audit_rejects_artifact_for_unlisted_product(tmp_path: Path) -> None:
    pid = next(p for p in NON_DEFAULT if products.product(p)["artifactTypes"])
    uc = json.loads(json.dumps(FIXTURES[pid]))
    uc.pop("products")
    issues = uc_structure.audit_uc_json(str(tmp_path / f"UC-{uc['id']}.json"), uc)
    assert any("is not listed in products" in i for i in issues), issues


@pytest.mark.parametrize("pid", PRODUCT_IDS)
def test_fixture_reaches_bronze(pid: str) -> None:
    result = gold_profile.audit_uc(FIXTURES[pid], REPO_ROOT / "content" / "fixture.json")
    assert result["tier"] != "none", result["gaps"]


def test_tier_required_unchanged_for_default_product() -> None:
    uc = FIXTURES[DEFAULT]
    assert gold_profile.tier_required(uc, gold_profile.BRONZE_REQUIRED) == gold_profile.BRONZE_REQUIRED
    assert gold_profile.tier_required(uc, gold_profile.GOLD_REQUIRED) == gold_profile.GOLD_REQUIRED


@pytest.mark.parametrize("pid", NON_DEFAULT)
def test_gold_v2_does_not_demand_splunkbase_for_non_spl_products(pid: str) -> None:
    uc = FIXTURES[pid]
    result = gold_profile_v2.audit_uc_v2(uc, REPO_ROOT / "content" / "fixture.json")
    expect_gap = products.applies(uc, "splReferences")
    has_gap = any("Splunkbase ID" in g for g in result["gaps"])
    assert has_gap == expect_gap


@pytest.mark.parametrize("pid", PRODUCT_IDS)
def test_fingerprint_follows_registry_fields(pid: str) -> None:
    uc = FIXTURES[pid]
    fields = id_ledger.fingerprint_field_names(uc)
    assert fields[0] == "title"
    assert fields[1:] == products.fingerprint_fields(uc)
    revision = id_ledger._revision_record(id_ledger.content_fingerprint(uc), "9.9.9", fields=fields)
    if tuple(fields) == id_ledger.DEFAULT_FINGERPRINT_FIELDS:
        assert "fingerprintFields" not in revision
    else:
        assert revision["fingerprintFields"] == fields
    changed = json.loads(json.dumps(uc))
    if "productArtifacts" in fields:
        changed["productArtifacts"][0]["body"] += " # edited"
    else:
        changed["spl"] += " | head 10"
    assert id_ledger.content_fingerprint(changed) != id_ledger.content_fingerprint(uc)


def test_default_fingerprint_matches_pre_registry_formula() -> None:
    import hashlib

    uc = FIXTURES[DEFAULT]
    legacy = json.dumps(
        {"spl": uc["spl"].strip(), "title": uc["title"].strip()},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    assert id_ledger.content_fingerprint(uc) == hashlib.sha256(legacy.encode("utf-8")).hexdigest()


@pytest.mark.parametrize("pid", PRODUCT_IDS)
def test_exports_follow_registry(pid: str) -> None:
    from splunk_uc.generators import recommender_app

    uc = dict(FIXTURES[pid])
    uc["_matchedCompliance"] = [{"_canonical": "gdpr", "regulation": "GDPR", "clause": "Art.32"}]
    sections = recommender_app._compliance_savedsearches_sections([uc], {})
    row = products.product(pid)
    assert bool(sections) == row["exports"]["savedSearches"]


@pytest.mark.parametrize("pid", NON_DEFAULT)
def test_non_spl_products_skip_dashboards_and_alert_actions(pid: str, tmp_path: Path) -> None:
    from splunk_uc.generators import alert_actions, dashboards

    uc = FIXTURES[pid]
    cat = tmp_path / "content" / "cat-99-fixtures"
    cat.mkdir(parents=True)
    (cat / f"UC-{uc['id']}.json").write_text(json.dumps(uc), encoding="utf-8")
    report = dashboards.emit_all(tmp_path / "content", tmp_path / "dash")
    assert report.uc_ids == [] and report.skipped == 1
    written = alert_actions.generate_all(
        content_dir=tmp_path / "content", out_dir=tmp_path / "alerts", dry_run=True
    )
    assert written == 0


@pytest.mark.parametrize("pid", PRODUCT_IDS)
def test_build_loader_emits_product_keys_only_when_non_default(pid: str) -> None:
    from build import parse_content

    uc = FIXTURES[pid]
    legacy = parse_content._canonical_uc_to_legacy(uc)
    if pid == DEFAULT:
        assert "prd" not in legacy and "pra" not in legacy and "prdn" not in legacy
    else:
        assert legacy["prd"] == [pid]
        assert legacy["prdn"] == [products.display_name(pid)]
    assert parse_content._compute_quality(legacy)[0] != "none"


@pytest.mark.parametrize("pid", NON_DEFAULT)
def test_no_generated_spl_guide_for_non_spl_products(pid: str) -> None:
    from build import parse_content

    uc = FIXTURES[pid]
    if products.applies(uc, "spl"):
        pytest.skip("product implements the use case in SPL")
    legacy = parse_content._canonical_uc_to_legacy(uc)
    record = {"i": 99, "s": [{"i": "99.1", "u": [legacy]}]}
    parse_content._post_process_category(record, parse_content._enrichment)
    assert "Run the SPL" not in (legacy.get("md") or "")


@pytest.mark.parametrize("pid", NON_DEFAULT)
def test_templates_render_products_and_artifacts(pid: str) -> None:
    from build import parse_content
    from build.templates import _helpers
    from build.templates import uc as uc_template

    legacy = parse_content._canonical_uc_to_legacy(FIXTURES[pid])
    cat = {"i": 99, "n": "Fixtures", "s": []}
    sub = {"i": "99.1", "n": "Fixture products", "u": [legacy]}
    ctx = _helpers.RenderContext(version="9.9.9", generated_at="2026-01-01T00:00:00Z")
    row = products.product(pid)
    html = uc_template.render_html(legacy, cat, sub, "fixtures", ctx=ctx)
    md = uc_template.render_markdown_twin(legacy, cat, sub, "fixtures", ctx=ctx)
    assert "Implemented in" in html and row["name"] in html
    assert "| Implemented in | " + row["name"] in md
    for artifact in FIXTURES[pid].get("productArtifacts", []):
        assert artifact["title"] in html and artifact["title"] in md
    payload = uc_template.render_index_json(legacy, cat, sub, "fixtures", ctx=ctx)
    assert payload["fields"]["prd"] == [pid]


def test_template_has_no_product_section_for_default() -> None:
    from build import parse_content
    from build.templates import _helpers
    from build.templates import uc as uc_template

    legacy = parse_content._canonical_uc_to_legacy(FIXTURES[DEFAULT])
    ctx = _helpers.RenderContext(version="9.9.9", generated_at="2026-01-01T00:00:00Z")
    cat = {"i": 99, "n": "Fixtures", "s": []}
    sub = {"i": "99.1", "n": "Fixture products", "u": [legacy]}
    assert "Implemented in" not in uc_template.render_html(legacy, cat, sub, "fixtures", ctx=ctx)
    assert "Implemented in" not in uc_template.render_markdown_twin(
        legacy, cat, sub, "fixtures", ctx=ctx
    )


@pytest.mark.parametrize("pid", PRODUCT_IDS)
def test_uc_thin_carries_products_only_when_non_default(pid: str) -> None:
    from build import parse_content
    from splunk_uc.generators import api_surface

    legacy = parse_content._canonical_uc_to_legacy(FIXTURES[pid])
    record = api_surface._recommender_uc_thin(legacy)
    if pid == DEFAULT:
        assert "products" not in record and "productArtifacts" not in record
    else:
        assert record["products"] == [pid]


@pytest.mark.parametrize("pid", PRODUCT_IDS)
def test_mcp_output_schema_accepts_fixture(pid: str) -> None:
    from splunk_uc_mcp.tools.use_case import GET_USE_CASE_OUTPUT_SCHEMA

    jsonschema.validate(FIXTURES[pid], GET_USE_CASE_OUTPUT_SCHEMA)


@pytest.mark.parametrize("pid", PRODUCT_IDS)
def test_lift_prompt_rubric_follows_product(pid: str) -> None:
    from splunk_uc.tools.lift import prompt

    datasources_rule, detailed_rule = prompt._rubric_rules(FIXTURES[pid])
    if products.applies(FIXTURES[pid], "splReferences"):
        assert "sourcetype" in datasources_rule
    else:
        assert "Splunkbase ID" not in datasources_rule
        assert products.implement_section(FIXTURES[pid]) in detailed_rule


def test_lift_firewall_covers_product_fields() -> None:
    from splunk_uc.tools.lift import validate

    assert {"products", "productArtifacts"} <= validate.FIREWALLED_FIELDS
