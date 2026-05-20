"""Comprehensive unit tests for ``src/splunk_uc/audits/meraki_spl.py``.

P16 Wave YY (2026-05-19) — burns down the test-coverage debt on the
``audit-meraki-spl`` Meraki-specific SPL hallucination guard.

The audit performs three orthogonal classes of check against every UC
sidecar whose ``app`` references the Meraki TA (Splunkbase 5580) or
whose ``spl`` queries a Meraki sourcetype:

1. **Sourcetype invariant**: every ``sourcetype=meraki:<X>`` (or bare
   ``meraki`` / ``cisco:meraki``) reference must be one of the
   canonical sourcetypes shipped by ``Splunk_TA_cisco_meraki`` or the
   SC4S Meraki vendor pack. Wildcard sourcetypes are skipped.
2. **Index-sourcetype consistency**: ``index=meraki`` or
   ``index=cisco_meraki`` must pair with a Meraki-named sourcetype
   within the next 200 characters.
3. **Hallucinated field guard**: a small set of historically-introduced
   hallucinated fields (``compliance_status``, ``compliance_reason``,
   ``people_count``, ``quality_score``, ``archive_status``,
   ``night_mode``, ``power_watts``) are only allowed if the SPL itself
   creates them via ``eval``, ``rename ... as``, or ``stats ... as``.
   The guard only fires inside SPL blobs that actually reference a
   Meraki sourcetype (``has_meraki_st`` gate).

Tests are hermetic — they build a synthetic ``content/cat-<n>-<slug>/``
corpus under ``tmp_path`` and monkey-patch ``meraki_spl.REPO`` and
``meraki_spl.CONTENT`` so the live 7,929-UC catalogue is never touched.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any, Protocol

import pytest

from splunk_uc.audits import meraki_spl as ms


class MakeUC(Protocol):
    """Factory for writing a synthetic UC sidecar under ``tmp_path``."""

    def __call__(
        self,
        uc_id: str,
        *,
        cat: str = "cat-1-meraki",
        app: Any = ...,
        spl: Any = ...,
        cim_spl: Any = ...,
        body: Any = ...,
    ) -> pathlib.Path: ...


@pytest.fixture
def fake_repo(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """Rewire ``meraki_spl.REPO`` and ``meraki_spl.CONTENT`` to ``tmp_path``."""
    content = tmp_path / "content"
    content.mkdir()
    monkeypatch.setattr(ms, "REPO", tmp_path)
    monkeypatch.setattr(ms, "CONTENT", content)
    return tmp_path


@pytest.fixture
def make_uc(fake_repo: pathlib.Path) -> MakeUC:
    """Factory for writing a synthetic UC sidecar."""

    def _factory(
        uc_id: str,
        *,
        cat: str = "cat-1-meraki",
        app: Any = ...,
        spl: Any = ...,
        cim_spl: Any = ...,
        body: Any = ...,
    ) -> pathlib.Path:
        cat_dir: pathlib.Path = ms.CONTENT / cat
        cat_dir.mkdir(exist_ok=True)
        p: pathlib.Path = cat_dir / f"UC-{uc_id}.json"
        if body is not ...:
            if isinstance(body, str):
                p.write_text(body, encoding="utf-8")
            else:
                p.write_text(json.dumps(body), encoding="utf-8")
            return p
        payload: dict[str, Any] = {"id": uc_id}
        if app is not ...:
            payload["app"] = app
        if spl is not ...:
            payload["spl"] = spl
        if cim_spl is not ...:
            payload["cimSpl"] = cim_spl
        p.write_text(json.dumps(payload), encoding="utf-8")
        return p

    return _factory


# ----------------------------------------------------------- module-level --


def test_repo_and_content_paths_are_3_levels_up_from_module() -> None:
    """Per ADR-0009, ``REPO`` resolves via ``parents[3]`` so the substrate
    walks ``meraki_spl.py → audits/ → splunk_uc/ → src/ → repo root``.
    """
    src_path = pathlib.Path(ms.__file__).resolve()
    assert src_path.parents[3].name == "splunk-monitoring-use-cases"


def test_canonical_sourcetypes_contains_documented_taxonomy() -> None:
    """The 35+ canonical Meraki sourcetypes must include the SC4S syslog
    triple, the modular-input ``meraki:sm:devices`` pattern, the API
    history triple, and a sampling of the documented TA sourcetypes.
    """
    assert "meraki" in ms.CANONICAL_SOURCETYPES
    assert "cisco:meraki" in ms.CANONICAL_SOURCETYPES
    assert "meraki:syslog" in ms.CANONICAL_SOURCETYPES
    assert "meraki:sm:devices" in ms.CANONICAL_SOURCETYPES
    assert "meraki:apirequestshistory" in ms.CANONICAL_SOURCETYPES
    assert "meraki:apirequestsoverview" in ms.CANONICAL_SOURCETYPES
    assert "meraki:apirequestsresponsecodes" in ms.CANONICAL_SOURCETYPES
    assert "meraki:webhook" in ms.CANONICAL_SOURCETYPES
    assert "meraki:webhooklogs:api" in ms.CANONICAL_SOURCETYPES
    assert len(ms.CANONICAL_SOURCETYPES) >= 35


def test_canonical_indexes_is_six_documented_entries() -> None:
    """The 6 canonical indexes are: meraki, cisco_meraki, cisco_network,
    wireless, network, cisco_security.
    """
    assert ms.CANONICAL_INDEXES == {
        "meraki",
        "cisco_meraki",
        "cisco_network",
        "wireless",
        "network",
        "cisco_security",
    }


def test_hallucinated_fields_excludes_co2_ppm_and_noise_db() -> None:
    """``co2_ppm`` and ``noise_db`` are legitimate BMS/Airthings/Awair
    field names; they are NOT Meraki MT hallucinations and must be
    absent from the guard set (per the inline comment).
    """
    assert ms.HALLUCINATED_FIELDS == {
        "compliance_status",
        "compliance_reason",
        "people_count",
        "quality_score",
        "archive_status",
        "night_mode",
        "power_watts",
    }
    assert "co2_ppm" not in ms.HALLUCINATED_FIELDS
    assert "noise_db" not in ms.HALLUCINATED_FIELDS


def test_re_sourcetype_matches_quoted_and_unquoted() -> None:
    """``RE_SOURCETYPE`` accepts both ``sourcetype="meraki:devices"`` and
    ``sourcetype=meraki:devices`` (no quotes) and tolerates whitespace
    around the ``=``.
    """
    m1 = ms.RE_SOURCETYPE.search('sourcetype="meraki:devices"')
    assert m1 is not None
    assert m1.group(1) == "meraki:devices"
    m2 = ms.RE_SOURCETYPE.search("sourcetype = meraki:devices")
    assert m2 is not None
    assert m2.group(2) == "meraki:devices"


def test_re_index_matches_quoted_and_unquoted() -> None:
    """``RE_INDEX`` accepts both ``index="meraki"`` and ``index=meraki``."""
    m1 = ms.RE_INDEX.search('index="meraki"')
    assert m1 is not None
    assert m1.group(1) == "meraki"
    m2 = ms.RE_INDEX.search("index=cisco_meraki")
    assert m2 is not None
    assert m2.group(2) == "cisco_meraki"


def test_re_meraki_sourcetype_matches_known_variants() -> None:
    """``RE_MERAKI_SOURCETYPE`` matches bare ``meraki``, namespaced
    ``meraki:<X>``, deeply nested ``meraki:webhooklogs:api``, and
    ``cisco:meraki`` (SC4S vendor pack) — both quoted and unquoted.
    """
    assert ms.RE_MERAKI_SOURCETYPE.search('sourcetype="meraki"')
    assert ms.RE_MERAKI_SOURCETYPE.search("sourcetype=meraki")
    assert ms.RE_MERAKI_SOURCETYPE.search("sourcetype=meraki:devices")
    assert ms.RE_MERAKI_SOURCETYPE.search('sourcetype="meraki:webhooklogs:api"')
    assert ms.RE_MERAKI_SOURCETYPE.search("sourcetype=cisco:meraki")


def test_re_meraki_sourcetype_rejects_meraki_prefixed_other_vendor() -> None:
    """``meraki_something`` (underscore boundary) is NOT a meraki
    sourcetype — the negative-lookahead ``(?![A-Za-z0-9_:])`` blocks it.
    """
    assert ms.RE_MERAKI_SOURCETYPE.search("sourcetype=meraki_foo") is None
    assert ms.RE_MERAKI_SOURCETYPE.search("sourcetype=meraki123") is None


def test_finding_dataclass_human_renders_severity_category_uc_message() -> None:
    """``Finding.human()`` renders ``[SEVERITY] [CATEGORY] uc_id: message``
    + optional ``in: <snippet>`` (truncated to 160 chars) + ``file: <path>``.
    """
    f = ms.Finding(
        file="content/cat-1/UC-1.1.1.json",
        uc_id="1.1.1",
        severity="HIGH",
        category="sourcetype",
        message="unknown Meraki sourcetype",
        snippet="sourcetype=meraki:notreal",
    )
    out = f.human()
    assert "[HIGH] [sourcetype] 1.1.1: unknown Meraki sourcetype" in out
    assert "in: sourcetype=meraki:notreal" in out
    assert "file: content/cat-1/UC-1.1.1.json" in out


def test_finding_human_omits_snippet_line_when_empty() -> None:
    """When ``snippet`` is the default empty string, the ``in: ...`` line
    is suppressed entirely.
    """
    f = ms.Finding(
        file="content/cat-1/UC-1.1.1.json",
        uc_id="1.1.1",
        severity="ERROR",
        category="parse",
        message="cannot parse JSON",
    )
    assert "\n        in:" not in f.human()


def test_finding_human_truncates_long_snippet_to_160_chars() -> None:
    """Snippets are truncated to 160 chars in ``human()``."""
    long_snippet = "x" * 500
    f = ms.Finding(
        file="content/cat-1/UC-1.1.1.json",
        uc_id="1.1.1",
        severity="HIGH",
        category="sourcetype",
        message="msg",
        snippet=long_snippet,
    )
    out = f.human()
    assert "in: " + ("x" * 160) in out
    assert "in: " + ("x" * 161) not in out


# ----------------------------------------------------------- _is_meraki_uc --


def test_is_meraki_uc_via_app_field_lowercase() -> None:
    """The ``app`` field is lowercased before matching ``meraki``."""
    assert ms._is_meraki_uc({"app": "Splunk_TA_cisco_meraki"})
    assert ms._is_meraki_uc({"app": "MERAKI"})


def test_is_meraki_uc_via_app_field_splunkbase_id_5580() -> None:
    """A Splunkbase ID of ``5580`` (with no other Meraki signal) still
    flags the UC as Meraki.
    """
    assert ms._is_meraki_uc({"app": "Some custom app (Splunkbase 5580)"})


def test_is_meraki_uc_via_spl_sourcetype() -> None:
    """A UC without ``meraki`` in ``app`` but with a Meraki sourcetype in
    ``spl`` is still flagged.
    """
    assert ms._is_meraki_uc({"app": "Cisco Network App", "spl": "sourcetype=meraki:devices"})


def test_is_meraki_uc_false_for_non_meraki_uc() -> None:
    """A UC with no Meraki signal in ``app`` or ``spl`` is not Meraki."""
    assert not ms._is_meraki_uc({"app": "Splunk_TA_aws", "spl": "sourcetype=aws:cloudtrail"})


def test_is_meraki_uc_handles_missing_app_and_spl() -> None:
    """``_is_meraki_uc`` is total over arbitrary input — missing keys
    are coerced to empty strings.
    """
    assert not ms._is_meraki_uc({})


def test_is_meraki_uc_coerces_non_string_app_and_spl() -> None:
    """Non-string ``app`` and ``spl`` values are coerced via ``str()``."""
    assert ms._is_meraki_uc({"app": ["Cisco Meraki TA"], "spl": None})
    assert not ms._is_meraki_uc({"app": 42, "spl": 99})


# ----------------------------------------------------------- _scan_uc parse --


def test_scan_uc_parse_error_emits_error_finding(fake_repo: pathlib.Path, make_uc: MakeUC) -> None:
    """A malformed JSON sidecar yields a single ``ERROR/parse`` finding."""
    p = make_uc("1.1.1", body="{ not valid json")
    findings: list[ms.Finding] = []
    ms._scan_uc(p, findings)
    assert len(findings) == 1
    assert findings[0].severity == "ERROR"
    assert findings[0].category == "parse"
    assert "cannot parse JSON" in findings[0].message


def test_scan_uc_missing_id_falls_back_to_stem(fake_repo: pathlib.Path, make_uc: MakeUC) -> None:
    """A UC with no ``id`` field uses the file stem as the UC ID."""
    p = make_uc("1.1.1", body={"spl": 'sourcetype="meraki:notreal"'})
    findings: list[ms.Finding] = []
    ms._scan_uc(p, findings)
    assert any(f.uc_id == "UC-1.1.1" for f in findings)


def test_scan_uc_blank_spl_and_cim_spl_emits_no_findings(
    fake_repo: pathlib.Path, make_uc: MakeUC
) -> None:
    """A UC with empty ``spl`` and ``cimSpl`` strings is skipped silently
    (the ``if not blob: continue`` short-circuit).
    """
    p = make_uc("1.1.1", spl="", cim_spl="")
    findings: list[ms.Finding] = []
    ms._scan_uc(p, findings)
    assert findings == []


def test_scan_uc_cim_spl_none_handled_as_empty(fake_repo: pathlib.Path, make_uc: MakeUC) -> None:
    """``cimSpl`` ``None`` is coerced to empty string via ``or ""``."""
    p = make_uc("1.1.1", spl="search foo", cim_spl=None)
    findings: list[ms.Finding] = []
    ms._scan_uc(p, findings)
    assert findings == []


# --------------------------------------------------- _scan_uc sourcetype --


def test_scan_uc_unknown_meraki_sourcetype_flagged_high(
    fake_repo: pathlib.Path, make_uc: MakeUC
) -> None:
    """A UC referencing ``sourcetype=meraki:notreal`` (not in the canonical
    set) emits one ``HIGH/sourcetype`` finding.
    """
    p = make_uc("1.1.1", spl='search index=meraki sourcetype="meraki:notreal"')
    findings: list[ms.Finding] = []
    ms._scan_uc(p, findings)
    relevant = [f for f in findings if f.category == "sourcetype"]
    assert len(relevant) == 1
    assert relevant[0].severity == "HIGH"
    assert "meraki:notreal" in relevant[0].message


def test_scan_uc_canonical_sourcetype_is_silent(fake_repo: pathlib.Path, make_uc: MakeUC) -> None:
    """A canonical sourcetype emits no findings."""
    p = make_uc("1.1.1", spl='search sourcetype="meraki:devices"')
    findings: list[ms.Finding] = []
    ms._scan_uc(p, findings)
    assert findings == []


def test_scan_uc_wildcard_sourcetype_skipped(fake_repo: pathlib.Path, make_uc: MakeUC) -> None:
    """A wildcard sourcetype (``sourcetype=meraki:*``) is skipped via the
    ``if "*" in st: continue`` carve-out.
    """
    p = make_uc("1.1.1", spl='search sourcetype="meraki:*"')
    findings: list[ms.Finding] = []
    ms._scan_uc(p, findings)
    assert findings == []


def test_scan_uc_non_meraki_named_sourcetype_skipped(
    fake_repo: pathlib.Path, make_uc: MakeUC
) -> None:
    """Sourcetypes that don't start with ``meraki:`` and aren't bare
    ``meraki`` / ``cisco:meraki`` are not in scope for this audit.
    """
    p = make_uc("1.1.1", spl='search sourcetype="cisco:wlc"')
    findings: list[ms.Finding] = []
    ms._scan_uc(p, findings)
    assert findings == []


def test_scan_uc_sourcetype_appears_in_cim_spl_also_scanned(
    fake_repo: pathlib.Path, make_uc: MakeUC
) -> None:
    """``cimSpl`` is scanned in addition to ``spl`` (both blobs walked)."""
    p = make_uc(
        "1.1.1",
        spl="",
        cim_spl='search sourcetype="meraki:bogus"',
    )
    findings: list[ms.Finding] = []
    ms._scan_uc(p, findings)
    assert any(f.severity == "HIGH" and "meraki:bogus" in f.message for f in findings)


def test_scan_uc_bare_meraki_sourcetype_is_canonical(
    fake_repo: pathlib.Path, make_uc: MakeUC
) -> None:
    """Bare ``sourcetype=meraki`` (SC4S syslog) is canonical → no finding."""
    p = make_uc("1.1.1", spl="search sourcetype=meraki")
    findings: list[ms.Finding] = []
    ms._scan_uc(p, findings)
    assert findings == []


def test_scan_uc_cisco_meraki_sourcetype_is_canonical(
    fake_repo: pathlib.Path, make_uc: MakeUC
) -> None:
    """``sourcetype=cisco:meraki`` (SC4S Meraki vendor pack) is canonical."""
    p = make_uc("1.1.1", spl='search sourcetype="cisco:meraki"')
    findings: list[ms.Finding] = []
    ms._scan_uc(p, findings)
    assert findings == []


# --------------------------------------- _scan_uc index/sourcetype mismatch --


def test_scan_uc_index_meraki_with_non_meraki_sourcetype_flagged_medium(
    fake_repo: pathlib.Path, make_uc: MakeUC
) -> None:
    """``index=meraki`` paired with a non-Meraki sourcetype within the
    next 200 chars emits one ``MEDIUM/index_sourcetype_mismatch`` finding.
    """
    p = make_uc(
        "1.1.1",
        spl='search index=meraki sourcetype="cisco:wlc:firewall"',
    )
    findings: list[ms.Finding] = []
    ms._scan_uc(p, findings)
    mismatches = [f for f in findings if f.category == "index_sourcetype_mismatch"]
    assert len(mismatches) == 1
    assert mismatches[0].severity == "MEDIUM"
    assert "cisco:wlc:firewall" in mismatches[0].message


def test_scan_uc_index_cisco_meraki_with_non_meraki_sourcetype_flagged(
    fake_repo: pathlib.Path, make_uc: MakeUC
) -> None:
    """The ``index=cisco_meraki`` branch is also flagged when paired with
    a non-Meraki sourcetype.
    """
    p = make_uc(
        "1.1.1",
        spl='search index=cisco_meraki sourcetype="cisco:catalyst"',
    )
    findings: list[ms.Finding] = []
    ms._scan_uc(p, findings)
    assert any(
        f.category == "index_sourcetype_mismatch" and "cisco:catalyst" in f.message
        for f in findings
    )


def test_scan_uc_other_index_does_not_emit_mismatch(
    fake_repo: pathlib.Path, make_uc: MakeUC
) -> None:
    """``index=wireless`` (or any non-Meraki canonical index) does NOT
    surface index-sourcetype-mismatch findings (only `meraki` and
    `cisco_meraki` indexes are scoped).
    """
    p = make_uc(
        "1.1.1",
        spl='search index=wireless sourcetype="cisco:wlc"',
    )
    findings: list[ms.Finding] = []
    ms._scan_uc(p, findings)
    assert not any(f.category == "index_sourcetype_mismatch" for f in findings)


def test_scan_uc_index_meraki_with_no_sourcetype_in_tail_silent(
    fake_repo: pathlib.Path, make_uc: MakeUC
) -> None:
    """If ``index=meraki`` is not followed by a sourcetype within 200
    characters, no mismatch is emitted (the ``if st_m:`` guard).
    """
    p = make_uc("1.1.1", spl="search index=meraki | stats count")
    findings: list[ms.Finding] = []
    ms._scan_uc(p, findings)
    assert not any(f.category == "index_sourcetype_mismatch" for f in findings)


def test_scan_uc_index_meraki_with_meraki_sourcetype_no_mismatch(
    fake_repo: pathlib.Path, make_uc: MakeUC
) -> None:
    """``index=meraki sourcetype=meraki:devices`` is the canonical pair —
    no mismatch.
    """
    p = make_uc(
        "1.1.1",
        spl='search index=meraki sourcetype="meraki:devices"',
    )
    findings: list[ms.Finding] = []
    ms._scan_uc(p, findings)
    assert not any(f.category == "index_sourcetype_mismatch" for f in findings)


def test_scan_uc_index_meraki_with_wildcard_sourcetype_skipped(
    fake_repo: pathlib.Path, make_uc: MakeUC
) -> None:
    """A wildcard sourcetype after ``index=meraki`` is skipped via the
    inner ``if "*" in st: continue``.
    """
    p = make_uc(
        "1.1.1",
        spl='search index=meraki sourcetype="meraki:*"',
    )
    findings: list[ms.Finding] = []
    ms._scan_uc(p, findings)
    assert not any(f.category == "index_sourcetype_mismatch" for f in findings)


# ----------------------------------------- _scan_uc hallucinated_field --


def test_scan_uc_hallucinated_field_in_meraki_spl_flagged(
    fake_repo: pathlib.Path, make_uc: MakeUC
) -> None:
    """A hallucinated field referenced in SPL that includes a Meraki
    sourcetype emits one ``MEDIUM/hallucinated_field`` finding.
    """
    p = make_uc(
        "1.1.1",
        spl='search sourcetype="meraki:devices" | stats count by compliance_status',
    )
    findings: list[ms.Finding] = []
    ms._scan_uc(p, findings)
    hf = [f for f in findings if f.category == "hallucinated_field"]
    assert len(hf) == 1
    assert hf[0].severity == "MEDIUM"
    assert "compliance_status" in hf[0].message


def test_scan_uc_hallucinated_field_without_meraki_sourcetype_silent(
    fake_repo: pathlib.Path, make_uc: MakeUC
) -> None:
    """A hallucinated field referenced outside a Meraki sourcetype is
    silently skipped (the ``if not has_meraki_st: continue`` gate).
    """
    p = make_uc(
        "1.1.1",
        spl="search sourcetype=cisco:wlc | stats count by compliance_status",
    )
    findings: list[ms.Finding] = []
    ms._scan_uc(p, findings)
    assert not any(f.category == "hallucinated_field" for f in findings)


def test_scan_uc_hallucinated_field_via_eval_alias_allowed(
    fake_repo: pathlib.Path, make_uc: MakeUC
) -> None:
    """A hallucinated field is allowed if the SPL itself creates it via
    ``eval``.
    """
    p = make_uc(
        "1.1.1",
        spl=('search sourcetype="meraki:devices" | eval compliance_status=if(...) | stats count'),
    )
    findings: list[ms.Finding] = []
    ms._scan_uc(p, findings)
    assert not any(f.category == "hallucinated_field" for f in findings)


def test_scan_uc_hallucinated_field_via_as_alias_allowed(
    fake_repo: pathlib.Path, make_uc: MakeUC
) -> None:
    """A hallucinated field is allowed if introduced via ``as <field>``."""
    p = make_uc(
        "1.1.1",
        spl=('search sourcetype="meraki:devices" | stats values(x) as compliance_status'),
    )
    findings: list[ms.Finding] = []
    ms._scan_uc(p, findings)
    assert not any(f.category == "hallucinated_field" for f in findings)


def test_scan_uc_hallucinated_field_via_rename_allowed(
    fake_repo: pathlib.Path, make_uc: MakeUC
) -> None:
    """A hallucinated field is allowed if introduced via ``rename ... as``."""
    p = make_uc(
        "1.1.1",
        spl=('search sourcetype="meraki:devices" | rename x as compliance_status | stats count'),
    )
    findings: list[ms.Finding] = []
    ms._scan_uc(p, findings)
    assert not any(f.category == "hallucinated_field" for f in findings)


def test_scan_uc_multiple_hallucinated_fields_each_flagged(
    fake_repo: pathlib.Path, make_uc: MakeUC
) -> None:
    """Multiple hallucinated fields in the same SPL each emit a separate
    finding (one per field).
    """
    p = make_uc(
        "1.1.1",
        spl=(
            'search sourcetype="meraki:devices" '
            "| stats count by compliance_status, people_count, quality_score"
        ),
    )
    findings: list[ms.Finding] = []
    ms._scan_uc(p, findings)
    hf = [f for f in findings if f.category == "hallucinated_field"]
    msgs = {f.message for f in hf}
    assert any("compliance_status" in m for m in msgs)
    assert any("people_count" in m for m in msgs)
    assert any("quality_score" in m for m in msgs)


def test_scan_uc_legitimate_co2_ppm_not_flagged(fake_repo: pathlib.Path, make_uc: MakeUC) -> None:
    """``co2_ppm`` is NOT in the hallucinated-fields set — a Meraki UC
    that references it must NOT be flagged. This is the documented
    BMS / Airthings / Awair / Kaiterra carve-out.
    """
    p = make_uc(
        "1.1.1",
        spl='search sourcetype="meraki:devices" | stats avg(co2_ppm)',
    )
    findings: list[ms.Finding] = []
    ms._scan_uc(p, findings)
    assert findings == []


def test_scan_uc_hallucinated_field_snippet_includes_surrounding_context(
    fake_repo: pathlib.Path, make_uc: MakeUC
) -> None:
    """The snippet on a hallucinated-field finding spans the offending
    field with 40 chars of context on either side.
    """
    p = make_uc(
        "1.1.1",
        spl=('search sourcetype="meraki:devices" | stats count by compliance_status'),
    )
    findings: list[ms.Finding] = []
    ms._scan_uc(p, findings)
    hf = [f for f in findings if f.category == "hallucinated_field"]
    assert len(hf) == 1
    assert "compliance_status" in hf[0].snippet


# ---------------------------------------------------------------- main() --


def test_main_clean_corpus_exit_zero(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A corpus with only canonical UCs exits 0 even with ``--check``."""
    make_uc("1.1.1", spl='search sourcetype="meraki:devices"')
    rc = ms.main(["--check"])
    assert rc == 0


def test_main_check_exits_one_on_finding(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--check`` exits 1 when any finding is emitted."""
    make_uc("1.1.1", spl='search sourcetype="meraki:notreal"')
    rc = ms.main(["--check"])
    assert rc == 1


def test_main_without_check_exits_zero_on_findings(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Without ``--check`` the audit returns 0 even with findings (it's
    informational by default).
    """
    make_uc("1.1.1", spl='search sourcetype="meraki:notreal"')
    rc = ms.main([])
    assert rc == 0


def test_main_human_report_prints_per_category_buckets(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The human report groups findings by category and renders each via
    ``Finding.human()``.
    """
    make_uc("1.1.1", spl='search sourcetype="meraki:notreal"')
    ms.main([])
    out = capsys.readouterr().out
    assert "Scanned 1 UCs" in out
    assert "Findings:" in out
    assert "sourcetype:" in out
    assert "[HIGH]" in out


def test_main_human_report_shows_zero_meraki_count_when_only_non_meraki(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The Meraki-SPL count uses the ``RE_MERAKI_SOURCETYPE`` regex; UCs
    without any Meraki sourcetype reference contribute 0 to that count.
    """
    make_uc("1.1.1", spl='search sourcetype="aws:cloudtrail"')
    ms.main([])
    out = capsys.readouterr().out
    assert "(0 Meraki SPL queries)" in out


def test_main_human_report_counts_meraki_spl_correctly(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The Meraki SPL count reflects UCs whose ``spl`` matches
    ``RE_MERAKI_SOURCETYPE`` — not all UCs.
    """
    make_uc("1.1.1", spl='search sourcetype="meraki:devices"')
    make_uc("1.1.2", spl='search sourcetype="aws:cloudtrail"')
    ms.main([])
    out = capsys.readouterr().out
    assert "Scanned 2 UCs (1 Meraki SPL queries)" in out


def test_main_json_mode_outputs_array_of_findings(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--json`` emits a JSON array of ``asdict(finding)`` records."""
    make_uc("1.1.1", spl='search sourcetype="meraki:notreal"')
    ms.main(["--json"])
    out = capsys.readouterr().out
    findings = json.loads(out)
    assert isinstance(findings, list)
    assert len(findings) == 1
    assert findings[0]["uc_id"] == "1.1.1"
    assert findings[0]["category"] == "sourcetype"
    assert findings[0]["severity"] == "HIGH"


def test_main_json_mode_emits_empty_array_on_clean_corpus(
    fake_repo: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An empty corpus emits ``[]`` in JSON mode."""
    ms.main(["--json"])
    assert json.loads(capsys.readouterr().out) == []


def test_main_truncates_after_25_findings_per_category(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """When a single category exceeds 25 findings, the human report
    shows the first 25 and then ``... +N more``.
    """
    for i in range(30):
        make_uc(f"1.1.{i}", spl=f'search sourcetype="meraki:notreal{i}"')
    ms.main([])
    out = capsys.readouterr().out
    assert "... +5 more" in out


def test_main_argv_none_falls_through_to_sys_argv(
    fake_repo: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``main(None)`` parses ``sys.argv[1:]``."""
    monkeypatch.setattr("sys.argv", ["audit-meraki-spl"])
    rc = ms.main(None)
    assert rc == 0


def test_main_help_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    """``--help`` exits 0 via ``argparse``'s ``SystemExit(0)``."""
    with pytest.raises(SystemExit) as exc_info:
        ms.main(["--help"])
    assert exc_info.value.code == 0


def test_main_human_report_skips_malformed_uc_in_meraki_count(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The human-report Meraki-count pass also tolerates parse errors and
    keeps counting valid UCs (the ``try/except`` around the JSON read).
    """
    make_uc("1.1.1", body="{ not valid json")
    make_uc("1.1.2", spl='search sourcetype="meraki:devices"')
    ms.main([])
    out = capsys.readouterr().out
    assert "(1 Meraki SPL queries)" in out


def test_main_iter_order_is_sorted_glob(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``files`` is iterated via ``sorted(CONTENT.glob(...))`` so the
    findings come out in deterministic order — across multiple cat-dirs.
    """
    make_uc("2.1.1", cat="cat-2-meraki-b", spl='search sourcetype="meraki:notreal-b"')
    make_uc("1.1.1", cat="cat-1-meraki-a", spl='search sourcetype="meraki:notreal-a"')
    ms.main(["--json"])
    out = capsys.readouterr().out
    findings = json.loads(out)
    assert [f["uc_id"] for f in findings] == ["1.1.1", "2.1.1"]


def test_module_has_dunder_main_block() -> None:
    """The ``if __name__ == "__main__":`` guard is present and uses
    ``raise SystemExit(main())`` so ``python -m splunk_uc.audits.meraki_spl``
    works.
    """
    src = pathlib.Path(ms.__file__).read_text(encoding="utf-8")
    assert 'if __name__ == "__main__":' in src
    assert "raise SystemExit(main())" in src


def test_scan_uc_pat_search_second_call_returns_none_defensive_continue(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Defensive ``continue`` at line 260: the first ``pat.search(blob)``
    succeeds, but the second one (re-search to grab ``.start()`` / ``.end()``)
    returns ``None``. This branch is unreachable under normal operation
    because ``blob`` doesn't mutate between the two calls; we cover it
    by monkey-patching ``re.compile`` to inject a stateful pattern whose
    second ``search()`` invocation returns ``None``.
    """
    import re

    real_compile = re.compile

    class _FlipPattern:
        def __init__(self, real_pat: re.Pattern[str], field: str) -> None:
            self._real = real_pat
            self._field = field
            self._calls = 0

        def search(self, blob: str, *args: Any, **kwargs: Any) -> Any:
            self._calls += 1
            if self._calls == 1:
                return self._real.search(blob, *args, **kwargs)
            return None

    def _flip_compile(pattern: str, *args: Any, **kwargs: Any) -> Any:
        real = real_compile(pattern, *args, **kwargs)
        if pattern == r"\bcompliance_status\b":
            return _FlipPattern(real, "compliance_status")
        return real

    monkeypatch.setattr(re, "compile", _flip_compile)
    p = make_uc(
        "1.1.1",
        spl='search sourcetype="meraki:devices" | stats count by compliance_status',
    )
    findings: list[ms.Finding] = []
    ms._scan_uc(p, findings)
    assert not any(
        f.category == "hallucinated_field" and "compliance_status" in f.message for f in findings
    )
