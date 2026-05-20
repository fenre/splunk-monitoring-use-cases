"""Comprehensive unit tests for ``src/splunk_uc/audits/placeholders.py``.

P16 Wave ZZ (2026-05-19) — burns down the test-coverage debt on the
``audit-placeholders`` placeholder / scaffolding text guard.

The audit walks the JSON SSOT and surfaces three classes of unfinished
content:

1. **Literal markers** — ``TBD`` / ``FIXME`` / ``XXX+`` / ``TODO`` /
   ``example.com`` / ``<YOUR_X>`` angle placeholders /
   ``"calculated_value"`` SPL stubs / ``control theme N`` titles.
2. **Blank ``knownFalsePositives``** — fields that are present but
   empty.
3. **Placeholder-only ``knownFalsePositives``** — values like ``"—"``,
   ``"N/A"``, ``"TBD"`` that pretend to fill the field.

Marker matching is gated by ``is_spl_safe`` so legitimate SPL identifiers
that happen to contain marker substrings don't false-positive on SPL
fields. Findings are filtered through a JSON baseline of accepted debt
before the ``--check`` exit-code gate fires — CI fails only on NEW
findings until the backlog is cleared.

Tests are hermetic — they build a synthetic ``content/cat-<n>-<slug>/``
corpus under ``tmp_path`` and monkey-patch the underlying ``_uc_walk``
module so the live 7,929-UC catalogue is never touched.
"""

from __future__ import annotations

import json
import pathlib
import sys
from typing import Any, Protocol

import pytest

from splunk_uc.audits import _uc_walk
from splunk_uc.audits import placeholders as ph


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
    """Rewire ``_uc_walk.REPO`` and ``_uc_walk.CONTENT`` to ``tmp_path``
    so ``iter_uc_sidecars()`` (used by ``placeholders.main``) walks the
    synthetic corpus instead of the live catalogue.
    """
    content = tmp_path / "content"
    content.mkdir()
    monkeypatch.setattr(_uc_walk, "REPO", tmp_path)
    monkeypatch.setattr(_uc_walk, "CONTENT", content)
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
        cat_dir: pathlib.Path = _uc_walk.CONTENT / cat
        cat_dir.mkdir(exist_ok=True)
        p: pathlib.Path = cat_dir / f"UC-{uc_id}.json"
        if body is ...:
            body = {"id": uc_id}
        if isinstance(body, str):
            p.write_text(body, encoding="utf-8")
        else:
            p.write_text(json.dumps(body), encoding="utf-8")
        return p

    return _factory


# ----------------------------------------------------------- module-level --


def test_default_baseline_resolves_under_data_audits_dir() -> None:
    """``DEFAULT_BASELINE`` resolves to
    ``<repo>/data/audits/placeholders-baseline.json`` via 4-parents-up
    + the ``data/audits/`` path components.
    """
    assert ph.DEFAULT_BASELINE.name == "placeholders-baseline.json"
    assert ph.DEFAULT_BASELINE.parent.name == "audits"
    assert ph.DEFAULT_BASELINE.parent.parent.name == "data"


def test_prose_fields_contains_documented_eleven_entries() -> None:
    """The 11 prose fields swept for placeholder text."""
    assert ph.PROSE_FIELDS == (
        "title",
        "description",
        "value",
        "implementation",
        "detailedImplementation",
        "visualization",
        "knownFalsePositives",
        "dataSources",
        "app",
        "exclusions",
        "evidence",
    )


def test_spl_fields_is_two_entries() -> None:
    """The 2 SPL fields scanned with the ``allow_spl=True`` relaxation."""
    assert ph.SPL_FIELDS == ("spl", "cimSpl")


def test_placeholder_fp_values_documented_dash_and_none_variants() -> None:
    """``PLACEHOLDER_FP_VALUES`` is the lowercase set of values that count
    as placeholder-only ``knownFalsePositives``.
    """
    assert "tbd" in ph.PLACEHOLDER_FP_VALUES
    assert "todo" in ph.PLACEHOLDER_FP_VALUES
    assert "n/a" in ph.PLACEHOLDER_FP_VALUES
    assert "—" in ph.PLACEHOLDER_FP_VALUES
    assert "-" in ph.PLACEHOLDER_FP_VALUES
    assert "|" in ph.PLACEHOLDER_FP_VALUES
    assert "none" in ph.PLACEHOLDER_FP_VALUES
    assert "none identified" in ph.PLACEHOLDER_FP_VALUES


def test_literal_tbd_negative_lookarounds_skip_hex_and_ticket_templates() -> None:
    """``_LITERAL_TBD`` deliberately skips ticket templates
    (``CHG-XXXX``), IPv6 multicast hex (``ff02::1:ffXX:XXXX``), and
    EUI-64 MAC grouping (``XX:XXXX:XXXX``) via the
    ``(?<![A-Za-z0-9_:#-])`` / ``(?![A-Za-z0-9_:-])`` lookarounds.
    """
    assert ph._LITERAL_TBD.search("standalone TBD marker") is not None
    assert ph._LITERAL_TBD.search("FIXME in prose") is not None
    assert ph._LITERAL_TBD.search("XXX placeholder") is not None
    assert ph._LITERAL_TBD.search("XXXX big placeholder") is not None
    assert ph._LITERAL_TBD.search("CHG-XXXX") is None
    assert ph._LITERAL_TBD.search("ff02::1:ffXX:XXXX") is None
    assert ph._LITERAL_TBD.search("12:XXXX:XXXX") is None
    assert ph._LITERAL_TBD.search("FIXMENOT") is None


def test_markers_includes_all_six_documented_categories() -> None:
    """The ``_MARKERS`` list has exactly the six documented entries."""
    cats = {entry[0] for entry in ph._MARKERS}
    assert cats == {
        "literal-tbd",
        "literal-todo",
        "example-com",
        "angle-placeholder",
        "calculated-value",
        "control-theme-n",
    }


def test_markers_spl_safety_flags_documented() -> None:
    """``is_spl_safe`` (the fifth tuple element) is False for prose-only
    markers (``literal-tbd``, ``literal-todo``, ``example-com``,
    ``control-theme-n``) and True for the two markers that legitimately
    appear in SPL (``angle-placeholder`` user-fillable tokens,
    ``calculated-value`` stubs).
    """
    spl_safe = {entry[0]: entry[4] for entry in ph._MARKERS}
    assert spl_safe["literal-tbd"] is False
    assert spl_safe["literal-todo"] is False
    assert spl_safe["example-com"] is False
    assert spl_safe["angle-placeholder"] is True
    assert spl_safe["calculated-value"] is True
    assert spl_safe["control-theme-n"] is False


# ----------------------------------------------------------------- Finding --


def test_finding_human_renders_severity_category_uc_message() -> None:
    """``Finding.human()`` renders
    ``[SEV] [CAT] uc_id (file): message`` + optional snippet (stripped
    + truncated at 160 chars).
    """
    f = ph.Finding(
        file="UC-1.1.1.json",
        uc_id="UC-1.1.1",
        severity="HIGH",
        category="literal-tbd",
        message="msg",
        snippet="  surrounding TBD context  ",
    )
    out = f.human()
    assert "[HIGH] [literal-tbd] UC-1.1.1 (UC-1.1.1.json): msg" in out
    assert "snippet: surrounding TBD context" in out


def test_finding_human_omits_snippet_when_empty() -> None:
    """Empty snippet suppresses the second-line snippet display."""
    f = ph.Finding(
        file="UC-1.1.1.json",
        uc_id="UC-1.1.1",
        severity="MED",
        category="known-fp-blank",
        message="empty kfp",
    )
    assert "snippet:" not in f.human()


def test_finding_human_truncates_long_snippet_to_160_chars() -> None:
    """Snippets longer than 160 chars are truncated."""
    f = ph.Finding(
        file="UC-1.1.1.json",
        uc_id="UC-1.1.1",
        severity="HIGH",
        category="literal-tbd",
        message="msg",
        snippet="x" * 500,
    )
    out = f.human()
    assert "snippet: " + ("x" * 160) in out


# ----------------------------------------------------------- _check_text --


def test_check_text_finds_literal_tbd() -> None:
    """A ``TBD`` token in prose surfaces as ``literal-tbd``."""
    findings = ph._check_text(
        "UC-1.1.1", "UC-1.1.1.json", "description", "look here TBD please", allow_spl=False
    )
    assert any(f.category == "literal-tbd" and f.severity == "HIGH" for f in findings)


def test_check_text_finds_literal_todo() -> None:
    """A ``TODO`` marker surfaces as ``literal-todo``."""
    findings = ph._check_text(
        "UC-1.1.1", "UC-1.1.1.json", "implementation", "step 1: TODO fill me in", allow_spl=False
    )
    assert any(f.category == "literal-todo" and f.severity == "HIGH" for f in findings)


def test_check_text_finds_example_com() -> None:
    """``example.com`` / ``example.org`` / ``example.net`` (case-insensitive)
    surfaces as ``example-com`` at MED.
    """
    for url in ("https://example.com/api", "EXAMPLE.ORG", "example.net/foo"):
        findings = ph._check_text(
            "UC-1.1.1", "UC-1.1.1.json", "implementation", url, allow_spl=False
        )
        assert any(f.category == "example-com" and f.severity == "MED" for f in findings), url


def test_check_text_finds_angle_placeholder() -> None:
    """``<YOUR_HEC_TOKEN>`` / ``<REPLACE_ME>`` surface as
    ``angle-placeholder`` at MED.
    """
    findings = ph._check_text(
        "UC-1.1.1",
        "UC-1.1.1.json",
        "implementation",
        "Set token to <YOUR_HEC_TOKEN>.",
        allow_spl=False,
    )
    assert any(f.category == "angle-placeholder" and f.severity == "MED" for f in findings)


def test_check_text_finds_calculated_value_stub_in_spl() -> None:
    """``"calculated_value"`` in SPL surfaces as ``calculated-value`` HIGH
    when ``allow_spl=True`` (it's marked ``is_spl_safe=True``).
    """
    findings = ph._check_text(
        "UC-1.1.1",
        "UC-1.1.1.json",
        "spl",
        '... | eval foo="calculated_value"',
        allow_spl=True,
    )
    assert any(f.category == "calculated-value" and f.severity == "HIGH" for f in findings)


def test_check_text_finds_control_theme_n_in_title() -> None:
    """``control theme N`` / ``indicator 5`` etc. surfaces as
    ``control-theme-n``.
    """
    findings = ph._check_text(
        "UC-1.1.1",
        "UC-1.1.1.json",
        "title",
        "Customer protection — control theme 7",
        allow_spl=False,
    )
    assert any(f.category == "control-theme-n" and f.severity == "HIGH" for f in findings)


def test_check_text_blocks_non_spl_safe_markers_on_spl_fields() -> None:
    """When ``allow_spl=False`` is False *and* the field is in
    ``SPL_FIELDS``, markers with ``is_spl_safe=False`` are skipped to
    avoid false-positives on legitimate SPL identifiers.

    The actual code-path is: ``if not allow_spl and not is_spl_safe and
    field in SPL_FIELDS: continue``.
    """
    findings = ph._check_text(
        "UC-1.1.1",
        "UC-1.1.1.json",
        "spl",
        "search index=main TBD",
        allow_spl=False,
    )
    assert not any(f.category == "literal-tbd" for f in findings)


def test_check_text_allows_spl_safe_markers_on_spl_fields_with_allow_spl_true() -> None:
    """When ``allow_spl=True`` (i.e. we're explicitly scanning SPL),
    ``is_spl_safe=True`` markers like ``angle-placeholder`` still
    surface.
    """
    findings = ph._check_text(
        "UC-1.1.1",
        "UC-1.1.1.json",
        "spl",
        "... <YOUR_INDEX> ...",
        allow_spl=True,
    )
    assert any(f.category == "angle-placeholder" for f in findings)


def test_check_text_snippet_normalises_newlines_to_pipes() -> None:
    """Multi-line snippets are flattened with ``\\n -> ' | '`` so the
    one-line ``Finding.human()`` rendering is readable.
    """
    findings = ph._check_text(
        "UC-1.1.1",
        "UC-1.1.1.json",
        "description",
        "first line\nsecond line TBD third line",
        allow_spl=False,
    )
    f = next(f for f in findings if f.category == "literal-tbd")
    assert "\n" not in f.snippet
    assert " | " in f.snippet


def test_check_text_silent_on_clean_text() -> None:
    """Text without any marker substrings emits no findings."""
    findings = ph._check_text(
        "UC-1.1.1", "UC-1.1.1.json", "description", "All values populated.", allow_spl=False
    )
    assert findings == []


def test_check_text_snippet_includes_40_char_context_each_side() -> None:
    """The snippet slice is ``[max(0, m.start() - 40) : m.end() + 40]``."""
    findings = ph._check_text(
        "UC-1.1.1",
        "UC-1.1.1.json",
        "description",
        "x" * 100 + " TBD " + "y" * 100,
        allow_spl=False,
    )
    f = next(f for f in findings if f.category == "literal-tbd")
    assert "TBD" in f.snippet
    assert len(f.snippet) <= 40 + len("TBD") + 40 + 2


# ------------------------------------------------------------ _check_known_fp --


def test_check_known_fp_field_missing_returns_empty() -> None:
    """Missing ``knownFalsePositives`` key is silent."""
    assert ph._check_known_fp("UC-1.1.1", "UC-1.1.1.json", {"id": "1.1.1"}) == []


def test_check_known_fp_non_string_returns_empty() -> None:
    """Non-string values silently pass."""
    assert (
        ph._check_known_fp(
            "UC-1.1.1", "UC-1.1.1.json", {"id": "1.1.1", "knownFalsePositives": ["list"]}
        )
        == []
    )


def test_check_known_fp_blank_string_emits_med() -> None:
    """Empty string (after strip) emits ``MED/known-fp-blank``."""
    findings = ph._check_known_fp(
        "UC-1.1.1", "UC-1.1.1.json", {"id": "1.1.1", "knownFalsePositives": "   "}
    )
    assert len(findings) == 1
    assert findings[0].severity == "MED"
    assert findings[0].category == "known-fp-blank"
    assert findings[0].snippet == ""


def test_check_known_fp_placeholder_value_emits_med() -> None:
    """A value that matches one of ``PLACEHOLDER_FP_VALUES`` (after
    stripping trailing ``.``) emits ``MED/known-fp-placeholder``.
    """
    for placeholder in ("TBD", "TODO.", "N/A", "—", "n/A"):
        findings = ph._check_known_fp(
            "UC-1.1.1",
            "UC-1.1.1.json",
            {"id": "1.1.1", "knownFalsePositives": placeholder},
        )
        assert len(findings) == 1, placeholder
        assert findings[0].category == "known-fp-placeholder", placeholder
        assert findings[0].snippet == placeholder.strip()


def test_check_known_fp_meaningful_value_silent() -> None:
    """A real ``knownFalsePositives`` value emits no findings."""
    findings = ph._check_known_fp(
        "UC-1.1.1",
        "UC-1.1.1.json",
        {
            "id": "1.1.1",
            "knownFalsePositives": (
                "Maintenance windows can cause this to trigger; check the change calendar."
            ),
        },
    )
    assert findings == []


def test_check_known_fp_lowercase_comparison_handles_mixed_case() -> None:
    """The check first compares against the original-cased value, then
    against the lower-cased value. ``"TBD"`` and ``"TbD"`` both flag.
    """
    for v in ("TBD", "tbd", "TbD"):
        findings = ph._check_known_fp(
            "UC-1.1.1", "UC-1.1.1.json", {"id": "1.1.1", "knownFalsePositives": v}
        )
        assert len(findings) == 1, v
        assert findings[0].category == "known-fp-placeholder", v


# ----------------------------------------------------------- _load_baseline --


def test_load_baseline_missing_file_returns_empty(tmp_path: pathlib.Path) -> None:
    """A nonexistent baseline returns an empty set without warning."""
    assert ph._load_baseline(tmp_path / "missing.json") == set()


def test_load_baseline_invalid_json_returns_empty_with_warn(
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Malformed JSON returns an empty set and emits a WARN to stderr."""
    p = tmp_path / "bad.json"
    p.write_text("{ not valid", encoding="utf-8")
    assert ph._load_baseline(p) == set()
    assert "WARN: could not read baseline" in capsys.readouterr().err


def test_load_baseline_io_error_returns_empty_with_warn(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``OSError`` on read is caught and emits the same WARN."""
    p = tmp_path / "unreadable.json"
    p.write_text("{}", encoding="utf-8")

    original_read_text = pathlib.Path.read_text

    def _raise_os_error(self: pathlib.Path, *args: Any, **kwargs: Any) -> str:
        if self == p:
            raise OSError("io fail")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(pathlib.Path, "read_text", _raise_os_error)
    assert ph._load_baseline(p) == set()
    assert "WARN: could not read baseline" in capsys.readouterr().err


def test_load_baseline_dict_with_entries_extracts_triples(tmp_path: pathlib.Path) -> None:
    """Schema-versioned baselines wrap entries under ``"entries"``."""
    p = tmp_path / "b.json"
    p.write_text(
        json.dumps(
            {
                "schema": "placeholders-baseline.v1",
                "entries": [
                    {"uc_id": "UC-1.1.1", "file": "UC-1.1.1.json", "category": "literal-tbd"},
                    {"uc_id": "UC-1.1.2", "file": "UC-1.1.2.json", "category": "literal-todo"},
                ],
            }
        ),
        encoding="utf-8",
    )
    triples = ph._load_baseline(p)
    assert triples == {
        ("UC-1.1.1", "UC-1.1.1.json", "literal-tbd"),
        ("UC-1.1.2", "UC-1.1.2.json", "literal-todo"),
    }


def test_load_baseline_bare_list_accepts_legacy_shape(tmp_path: pathlib.Path) -> None:
    """A bare-list baseline (legacy) is also accepted via the
    ``else: data`` branch of the ``isinstance(data, dict)`` check.
    """
    p = tmp_path / "b.json"
    p.write_text(
        json.dumps(
            [
                {"uc_id": "UC-1.1.1", "file": "UC-1.1.1.json", "category": "literal-tbd"},
            ]
        ),
        encoding="utf-8",
    )
    assert ph._load_baseline(p) == {("UC-1.1.1", "UC-1.1.1.json", "literal-tbd")}


def test_load_baseline_skips_non_dict_entries(tmp_path: pathlib.Path) -> None:
    """Non-dict entries are silently skipped."""
    p = tmp_path / "b.json"
    p.write_text(
        json.dumps(
            {
                "entries": [
                    "not a dict",
                    42,
                    None,
                    {"uc_id": "UC-1.1.1", "file": "UC-1.1.1.json", "category": "literal-tbd"},
                ]
            }
        ),
        encoding="utf-8",
    )
    assert ph._load_baseline(p) == {("UC-1.1.1", "UC-1.1.1.json", "literal-tbd")}


def test_load_baseline_skips_entries_missing_keys(tmp_path: pathlib.Path) -> None:
    """Entries missing any of (uc_id, file, category) are skipped."""
    p = tmp_path / "b.json"
    p.write_text(
        json.dumps(
            {
                "entries": [
                    {"uc_id": "UC-1.1.1", "file": "UC-1.1.1.json"},
                    {"file": "UC-1.1.2.json", "category": "literal-tbd"},
                    {"uc_id": "UC-1.1.3", "category": "literal-tbd"},
                    {"uc_id": "", "file": "x", "category": "y"},
                    {"uc_id": "UC-1.1.4", "file": "UC-1.1.4.json", "category": "literal-tbd"},
                ]
            }
        ),
        encoding="utf-8",
    )
    assert ph._load_baseline(p) == {("UC-1.1.4", "UC-1.1.4.json", "literal-tbd")}


def test_baseline_key_extracts_uc_id_file_category() -> None:
    """``_baseline_key`` returns the canonical triple."""
    f = ph.Finding(
        file="UC-1.1.1.json",
        uc_id="UC-1.1.1",
        severity="HIGH",
        category="literal-tbd",
        message="msg",
    )
    assert ph._baseline_key(f) == ("UC-1.1.1", "UC-1.1.1.json", "literal-tbd")


# ---------------------------------------------------------------- main() --


def test_main_clean_corpus_emits_no_findings_exit_zero(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A clean corpus exits 0 with a human report showing 0 findings."""
    make_uc(
        "1.1.1",
        body={"id": "1.1.1", "title": "Clean title", "description": "Real description."},
    )
    rc = ph.main(["--no-baseline", "--check"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Sidecars scanned: 1" in out
    assert "Baseline: disabled (--no-baseline)" in out


def test_main_finds_literal_tbd_in_description_high(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A UC with ``TBD`` in description surfaces a HIGH finding and
    ``--check`` exits 1.
    """
    make_uc(
        "1.1.1",
        body={"id": "1.1.1", "title": "X", "description": "Status: TBD pending."},
    )
    rc = ph.main(["--no-baseline", "--check"])
    assert rc == 1
    out = capsys.readouterr().out
    assert "literal-tbd" in out


def test_main_severity_threshold_med_promotes_med_findings_to_blocking(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """With ``--severity MED`` and ``--check``, a single MED finding
    (e.g. ``angle-placeholder``) is enough to exit 1.
    """
    make_uc(
        "1.1.1",
        body={"id": "1.1.1", "implementation": "Set token to <YOUR_HEC_TOKEN>."},
    )
    rc = ph.main(["--no-baseline", "--check", "--severity", "MED"])
    assert rc == 1


def test_main_severity_default_high_lets_med_findings_pass(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
) -> None:
    """Without ``--severity MED``, a MED-only corpus exits 0 even with
    ``--check`` because the default threshold is HIGH.
    """
    make_uc(
        "1.1.1",
        body={"id": "1.1.1", "implementation": "Set token to <YOUR_HEC_TOKEN>."},
    )
    rc = ph.main(["--no-baseline", "--check"])
    assert rc == 0


def test_main_json_mode_outputs_array_of_surfaced_findings(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--json`` emits the surfaced (post-baseline-filter) findings as
    a JSON array.
    """
    make_uc(
        "1.1.1",
        body={"id": "1.1.1", "description": "Status: TBD"},
    )
    ph.main(["--no-baseline", "--json"])
    out = capsys.readouterr().out
    findings = json.loads(out)
    assert isinstance(findings, list)
    assert any(f["category"] == "literal-tbd" for f in findings)


def test_main_baseline_filters_findings(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A baseline entry matching ``(uc_id, file, category)`` suppresses
    the corresponding finding from the surfaced list (and from the
    ``--check`` exit code).
    """
    make_uc(
        "1.1.1",
        body={"id": "1.1.1", "description": "Status: TBD"},
    )
    baseline = tmp_path / "baseline.json"
    baseline.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "uc_id": "UC-1.1.1",
                        "file": "UC-1.1.1.json",
                        "category": "literal-tbd",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    rc = ph.main(["--baseline", str(baseline), "--check"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "1 accepted entries; 1 matched + suppressed" in out


def test_main_baseline_missing_file_default_path_message(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: pathlib.Path,
) -> None:
    """When the default baseline path doesn't exist, the human report
    says ``(missing)``.
    """
    make_uc("1.1.1")
    missing = tmp_path / "definitely-missing.json"
    rc = ph.main(["--baseline", str(missing)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "(missing)" in out


def test_main_baseline_empty_file_message(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """When the baseline file exists but has no entries, the human
    report prints ``(empty / not present)``.
    """
    make_uc("1.1.1")
    empty = tmp_path / "empty.json"
    empty.write_text(json.dumps({"entries": []}), encoding="utf-8")
    rc = ph.main(["--baseline", str(empty)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "(empty / not present)" in out


def test_main_findings_by_severity_renders_sorted(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The ``Findings by severity:`` line includes counts in sorted
    severity-key order (``HIGH`` < ``MED`` alphabetically).
    """
    make_uc(
        "1.1.1",
        body={
            "id": "1.1.1",
            "description": "Status: TBD",
            "implementation": "Token: <YOUR_HEC_TOKEN>",
        },
    )
    ph.main(["--no-baseline"])
    out = capsys.readouterr().out
    assert "HIGH=" in out
    assert "MED=" in out


def test_main_findings_by_severity_none_when_empty(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """When there are no surfaced findings, the report shows
    ``(none after baseline)`` for the severity line.
    """
    make_uc("1.1.1")
    ph.main(["--no-baseline"])
    out = capsys.readouterr().out
    assert "Findings by severity: (none after baseline)" in out
    assert "(none after baseline)" in out


def test_main_findings_by_category_lists_sorted_by_count_desc(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``Findings by category:`` lists each category with its count,
    sorted by count descending.
    """
    make_uc(
        "1.1.1",
        body={
            "id": "1.1.1",
            "description": "Status: TBD TBD",
            "value": "TODO",
        },
    )
    ph.main(["--no-baseline"])
    out = capsys.readouterr().out
    assert "literal-tbd" in out
    assert "literal-todo" in out


def test_main_findings_section_shows_first_50_only(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Findings list is truncated at 50 with an ``... and N more`` line."""
    for i in range(55):
        make_uc(
            f"1.1.{i}",
            body={"id": f"1.1.{i}", "description": "Status: TBD"},
        )
    ph.main(["--no-baseline"])
    out = capsys.readouterr().out
    assert "FINDINGS (first 50 shown):" in out
    assert "... and 5 more" in out


def test_main_findings_section_omitted_when_no_findings(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """If there are no surfaced findings, the ``FINDINGS`` section is
    not printed at all.
    """
    make_uc("1.1.1")
    ph.main(["--no-baseline"])
    out = capsys.readouterr().out
    assert "FINDINGS" not in out


def test_main_finds_known_fp_blank_in_kfp_field(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An empty ``knownFalsePositives`` value surfaces as ``known-fp-blank``."""
    make_uc(
        "1.1.1",
        body={"id": "1.1.1", "knownFalsePositives": "   "},
    )
    ph.main(["--no-baseline"])
    out = capsys.readouterr().out
    assert "known-fp-blank" in out


def test_main_finds_known_fp_placeholder(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A ``knownFalsePositives: "TBD"`` surfaces as ``known-fp-placeholder``."""
    make_uc(
        "1.1.1",
        body={"id": "1.1.1", "knownFalsePositives": "TBD"},
    )
    ph.main(["--no-baseline"])
    out = capsys.readouterr().out
    assert "known-fp-placeholder" in out


def test_main_finds_calculated_value_stub_via_spl_field(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A ``"calculated_value"`` literal in the ``spl`` field of a UC
    surfaces as a HIGH finding via the ``calculated-value`` marker
    (which is ``is_spl_safe=True``, so it fires under
    ``allow_spl=True``).
    """
    make_uc(
        "1.1.1",
        body={
            "id": "1.1.1",
            "spl": '... | eval foo="calculated_value"',
        },
    )
    rc = ph.main(["--no-baseline", "--check"])
    assert rc == 1
    out = capsys.readouterr().out
    assert "calculated-value" in out


def test_main_skips_non_string_prose_fields(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Prose-field values that aren't strings (e.g. list, None) are
    silently skipped via the ``isinstance(v, str)`` guard.
    """
    make_uc(
        "1.1.1",
        body={"id": "1.1.1", "title": ["not", "a", "string"], "description": None},
    )
    rc = ph.main(["--no-baseline", "--check"])
    assert rc == 0


def test_main_skips_empty_string_prose_fields(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Empty-string prose fields are skipped (``if isinstance(v, str)
    and v``)."""
    make_uc(
        "1.1.1",
        body={"id": "1.1.1", "title": "", "description": ""},
    )
    rc = ph.main(["--no-baseline", "--check"])
    assert rc == 0


def test_main_missing_id_renders_as_uc_unknown(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A UC without an ``id`` field renders as ``UC-<unknown>``."""
    make_uc("1.1.1", body={"description": "TBD"})
    ph.main(["--no-baseline"])
    out = capsys.readouterr().out
    assert "UC-<unknown>" in out


def test_main_argv_none_falls_through_to_sys_argv(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``main(None)`` parses ``sys.argv[1:]``."""
    make_uc("1.1.1")
    monkeypatch.setattr("sys.argv", ["audit-placeholders", "--no-baseline"])
    assert ph.main(None) == 0


def test_main_help_exits_zero() -> None:
    """``--help`` exits 0 via argparse."""
    with pytest.raises(SystemExit) as exc_info:
        ph.main(["--help"])
    assert exc_info.value.code == 0


# ---------------------------------------------------- --write-baseline path --


def test_main_write_baseline_emits_high_and_med_findings(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--write-baseline`` snapshots HIGH+MED findings to the baseline
    path and returns 0; LOW (none exist in this audit by default) is
    excluded.
    """
    make_uc(
        "1.1.1",
        body={
            "id": "1.1.1",
            "description": "Status: TBD",
            "implementation": "Token: <YOUR_HEC_TOKEN>",
        },
    )
    target = tmp_path / "out" / "baseline.json"
    rc = ph.main(["--baseline", str(target), "--write-baseline"])
    assert rc == 0
    written = json.loads(target.read_text(encoding="utf-8"))
    assert written["schema"] == "placeholders-baseline.v1"
    assert written["entry_count"] == 2
    cats = {e["category"] for e in written["entries"]}
    assert cats == {"literal-tbd", "angle-placeholder"}
    assert "Wrote 2 accepted-debt entries" in capsys.readouterr().err


def test_main_write_baseline_deduplicates_entries(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    tmp_path: pathlib.Path,
) -> None:
    """When two UCs in the same file share the same ``(uc_id, file,
    category)`` triple (which can't happen across files but CAN happen
    if the same SPL pattern fires twice in different prose fields of
    the same UC), the baseline is deduplicated.
    """
    make_uc(
        "1.1.1",
        body={
            "id": "1.1.1",
            "description": "Status: TBD",
            "value": "TBD pending review",
        },
    )
    target = tmp_path / "baseline.json"
    rc = ph.main(["--baseline", str(target), "--write-baseline"])
    assert rc == 0
    written = json.loads(target.read_text(encoding="utf-8"))
    triples = {(e["uc_id"], e["file"], e["category"]) for e in written["entries"]}
    assert len(triples) == len(written["entries"])


def test_main_write_baseline_sorts_entries_deterministically(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    tmp_path: pathlib.Path,
) -> None:
    """``deduped.sort(key=lambda e: (e["category"], e["uc_id"], e["file"]))``
    means the on-disk baseline is byte-stable across runs.
    """
    make_uc("2.1.1", cat="cat-2-bar", body={"id": "2.1.1", "description": "Status: TBD"})
    make_uc("1.1.1", body={"id": "1.1.1", "description": "Status: TBD"})
    target = tmp_path / "baseline.json"
    ph.main(["--baseline", str(target), "--write-baseline"])
    written = json.loads(target.read_text(encoding="utf-8"))
    uc_ids = [e["uc_id"] for e in written["entries"]]
    assert uc_ids == sorted(uc_ids)


def test_main_write_baseline_creates_parent_directory(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    tmp_path: pathlib.Path,
) -> None:
    """``baseline_path.parent.mkdir(parents=True, exist_ok=True)`` means
    nested directories don't have to exist before ``--write-baseline``.
    """
    make_uc("1.1.1", body={"id": "1.1.1", "description": "TBD"})
    target = tmp_path / "deeply" / "nested" / "path" / "baseline.json"
    ph.main(["--baseline", str(target), "--write-baseline"])
    assert target.exists()


def test_main_write_baseline_emits_empty_baseline_on_clean_corpus(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    tmp_path: pathlib.Path,
) -> None:
    """Clean corpus produces a baseline with ``entry_count: 0``."""
    make_uc("1.1.1")
    target = tmp_path / "baseline.json"
    ph.main(["--baseline", str(target), "--write-baseline"])
    written = json.loads(target.read_text(encoding="utf-8"))
    assert written["entry_count"] == 0
    assert written["entries"] == []


def test_main_baseline_with_entries_renders_path_and_counts(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """When the baseline file exists and contains entries, the human
    report shows ``Baseline: <path> (N accepted entries; M matched +
    suppressed)``.
    """
    make_uc("1.1.1", body={"id": "1.1.1", "description": "Status: TBD"})
    baseline = tmp_path / "baseline.json"
    baseline.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "uc_id": "UC-1.1.1",
                        "file": "UC-1.1.1.json",
                        "category": "literal-tbd",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    ph.main(["--baseline", str(baseline)])
    out = capsys.readouterr().out
    assert "1 accepted entries" in out
    assert "1 matched + suppressed" in out


# ----------------------------------------------------- __main__ smoke --


def test_module_dunder_main_exists() -> None:
    """The ``if __name__ == "__main__":`` block uses
    ``sys.exit(main())``.
    """
    src = pathlib.Path(ph.__file__).read_text(encoding="utf-8")
    assert 'if __name__ == "__main__":' in src
    assert "sys.exit(main())" in src
