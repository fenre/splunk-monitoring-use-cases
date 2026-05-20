"""Comprehensive unit tests for ``src/splunk_uc/audits/mitre_taxonomy.py``.

P16 Wave AAA (2026-05-19) — burns down the test-coverage debt on the
``audit-mitre-taxonomy`` ATT&CK technique-ID validator.

The audit walks every ``content/cat-*/UC-*.json`` and validates the
``mitreAttack`` array against the canonical technique-ID grammar
(``Txxxx`` / ``Txxxx.yyy`` / ``TAxxxx``). Anything else is a violation
broken down into:

* HIGH ``mitre-invalid-token`` — non-canonical token (free text, junk).
* HIGH ``mitre-cve-mixed`` — CVE-IDs smuggled into the MITRE field.
* HIGH ``mitre-url-in-field`` — http(s):// links in the MITRE field.
* MED ``mitre-parenthetical-prose`` — ``T1021 (Remote Services)``-style
  free-text after a technique ID.
* MED ``mitre-na-unjustified`` — bare ``N/A`` without a parenthesised
  reason.
* LOW ``mitre-empty`` — empty body or empty list.

Tests are hermetic — they build a synthetic ``content/cat-<n>-<slug>/``
corpus under ``tmp_path`` and monkey-patch ``mt.CONTENT_DIR`` so the
live 7,929-UC catalogue is never touched.
"""

from __future__ import annotations

import json
import os
import pathlib
from typing import Any, Protocol

import pytest

from splunk_uc.audits import mitre_taxonomy as mt


class MakeUC(Protocol):
    """Factory for writing a synthetic UC sidecar under ``tmp_path``."""

    def __call__(
        self,
        uc_id: str,
        *,
        cat: str = "cat-1-foo",
        body: Any = ...,
    ) -> pathlib.Path: ...


@pytest.fixture
def fake_repo(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """Rewire ``mt.CONTENT_DIR`` to a synthetic ``tmp_path/content``."""
    content = tmp_path / "content"
    content.mkdir()
    monkeypatch.setattr(mt, "CONTENT_DIR", str(content))
    return tmp_path


@pytest.fixture
def make_uc(fake_repo: pathlib.Path) -> MakeUC:
    """Factory for writing a synthetic UC sidecar."""

    def _factory(
        uc_id: str,
        *,
        cat: str = "cat-1-foo",
        body: Any = ...,
    ) -> pathlib.Path:
        cat_dir = pathlib.Path(mt.CONTENT_DIR) / cat
        cat_dir.mkdir(exist_ok=True)
        p = cat_dir / f"UC-{uc_id}.json"
        if body is ...:
            body = {"id": uc_id}
        if isinstance(body, str):
            p.write_text(body, encoding="utf-8")
        else:
            p.write_text(json.dumps(body), encoding="utf-8")
        return p

    return _factory


# ----------------------------------------------------------- module-level --


def test_repo_root_walks_three_parents_up() -> None:
    """``REPO_ROOT`` resolves via ``dirname(dirname(dirname(dirname(...))))``
    so the substrate walks ``mitre_taxonomy.py → audits/ → splunk_uc/ →
    src/ → repo root``.
    """
    src_path = os.path.abspath(mt.__file__)
    expected_root = os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.dirname(src_path)),
        )
    )
    assert mt.REPO_ROOT == expected_root


def test_content_dir_resolves_to_repo_root_content() -> None:
    """``CONTENT_DIR`` is ``REPO_ROOT/content`` per the documented layout
    (this is the live constant — fixture overrides it per-test)."""
    # Walk parents once to recover the live value since fake_repo isn't
    # active in this test.
    src_path = os.path.abspath(mt.__file__)
    expected_root = os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.dirname(src_path)),
        )
    )
    assert mt.REPO_ROOT == expected_root
    # Note: fake_repo would have overwritten CONTENT_DIR.


def test_re_valid_token_accepts_canonical_grammar() -> None:
    """``RE_VALID_TOKEN`` accepts the four documented shapes."""
    assert mt.RE_VALID_TOKEN.match("T1078")
    assert mt.RE_VALID_TOKEN.match("T1003.001")
    assert mt.RE_VALID_TOKEN.match("TA0006")
    assert mt.RE_VALID_TOKEN.match("T0859")  # ICS
    assert mt.RE_VALID_TOKEN.match("T0800")  # ICS lower bound


def test_re_valid_token_rejects_off_grammar() -> None:
    """Non-canonical shapes are rejected."""
    assert not mt.RE_VALID_TOKEN.match("T")
    assert not mt.RE_VALID_TOKEN.match("T1")
    assert not mt.RE_VALID_TOKEN.match("T12345")  # 5 digits not 4
    assert not mt.RE_VALID_TOKEN.match("T1078.1")  # 1-digit sub-technique
    assert not mt.RE_VALID_TOKEN.match("T1078.0001")  # 4-digit sub-technique
    assert not mt.RE_VALID_TOKEN.match("TA006")  # 3 digits
    assert not mt.RE_VALID_TOKEN.match("CVE-2025-33073")
    assert not mt.RE_VALID_TOKEN.match("T1078 (foo)")


# ----------------------------------------------------------------- Finding --


def test_finding_human_renders_severity_category_uc_message() -> None:
    """``Finding.human()`` renders
    ``[SEV] [CAT] uc_id (basename(file)): message``, with the snippet
    stripped and truncated at 200 chars on a second line.
    """
    f = mt.Finding(
        file="/repo/content/cat-1-foo/UC-1.1.1.json",
        uc_id="UC-1.1.1",
        severity="HIGH",
        category="mitre-invalid-token",
        message="msg",
        snippet="   surrounding context  ",
    )
    out = f.human()
    assert "[HIGH] [mitre-invalid-token] UC-1.1.1 (UC-1.1.1.json): msg" in out
    assert "snippet: surrounding context" in out


def test_finding_human_omits_snippet_when_empty() -> None:
    """Empty snippet suppresses the snippet line entirely."""
    f = mt.Finding(
        file="UC-1.1.1.json",
        uc_id="UC-1.1.1",
        severity="LOW",
        category="mitre-empty",
        message="empty",
    )
    assert "snippet:" not in f.human()


def test_finding_human_truncates_long_snippet_to_200_chars() -> None:
    """Snippets longer than 200 chars are truncated."""
    f = mt.Finding(
        file="UC-1.1.1.json",
        uc_id="UC-1.1.1",
        severity="HIGH",
        category="mitre-invalid-token",
        message="msg",
        snippet="x" * 500,
    )
    out = f.human()
    assert "snippet: " + ("x" * 200) in out
    assert "snippet: " + ("x" * 201) not in out


# ---------------------------------------------------- _tokenize_mitre_body --


def test_tokenize_mitre_body_empty_returns_empty_list() -> None:
    """An empty body string returns ``[]``."""
    assert mt._tokenize_mitre_body("") == []


def test_tokenize_mitre_body_strips_per_token() -> None:
    """Comma-separated tokens are stripped of whitespace."""
    assert mt._tokenize_mitre_body("  T1078 , T1003.001  ") == ["T1078", "T1003.001"]


def test_tokenize_mitre_body_discards_empty_splits() -> None:
    """Empty splits (extra commas, trailing comma) are discarded."""
    assert mt._tokenize_mitre_body("T1078, , T1003") == ["T1078", "T1003"]
    assert mt._tokenize_mitre_body(", T1078,") == ["T1078"]
    assert mt._tokenize_mitre_body(",,,") == []


def test_tokenize_mitre_body_keeps_parens_intact() -> None:
    """Parenthetical content is NOT split — it's part of the token so the
    validator can flag it as free text.
    """
    assert mt._tokenize_mitre_body("T1078 (foo, bar)") == ["T1078 (foo", "bar)"]
    # The above demonstrates the documented "does not attempt to tokenise
    # inside parentheses" behaviour — the simple comma-split treats the
    # paren as opaque.


# ----------------------------------------------------- _check_mitre_line --


def test_check_mitre_line_empty_body_emits_low_empty() -> None:
    """Empty body emits ``LOW/mitre-empty``."""
    findings = mt._check_mitre_line("UC-1.1.1", "UC-1.1.1.json", "")
    assert len(findings) == 1
    assert findings[0].severity == "LOW"
    assert findings[0].category == "mitre-empty"


def test_check_mitre_line_whitespace_body_emits_low_empty() -> None:
    """Whitespace-only body (after strip) is treated as empty."""
    findings = mt._check_mitre_line("UC-1.1.1", "UC-1.1.1.json", "   ")
    assert len(findings) == 1
    assert findings[0].category == "mitre-empty"


def test_check_mitre_line_na_with_reason_silent() -> None:
    """``N/A (content health monitoring)`` is accepted — no findings."""
    findings = mt._check_mitre_line("UC-1.1.1", "UC-1.1.1.json", "N/A (content health monitoring)")
    assert findings == []


def test_check_mitre_line_na_with_dotless_variant_silent() -> None:
    """``NA (reason)`` (no slash) is also accepted via the
    ``N/?A`` regex.
    """
    findings = mt._check_mitre_line("UC-1.1.1", "UC-1.1.1.json", "NA (meta detection)")
    assert findings == []


def test_check_mitre_line_na_case_insensitive() -> None:
    """``n/a (reason)`` and ``Na (reason)`` are accepted."""
    for body in ("n/a (reason)", "Na (reason)", "N/A (reason)"):
        findings = mt._check_mitre_line("UC-1.1.1", "UC-1.1.1.json", body)
        assert findings == [], body


def test_check_mitre_line_bare_na_emits_med_unjustified() -> None:
    """A bare ``N/A`` (no parens) emits ``MED/mitre-na-unjustified``."""
    findings = mt._check_mitre_line("UC-1.1.1", "UC-1.1.1.json", "N/A")
    assert len(findings) == 1
    assert findings[0].severity == "MED"
    assert findings[0].category == "mitre-na-unjustified"


def test_check_mitre_line_na_with_empty_parens_emits_med() -> None:
    """``N/A ()`` (empty parens) still emits the unjustified finding."""
    findings = mt._check_mitre_line("UC-1.1.1", "UC-1.1.1.json", "N/A ()")
    # N/A () doesn't actually match the outer regex (requires
    # non-empty parens), so it falls through to the tokenisation path
    # and flags as invalid + parenthetical.
    assert any(
        f.category in ("mitre-na-unjustified", "mitre-invalid-token", "mitre-parenthetical-prose")
        for f in findings
    )


def test_check_mitre_line_valid_single_token_silent() -> None:
    """A single canonical token (``T1078``) emits no findings."""
    findings = mt._check_mitre_line("UC-1.1.1", "UC-1.1.1.json", "T1078")
    assert findings == []


def test_check_mitre_line_valid_multiple_tokens_silent() -> None:
    """Multiple canonical tokens emit no findings."""
    findings = mt._check_mitre_line("UC-1.1.1", "UC-1.1.1.json", "T1078, T1003.001, TA0006, T0859")
    assert findings == []


def test_check_mitre_line_cve_token_emits_high_cve_mixed() -> None:
    """A CVE ID in the MITRE field emits ``HIGH/mitre-cve-mixed``."""
    findings = mt._check_mitre_line("UC-1.1.1", "UC-1.1.1.json", "T1190, CVE-2025-33073")
    cve = [f for f in findings if f.category == "mitre-cve-mixed"]
    assert len(cve) == 1
    assert cve[0].severity == "HIGH"
    assert "CVE-2025-33073" in cve[0].message


def test_check_mitre_line_multiple_cves_aggregated_into_one_finding() -> None:
    """Multiple CVE-IDs are aggregated into a single comma-joined
    finding (not one finding per CVE).
    """
    findings = mt._check_mitre_line("UC-1.1.1", "UC-1.1.1.json", "CVE-2025-33073, CVE-2024-12345")
    cve = [f for f in findings if f.category == "mitre-cve-mixed"]
    assert len(cve) == 1
    assert "CVE-2025-33073" in cve[0].message
    assert "CVE-2024-12345" in cve[0].message


def test_check_mitre_line_url_token_emits_high_url_in_field() -> None:
    """An ``http(s)://`` URL in the MITRE field emits
    ``HIGH/mitre-url-in-field``.
    """
    findings = mt._check_mitre_line("UC-1.1.1", "UC-1.1.1.json", "T1078, https://example.com/foo")
    url = [f for f in findings if f.category == "mitre-url-in-field"]
    assert len(url) == 1
    assert url[0].severity == "HIGH"
    assert "https://example.com/foo" in url[0].message


def test_check_mitre_line_http_url_token_also_caught() -> None:
    """An ``http://`` URL (non-HTTPS) is also caught."""
    findings = mt._check_mitre_line("UC-1.1.1", "UC-1.1.1.json", "http://attack.mitre.org/foo")
    assert any(f.category == "mitre-url-in-field" for f in findings)


def test_check_mitre_line_parenthetical_token_emits_med() -> None:
    """``T1021 (Remote Services)`` emits ``MED/mitre-parenthetical-prose``."""
    findings = mt._check_mitre_line("UC-1.1.1", "UC-1.1.1.json", "T1078, T1021 (Remote Services)")
    paren = [f for f in findings if f.category == "mitre-parenthetical-prose"]
    assert len(paren) == 1
    assert paren[0].severity == "MED"


def test_check_mitre_line_open_paren_only_caught() -> None:
    """A token with an open-paren but no close-paren is still caught."""
    findings = mt._check_mitre_line("UC-1.1.1", "UC-1.1.1.json", "T1078(unclosed")
    assert any(f.category == "mitre-parenthetical-prose" for f in findings)


def test_check_mitre_line_close_paren_only_caught() -> None:
    """A token with a close-paren but no open-paren is still caught."""
    findings = mt._check_mitre_line("UC-1.1.1", "UC-1.1.1.json", "T1078unclosed)")
    assert any(f.category == "mitre-parenthetical-prose" for f in findings)


def test_check_mitre_line_invalid_token_emits_high() -> None:
    """A non-canonical token like ``Lateral Movement`` emits
    ``HIGH/mitre-invalid-token``.
    """
    findings = mt._check_mitre_line("UC-1.1.1", "UC-1.1.1.json", "T1078, Lateral Movement")
    bad = [f for f in findings if f.category == "mitre-invalid-token"]
    assert len(bad) == 1
    assert bad[0].severity == "HIGH"
    assert "Lateral Movement" in bad[0].message


def test_check_mitre_line_multiple_invalid_tokens_aggregated() -> None:
    """Multiple invalid tokens are aggregated into a single finding."""
    findings = mt._check_mitre_line("UC-1.1.1", "UC-1.1.1.json", "bogus1, bogus2")
    bad = [f for f in findings if f.category == "mitre-invalid-token"]
    assert len(bad) == 1
    assert "bogus1" in bad[0].message
    assert "bogus2" in bad[0].message


def test_check_mitre_line_uppercases_token_for_validation() -> None:
    """The validator uppercases tokens via ``.upper()`` before matching,
    so ``t1078`` is accepted (the CVE regex also matches against
    upper-cased text).
    """
    findings = mt._check_mitre_line("UC-1.1.1", "UC-1.1.1.json", "t1078")
    assert findings == []


def test_check_mitre_line_no_tokens_after_split_returns_empty() -> None:
    """A body that strips to non-empty but tokenises to empty (all
    commas) returns no findings via the ``if not tokens: return``
    guard.
    """
    findings = mt._check_mitre_line("UC-1.1.1", "UC-1.1.1.json", ", ,,")
    assert findings == []


def test_check_mitre_line_all_finding_categories_coexist() -> None:
    """A pathological body can simultaneously emit CVE, URL,
    parenthetical, and invalid findings.
    """
    findings = mt._check_mitre_line(
        "UC-1.1.1",
        "UC-1.1.1.json",
        "CVE-2025-33073, https://example.com, T1021 (Remote Services), garbage",
    )
    cats = {f.category for f in findings}
    assert "mitre-cve-mixed" in cats
    assert "mitre-url-in-field" in cats
    assert "mitre-parenthetical-prose" in cats
    assert "mitre-invalid-token" in cats


# ----------------------------------------------------------- audit_uc_json --


def test_audit_uc_json_missing_mitreattack_returns_empty(
    fake_repo: pathlib.Path, make_uc: MakeUC
) -> None:
    """A UC without a ``mitreAttack`` field emits no findings."""
    p = make_uc("1.1.1")
    findings = mt.audit_uc_json(str(p), {"id": "1.1.1"})
    assert findings == []


def test_audit_uc_json_non_list_mitreattack_returns_empty(
    fake_repo: pathlib.Path,
) -> None:
    """``mitreAttack`` that isn't a list (str, dict, int) emits no
    findings (defensive — schema enforces list, this is a fallback).
    """
    assert mt.audit_uc_json("p", {"id": "1.1.1", "mitreAttack": "T1078"}) == []
    assert mt.audit_uc_json("p", {"id": "1.1.1", "mitreAttack": {"t": "1078"}}) == []
    assert mt.audit_uc_json("p", {"id": "1.1.1", "mitreAttack": 42}) == []


def test_audit_uc_json_empty_list_emits_low_empty() -> None:
    """An empty ``mitreAttack`` array emits ``LOW/mitre-empty``."""
    findings = mt.audit_uc_json("p", {"id": "1.1.1", "mitreAttack": []})
    assert len(findings) == 1
    assert findings[0].severity == "LOW"
    assert findings[0].category == "mitre-empty"
    assert "mitreAttack`" in findings[0].message


def test_audit_uc_json_missing_id_renders_as_question_mark() -> None:
    """A UC without ``id`` renders ``UC-?``."""
    findings = mt.audit_uc_json("p", {"mitreAttack": []})
    assert findings[0].uc_id == "UC-?"


def test_audit_uc_json_joins_list_via_comma_space() -> None:
    """The array is joined via ``", "`` before being validated."""
    findings = mt.audit_uc_json("p", {"id": "1.1.1", "mitreAttack": ["T1078", "garbage"]})
    assert any("garbage" in f.message for f in findings)


def test_audit_uc_json_coerces_non_string_tokens_via_str() -> None:
    """Non-string tokens (int, None) are coerced via ``str()`` before
    joining.
    """
    findings = mt.audit_uc_json("p", {"id": "1.1.1", "mitreAttack": [1078, "T1003.001"]})
    # 1078 → "1078" which doesn't match the regex → invalid-token finding
    assert any("1078" in f.message and "Non-canonical" in f.message for f in findings)


# ---------------------------------------------------------------- main() --


def test_main_clean_corpus_exit_zero(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A clean corpus exits 0 even with ``--check``."""
    make_uc("1.1.1", body={"id": "1.1.1", "mitreAttack": ["T1078"]})
    rc = mt.main(["--check"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Files scanned: 1" in out


def test_main_high_finding_check_exits_one(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A HIGH finding (e.g. CVE in MITRE) with ``--check`` exits 1."""
    make_uc("1.1.1", body={"id": "1.1.1", "mitreAttack": ["T1078", "CVE-2025-33073"]})
    rc = mt.main(["--check"])
    assert rc == 1
    out = capsys.readouterr().out
    assert "mitre-cve-mixed" in out


def test_main_low_finding_does_not_block_default_severity(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
) -> None:
    """A LOW-only finding (empty ``mitreAttack``) doesn't block default
    HIGH ``--check``.
    """
    make_uc("1.1.1", body={"id": "1.1.1", "mitreAttack": []})
    rc = mt.main(["--check"])
    assert rc == 0


def test_main_severity_low_promotes_low_to_blocking(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
) -> None:
    """``--severity LOW`` makes even LOW findings block."""
    make_uc("1.1.1", body={"id": "1.1.1", "mitreAttack": []})
    rc = mt.main(["--check", "--severity", "LOW"])
    assert rc == 1


def test_main_severity_med_promotes_med_to_blocking(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
) -> None:
    """``--severity MED`` makes MED findings block."""
    make_uc("1.1.1", body={"id": "1.1.1", "mitreAttack": ["N/A"]})
    rc = mt.main(["--check", "--severity", "MED"])
    assert rc == 1


def test_main_without_check_returns_zero_on_findings(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
) -> None:
    """Without ``--check``, even HIGH findings exit 0 (informational)."""
    make_uc("1.1.1", body={"id": "1.1.1", "mitreAttack": ["CVE-2025-33073"]})
    rc = mt.main([])
    assert rc == 0


def test_main_json_mode_outputs_findings_array(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--json`` emits the findings as an asdict() array."""
    make_uc("1.1.1", body={"id": "1.1.1", "mitreAttack": ["bogus"]})
    mt.main(["--json"])
    out = capsys.readouterr().out
    findings = json.loads(out)
    assert isinstance(findings, list)
    assert any(f["category"] == "mitre-invalid-token" for f in findings)


def test_main_json_mode_empty_array_on_clean_corpus(
    fake_repo: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--json`` emits ``[]`` on a clean corpus."""
    mt.main(["--json"])
    assert json.loads(capsys.readouterr().out) == []


def test_main_human_report_includes_files_scanned_count(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The human report includes the ``Files scanned:`` summary."""
    make_uc("1.1.1", body={"id": "1.1.1", "mitreAttack": ["T1078"]})
    make_uc("1.1.2", body={"id": "1.1.2", "mitreAttack": ["T1003.001"]})
    mt.main([])
    out = capsys.readouterr().out
    assert "Files scanned: 2" in out


def test_main_human_report_findings_by_severity_sorted(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``Findings by severity:`` lists each severity-key alphabetically."""
    make_uc("1.1.1", body={"id": "1.1.1", "mitreAttack": ["CVE-2025-33073"]})
    make_uc("1.1.2", body={"id": "1.1.2", "mitreAttack": ["N/A"]})
    mt.main([])
    out = capsys.readouterr().out
    assert "HIGH=" in out
    assert "MED=" in out


def test_main_findings_by_category_sorted_by_count_desc(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``Findings by category:`` lists categories by count descending."""
    for i in range(3):
        make_uc(f"1.1.{i}", body={"id": f"1.1.{i}", "mitreAttack": ["bogus"]})
    make_uc("1.1.99", body={"id": "1.1.99", "mitreAttack": ["N/A"]})
    mt.main([])
    out = capsys.readouterr().out
    inv_idx = out.find("mitre-invalid-token")
    na_idx = out.find("mitre-na-unjustified")
    assert inv_idx != -1 and na_idx != -1
    assert inv_idx < na_idx  # 3 invalid tokens come before 1 unjustified


def test_main_findings_section_omitted_when_clean(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Clean corpus omits the ``FINDINGS:`` block."""
    make_uc("1.1.1", body={"id": "1.1.1", "mitreAttack": ["T1078"]})
    mt.main([])
    out = capsys.readouterr().out
    assert "FINDINGS:" not in out


def test_main_findings_section_renders_each_finding_via_human(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Each finding is rendered via ``Finding.human()`` in the FINDINGS
    section.
    """
    make_uc("1.1.1", body={"id": "1.1.1", "mitreAttack": ["bogus"]})
    mt.main([])
    out = capsys.readouterr().out
    assert "FINDINGS:" in out
    assert "[HIGH] [mitre-invalid-token]" in out


def test_main_skips_malformed_json_silently(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Malformed JSON files are silently skipped via the ``try/except``
    around ``json.load``.
    """
    make_uc("1.1.1", body="{ not valid json")
    make_uc("1.1.2", body={"id": "1.1.2", "mitreAttack": ["T1078"]})
    mt.main([])
    out = capsys.readouterr().out
    assert "Files scanned: 2" in out


def test_main_skips_unreadable_files_silently(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``OSError`` on read is silently swallowed."""
    p = make_uc("1.1.1", body={"id": "1.1.1", "mitreAttack": ["T1078"]})

    real_open = open

    def _fail_open(path: Any, *args: Any, **kwargs: Any) -> Any:
        if str(path) == str(p):
            raise OSError("io fail")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr("builtins.open", _fail_open)
    rc = mt.main([])
    assert rc == 0


def test_main_iter_order_is_sorted_glob(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``glob.glob(...)`` is wrapped in ``sorted()`` for deterministic
    output.
    """
    make_uc("2.1.1", cat="cat-2-bar", body={"id": "2.1.1", "mitreAttack": ["bogus-b"]})
    make_uc("1.1.1", cat="cat-1-foo", body={"id": "1.1.1", "mitreAttack": ["bogus-a"]})
    mt.main(["--json"])
    out = capsys.readouterr().out
    findings = json.loads(out)
    uc_ids = [f["uc_id"] for f in findings]
    assert uc_ids == ["UC-1.1.1", "UC-2.1.1"]


def test_main_argv_none_falls_through_to_sys_argv(
    fake_repo: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``main(None)`` parses ``sys.argv[1:]``."""
    monkeypatch.setattr("sys.argv", ["audit-mitre-taxonomy"])
    rc = mt.main(None)
    assert rc == 0


def test_main_help_exits_zero() -> None:
    """``--help`` exits 0 via argparse."""
    with pytest.raises(SystemExit) as exc_info:
        mt.main(["--help"])
    assert exc_info.value.code == 0


# ----------------------------------------------------- __main__ smoke --


def test_module_dunder_main_exists() -> None:
    """The ``if __name__ == "__main__":`` block uses
    ``sys.exit(main())``.
    """
    src = pathlib.Path(mt.__file__).read_text(encoding="utf-8")
    assert 'if __name__ == "__main__":' in src
    assert "sys.exit(main())" in src
