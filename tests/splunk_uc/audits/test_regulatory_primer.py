"""Tests for ``splunk_uc.audits.regulatory_primer``.

The audit compares machine-verifiable claims in
``docs/regulatory-primer.md`` against the authoritative sources
(``content/cat-22-regulatory-compliance/_category.json`` and
``data/regulations.json``). It emits five categories of findings —
UC counts in body text, UC counts in the Appendix A table,
framework totals, tier badges, dead file references, and "Phase N.N"
internal jargon.

Before this file: 12.1 % coverage (one incidental import path).
After this file: hermetic exercises of every documented finding
category plus the CLI mode contracts.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from splunk_uc.audits import regulatory_primer as audit


# --------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------- #


@pytest.fixture
def hermetic_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> dict[str, Path]:
    """Point the audit's module-level paths at a synthetic catalogue.

    Returns a dict of ``{primer, category_json, regulations_json,
    repo_root}`` so tests can drop files in directly. The audit must
    survive ``audit()`` against this synthetic corpus and ``main()``
    against it via monkeypatched module paths.
    """

    repo = tmp_path
    docs = repo / "docs"
    cat_dir = repo / "content" / "cat-22-regulatory-compliance"
    data_dir = repo / "data"
    for d in (docs, cat_dir, data_dir):
        d.mkdir(parents=True)

    primer = docs / "regulatory-primer.md"
    category_json = cat_dir / "_category.json"
    regulations_json = data_dir / "regulations.json"

    monkeypatch.setattr(audit, "REPO_ROOT", str(repo))
    monkeypatch.setattr(audit, "PRIMER", str(primer))
    monkeypatch.setattr(audit, "CATEGORY_JSON", str(category_json))
    monkeypatch.setattr(audit, "REGULATIONS_JSON", str(regulations_json))

    return {
        "repo_root": repo,
        "docs": docs,
        "primer": primer,
        "category_json": category_json,
        "regulations_json": regulations_json,
    }


def _seed_authoritative_sources(
    paths: dict[str, Path],
    *,
    sub_counts: dict[str, int] | None = None,
    frameworks: list[dict] | None = None,
) -> None:
    """Write the two authoritative sources into the hermetic root.

    ``sub_counts`` is a {subcategory_id: useCaseCount} map.
    ``frameworks`` is a list of {tier: int} dicts (other framework
    keys are unused by this audit).
    """

    sub_counts = sub_counts or {"22.1": 10, "22.2": 5}
    paths["category_json"].write_text(
        json.dumps(
            {
                "subcategories": [
                    {"id": sid, "useCaseCount": n}
                    for sid, n in sub_counts.items()
                ]
            }
        ),
        encoding="utf-8",
    )
    frameworks = frameworks or [
        {"tier": 1, "id": "f1"},
        {"tier": 2, "id": "f2"},
        {"tier": 2, "id": "f3"},
        {"tier": 3, "id": "f4"},
    ]
    paths["regulations_json"].write_text(
        json.dumps({"frameworks": frameworks}),
        encoding="utf-8",
    )


# --------------------------------------------------------------------- #
# _load_uc_counts / _load_framework_tiers
# --------------------------------------------------------------------- #


def test_load_uc_counts_aggregates_extended_subcategories(
    hermetic_paths: dict[str, Path],
) -> None:
    """Extended subcategories (e.g. ``22.35a``) must roll up under the
    base ID (``22.35``) so the body / table tallies match."""

    _seed_authoritative_sources(
        hermetic_paths,
        sub_counts={"22.1": 3, "22.35a": 2, "22.35b": 7},
    )
    counts = audit._load_uc_counts()
    assert counts["22.1"] == 3
    assert counts["22.35"] == 9


def test_load_framework_tiers_buckets_by_tier(
    hermetic_paths: dict[str, Path],
) -> None:
    _seed_authoritative_sources(hermetic_paths)
    total, tiers = audit._load_framework_tiers()
    assert total == 4
    assert tiers == {1: 1, 2: 2, 3: 1}


# --------------------------------------------------------------------- #
# audit() — UC count findings
# --------------------------------------------------------------------- #


def test_audit_body_ships_phrase_matches_truth_returns_no_finding(
    hermetic_paths: dict[str, Path],
) -> None:
    _seed_authoritative_sources(
        hermetic_paths, sub_counts={"22.1": 10}
    )
    text = "Today §22.1 ships 10 dedicated detections."
    findings = audit.audit(text)
    assert findings == []


def test_audit_body_ships_phrase_mismatch_returns_high(
    hermetic_paths: dict[str, Path],
) -> None:
    _seed_authoritative_sources(
        hermetic_paths, sub_counts={"22.1": 10}
    )
    text = "Today §22.1 ships 7 dedicated detections."
    findings = audit.audit(text)
    assert any(
        f.severity == "HIGH"
        and f.category == "uc-count-body"
        and "22.1" in f.message
        for f in findings
    )


def test_audit_paren_dedicated_uses_preceding_section_context(
    hermetic_paths: dict[str, Path],
) -> None:
    """Pattern: ``§22.2 ... (3 dedicated UCs)`` — the count must be
    matched against the *nearest preceding* ``§22.X`` token."""

    _seed_authoritative_sources(
        hermetic_paths, sub_counts={"22.2": 5}
    )
    text = "Some intro. §22.2 has detail in (3 dedicated UCs)."
    findings = audit.audit(text)
    assert any(
        f.category == "uc-count-body" and "22.2" in f.message
        for f in findings
    )


def test_audit_paren_dedicated_without_context_is_skipped(
    hermetic_paths: dict[str, Path],
) -> None:
    """If no ``§22.X`` precedes the parenthesised count, the audit
    cannot resolve which subcategory the claim refers to and must
    silently skip it (not crash, not false-positive)."""

    _seed_authoritative_sources(
        hermetic_paths, sub_counts={"22.1": 10}
    )
    text = "Unrelated paragraph with (4 native UCs) but no section ref."
    findings = audit.audit(text)
    assert findings == []


def test_audit_appendix_a_table_mismatch_returns_high(
    hermetic_paths: dict[str, Path],
) -> None:
    _seed_authoritative_sources(
        hermetic_paths, sub_counts={"22.3": 12}
    )
    text = (
        "Some intro.\n\n"
        "| Sub | Title | Class | Owner | Count |\n"
        "|-----|-------|-------|-------|-------|\n"
        "| 22.3 | ISO 27001 | reg | sec | 8 |\n"
    )
    findings = audit.audit(text)
    assert any(
        f.severity == "HIGH"
        and f.category == "uc-count-table"
        and "22.3" in f.message
        for f in findings
    )


# --------------------------------------------------------------------- #
# audit() — framework total findings
# --------------------------------------------------------------------- #


def test_audit_framework_total_mismatch_returns_high(
    hermetic_paths: dict[str, Path],
) -> None:
    _seed_authoritative_sources(hermetic_paths)  # 4 frameworks
    text = "Our 7-framework inventory is the reference set."
    findings = audit.audit(text)
    assert any(
        f.severity == "HIGH" and f.category == "framework-total"
        for f in findings
    )


def test_audit_tier2_intro_mismatch_returns_high(
    hermetic_paths: dict[str, Path],
) -> None:
    _seed_authoritative_sources(hermetic_paths)  # tier 2 = 2
    text = "We added an additional 5 tier-2 frameworks last quarter."
    findings = audit.audit(text)
    assert any(
        f.severity == "HIGH" and f.category == "tier2-count"
        for f in findings
    )


def test_audit_tier2_badge_mismatch_returns_high(
    hermetic_paths: dict[str, Path],
) -> None:
    _seed_authoritative_sources(hermetic_paths)  # tier 2 = 2
    text = "**Tier 2** premium content; 56 frameworks are covered."
    findings = audit.audit(text)
    assert any(
        f.severity == "HIGH" and f.category == "tier2-badge"
        for f in findings
    )


def test_audit_tier3_badge_mismatch_returns_high(
    hermetic_paths: dict[str, Path],
) -> None:
    _seed_authoritative_sources(hermetic_paths)  # tier 3 = 1
    text = "**Tier 3** emerging coverage; 9 today across regions."
    findings = audit.audit(text)
    assert any(
        f.severity == "HIGH" and f.category == "tier3-badge"
        for f in findings
    )


# --------------------------------------------------------------------- #
# audit() — file refs and phase jargon
# --------------------------------------------------------------------- #


def test_audit_dead_file_ref_returns_high(
    hermetic_paths: dict[str, Path],
) -> None:
    _seed_authoritative_sources(hermetic_paths)
    text = "See `data/no-such-file.json` for details."
    findings = audit.audit(text)
    assert any(
        f.severity == "HIGH" and f.category == "dead-file-ref"
        for f in findings
    )


def test_audit_existing_file_ref_no_finding(
    hermetic_paths: dict[str, Path],
) -> None:
    """The regulations.json the audit just wrote MUST resolve cleanly."""

    _seed_authoritative_sources(hermetic_paths)
    text = "See `data/regulations.json` for the source of truth."
    findings = audit.audit(text)
    dead = [f for f in findings if f.category == "dead-file-ref"]
    assert dead == []


def test_audit_glob_style_file_ref_is_skipped(
    hermetic_paths: dict[str, Path],
) -> None:
    _seed_authoritative_sources(hermetic_paths)
    text = (
        "See `data/crosswalks/*.json` (any crosswalk file) and "
        "`data/profiles/{vendor}.json` (templated)."
    )
    findings = audit.audit(text)
    dead = [f for f in findings if f.category == "dead-file-ref"]
    assert dead == []


def test_audit_phase_jargon_returns_med(
    hermetic_paths: dict[str, Path],
) -> None:
    _seed_authoritative_sources(hermetic_paths)
    text = "Phase 4.2 shipped the cross-walk; Phase 5.1 is pending."
    findings = audit.audit(text)
    phase = [f for f in findings if f.category == "phase-jargon"]
    assert len(phase) == 2
    assert all(f.severity == "MED" for f in phase)


def test_audit_clean_primer_returns_no_findings(
    hermetic_paths: dict[str, Path],
) -> None:
    _seed_authoritative_sources(
        hermetic_paths,
        sub_counts={"22.1": 4, "22.2": 6},
        frameworks=[{"tier": 1}, {"tier": 2}, {"tier": 3}],
    )
    text = (
        "Our 3-framework inventory underpins the primer.\n"
        "§22.1 ships 4 dedicated detections.\n"
        "§22.2 ships 6 dedicated detections.\n"
        "See `data/regulations.json` for the source of truth.\n"
    )
    assert audit.audit(text) == []


# --------------------------------------------------------------------- #
# Finding.human — formatting contract
# --------------------------------------------------------------------- #


def test_finding_human_includes_line_when_present() -> None:
    f = audit.Finding(
        severity="HIGH",
        category="x",
        message="msg",
        line=42,
    )
    out = f.human()
    assert "(line 42)" in out
    assert "[HIGH]" in out
    assert "[x]" in out


def test_finding_human_omits_line_when_zero() -> None:
    f = audit.Finding(severity="LOW", category="x", message="msg")
    assert "line" not in f.human()


# --------------------------------------------------------------------- #
# main — CLI contract
# --------------------------------------------------------------------- #


def _write_primer(paths: dict[str, Path], text: str) -> None:
    paths["primer"].write_text(text, encoding="utf-8")


def test_main_default_returns_zero_even_with_findings(
    hermetic_paths: dict[str, Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed_authoritative_sources(hermetic_paths)
    _write_primer(
        hermetic_paths,
        "Phase 4.2 reference (jargon, MED).",
    )
    rc = audit.main([])
    out = capsys.readouterr().out
    assert rc == 0  # default mode is report-only
    assert "Findings" in out


def test_main_check_returns_one_on_high(
    hermetic_paths: dict[str, Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed_authoritative_sources(hermetic_paths)
    _write_primer(
        hermetic_paths,
        "Our 99-framework inventory is wrong.",
    )
    rc = audit.main(["--check"])
    assert rc == 1
    out = capsys.readouterr().out
    assert "framework-total" in out or "HIGH" in out


def test_main_check_returns_zero_when_only_med_findings(
    hermetic_paths: dict[str, Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--check`` fails ONLY on HIGH; MED-only is still green."""

    _seed_authoritative_sources(hermetic_paths)
    _write_primer(
        hermetic_paths,
        "Phase 4.2 jargon should be reworded.",
    )
    rc = audit.main(["--check"])
    assert rc == 0


def test_main_strict_returns_one_on_med(
    hermetic_paths: dict[str, Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed_authoritative_sources(hermetic_paths)
    _write_primer(
        hermetic_paths,
        "Phase 4.2 jargon.",
    )
    rc = audit.main(["--strict"])
    assert rc == 1


def test_main_json_emits_parseable_payload(
    hermetic_paths: dict[str, Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed_authoritative_sources(hermetic_paths)
    _write_primer(
        hermetic_paths,
        "Phase 4.2 jargon and 99-framework inventory.",
    )
    rc = audit.main(["--json"])
    out = capsys.readouterr().out
    assert rc == 0
    parsed = json.loads(out)
    assert isinstance(parsed, list) and parsed
    severities = {f["severity"] for f in parsed}
    categories = {f["category"] for f in parsed}
    assert "HIGH" in severities
    assert "MED" in severities
    assert "framework-total" in categories
    assert "phase-jargon" in categories


def test_main_clean_primer_prints_all_match(
    hermetic_paths: dict[str, Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed_authoritative_sources(
        hermetic_paths,
        sub_counts={"22.1": 4},
        frameworks=[{"tier": 1}],
    )
    _write_primer(
        hermetic_paths,
        "Our 1-framework inventory grew. §22.1 ships 4 dedicated.\n",
    )
    rc = audit.main([])
    out = capsys.readouterr().out
    assert rc == 0
    assert "All primer claims match" in out
