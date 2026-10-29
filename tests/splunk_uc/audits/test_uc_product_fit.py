"""Tests for ``splunk_uc.audits.uc_product_fit`` (ADR-0017 Phase 2)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

import splunk_uc.audits.uc_product_fit as fit
from splunk_uc import products

REPO_ROOT = Path(__file__).resolve().parents[3]


def _non_spl_product() -> dict[str, Any]:
    """A registry product that is not implemented in SPL and has artifact types."""
    for row in products.all_products():
        if row["artifactTypes"] and "spl" not in row["audits"]:
            return row
    pytest.skip("registry has no non-SPL product with artifact types")


def _spl_product() -> dict[str, Any]:
    """A non-default registry product that is implemented in SPL."""
    for row in products.all_products():
        if row["id"] != products.default_product_id() and "spl" in row["audits"]:
            return row
    pytest.skip("registry has no non-default SPL product")


def _rules(pid: str) -> dict[str, Any]:
    return {
        "products": {
            pid: {
                "aliases": ["OldName"],
                "dataMarkers": ["^acme"],
                "documentedIngest": {
                    "indexes": ["acme_events"],
                    "sourcetypes": ["acme:event"],
                    "commands": ["acmesearch"],
                },
                "evidence": [{"title": "docs", "url": "https://example.com/acme"}],
            }
        }
    }


def _uc(spl: str, implementation: str = "Tune thresholds.", **extra: Any) -> dict[str, Any]:
    return {"id": "1.1.1", "title": "t", "spl": spl, "implementation": implementation, **extra}


def _kinds(cands: list[fit.Candidate]) -> list[str]:
    return [r.kind for c in cands for r in c.reasons]


# --------------------------------------------------------------- makeresults


def test_makeresults_checklist_is_flagged() -> None:
    spl = '| makeresults | eval section=mvappend("a","b") | mvexpand section | table section'
    assert _kinds(fit.find_candidates([_uc(spl)], {"products": {}})) == ["makeresults-only"]


@pytest.mark.parametrize(
    "spl",
    [
        "| makeresults | append [ search index=main | stats count ]",
        "| makeresults | append [| tstats count where index=main ]",
        "| makeresults | append [| inputlookup assets.csv ]",
        "| makeresults | append [| rest /services/server/info ]",
    ],
)
def test_makeresults_that_reads_data_is_not_flagged(spl: str) -> None:
    assert fit.find_candidates([_uc(spl)], {"products": {}}) == []


# ------------------------------------------------------- undocumented ingest


def test_product_sourcetype_and_index_outside_documented_ingest() -> None:
    pid = _non_spl_product()["id"]
    cands = fit.find_candidates(
        [_uc("index=acme-logs sourcetype=acme:custom | stats count")], _rules(pid)
    )
    assert [(r.kind, r.detail, r.product) for c in cands for r in c.reasons] == [
        ("undocumented-sourcetype", "acme:custom", pid),
        ("undocumented-index", "acme-logs", pid),
    ]


def test_documented_ingest_and_unrelated_data_are_not_flagged() -> None:
    pid = _non_spl_product()["id"]
    ucs = [
        _uc("index=acme_events sourcetype=acme:event | stats count"),
        _uc("| acmesearch flow | stats count"),
        _uc("index=main sourcetype=syslog | stats count"),
        _uc('index=acme* sourcetype="acme:*" | stats count'),
    ]
    assert fit.find_candidates(ucs, _rules(pid)) == []


# --------------------------------------------------------- configures-product


def test_prose_configuring_the_product_over_its_data_is_flagged() -> None:
    row = _non_spl_product()
    noun = row["artifactTypes"][0].replace("-", " ")
    uc = _uc(
        "index=acme_events | stats count",
        implementation=f"Create a {noun} in OldName for this. Then tune thresholds.",
    )
    cands = fit.find_candidates([uc], _rules(row["id"]))
    assert _kinds(cands) == ["configures-product"]
    assert cands[0].reasons[0].detail == f"Create a {noun} in OldName for this."


def test_prose_without_product_data_is_not_flagged() -> None:
    row = _non_spl_product()
    noun = row["artifactTypes"][0].replace("-", " ")
    uc = _uc("index=main | stats count", implementation=f"Trigger a {row['name']} {noun}.")
    assert fit.find_candidates([uc], _rules(row["id"])) == []


def test_prose_is_ignored_for_products_implemented_in_spl() -> None:
    row = _spl_product()
    noun = row["artifactTypes"][0].replace("-", " ")
    uc = _uc("index=acme_events | stats count", implementation=f"Define the {row['name']} {noun}.")
    assert fit.find_candidates([uc], _rules(row["id"])) == []


# ------------------------------------------------------------- validation


def test_committed_rules_and_review_are_valid() -> None:
    ucs = {str(u["id"]) for u in fit.iter_ucs(fit.CONTENT_ROOT)}
    assert fit.validate_rules(fit._load_json(fit.RULES_PATH)) == []
    assert fit.validate_review(fit._load_json(fit.REVIEW_PATH), ucs) == []


def test_rules_reject_unknown_and_default_products() -> None:
    rules = _rules(products.default_product_id())
    rules["products"]["not-a-product"] = rules["products"][products.default_product_id()]
    issues = fit.validate_rules(rules)
    assert any("default product" in i for i in issues)
    assert any("unknown product 'not-a-product'" in i for i in issues)


def test_review_requires_evidence_for_migrate_and_keep() -> None:
    review = {
        "$schema": "x",
        "schemaVersion": "1.0.0",
        "entries": [
            {"id": "1.1.1", "verdict": "keep", "note": "n"},
            {"id": "1.1.2", "verdict": "migrate", "note": "n"},
            {"id": "1.1.3", "verdict": "needs-sme-review", "note": "no docs"},
        ],
    }
    issues = fit.validate_review(review, {"1.1.1", "1.1.2", "1.1.3"})
    assert sum("evidence" in i for i in issues) == 2
    assert any("'products' is a required property" in i for i in issues)


def test_review_rejects_duplicates_unknown_ucs_and_products() -> None:
    entry = {"id": "1.1.1", "verdict": "needs-sme-review", "note": "n", "products": ["nope"]}
    review = {"$schema": "x", "schemaVersion": "1.0.0", "entries": [entry, dict(entry)]}
    issues = fit.validate_review(review, set())
    assert any("more than once" in i for i in issues)
    assert any("does not exist" in i for i in issues)
    assert any("unknown product 'nope'" in i for i in issues)


# ---------------------------------------------------------------- main()


def _patch_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, review: dict[str, Any]) -> None:
    content = tmp_path / "content" / "cat-01-x"
    content.mkdir(parents=True)
    (content / "UC-1.1.1.json").write_text(
        json.dumps(_uc("| makeresults | eval a=1 | table a")), encoding="utf-8"
    )
    review_path = tmp_path / "review.json"
    review_path.write_text(json.dumps(review), encoding="utf-8")
    monkeypatch.setattr(fit, "CONTENT_ROOT", tmp_path / "content")
    monkeypatch.setattr(fit, "REVIEW_PATH", review_path)


def test_main_warns_but_passes_check_with_unreviewed_candidates(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _patch_paths(monkeypatch, tmp_path, {"$schema": "x", "schemaVersion": "1.0.0", "entries": []})
    assert fit.main(["--check", "--out", str(tmp_path / "r.json")]) == 0
    assert "1 candidate(s), 1 unreviewed" in capsys.readouterr().out
    assert fit.main(["--strict", "--out", str(tmp_path / "r.json")]) == 1
    report = json.loads((tmp_path / "r.json").read_text(encoding="utf-8"))
    assert report["byReason"] == {"makeresults-only": 1}


def test_main_strict_passes_once_reviewed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    entry = {"id": "1.1.1", "verdict": "needs-sme-review", "note": "checklist"}
    _patch_paths(
        monkeypatch, tmp_path, {"$schema": "x", "schemaVersion": "1.0.0", "entries": [entry]}
    )
    assert fit.main(["--strict", "--out", str(tmp_path / "r.json")]) == 0


def test_main_check_fails_on_malformed_review(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    entry = {"id": "9.9.9", "verdict": "needs-sme-review", "note": "missing UC"}
    _patch_paths(
        monkeypatch, tmp_path, {"$schema": "x", "schemaVersion": "1.0.0", "entries": [entry]}
    )
    assert fit.main(["--check", "--out", str(tmp_path / "r.json")]) == 1
