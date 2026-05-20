"""Comprehensive unit tests for ``src/splunk_uc/audits/known_fp.py``.

Pins every documented contract of the ``knownFalsePositives`` audit:

- module-level constants (``PLACEHOLDER_VALUES`` exactly the documented set
  to defend against silent drift);
- the ``Finding`` ``NamedTuple`` shape (six fields with the ``snippet=""``
  default);
- the ``_classify`` decision tree across HIGH (literal ``|``), MED (empty
  or whitespace-only), LOW (placeholder values, case-insensitive), and the
  empty-tuple acceptance path;
- the ``main()`` CLI matrix — sidecars without the field are skipped,
  non-string values are coerced to empty via ``get_text_field`` and surface
  as MED, output formatting (header, severity tally, kind tally,
  per-finding lines, snippet truncation at 120 chars, list truncation at
  30 with the ``... and N more`` footer), the sort order (severity, file,
  uc_id), and the ``--check`` exit-code matrix (HIGH → 1, MED-only → 0).
"""

from __future__ import annotations

import json
import pathlib
from typing import Any, Protocol

import pytest

from splunk_uc.audits import _uc_walk, known_fp


class MakeUC(Protocol):
    def __call__(
        self,
        uc_id: str,
        known_fp_value: Any = ...,
        category: int = 1,
    ) -> pathlib.Path: ...


@pytest.fixture
def fake_repo(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """Build a hermetic content/ tree and patch upstream ``_uc_walk.CONTENT``.

    ``known_fp.py`` delegates to ``iter_uc_sidecars()`` which closes over
    ``_uc_walk.CONTENT`` — the patch has to be on the upstream module.
    """
    content = tmp_path / "content"
    content.mkdir()
    monkeypatch.setattr(_uc_walk, "REPO", tmp_path)
    monkeypatch.setattr(_uc_walk, "CONTENT", content)
    return tmp_path


@pytest.fixture
def make_uc(fake_repo: pathlib.Path) -> MakeUC:
    """Factory that materialises a UC sidecar under ``content/cat-NN-foo/``."""

    def _make(
        uc_id: str,
        known_fp_value: Any = ...,
        category: int = 1,
    ) -> pathlib.Path:
        cat_dir = fake_repo / "content" / f"cat-{category:02d}-foo"
        cat_dir.mkdir(exist_ok=True)
        sidecar = cat_dir / f"UC-{uc_id}.json"
        payload: dict[str, Any] = {"id": uc_id, "title": f"UC {uc_id}"}
        if known_fp_value is not ...:
            payload["knownFalsePositives"] = known_fp_value
        sidecar.write_text(json.dumps(payload), encoding="utf-8")
        return sidecar

    return _make


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------


def test_placeholder_values_exact_contents() -> None:
    """Pin the placeholder vocabulary against silent drift."""
    assert known_fp.PLACEHOLDER_VALUES == {
        "-",
        ".",
        "...",
        "tbd",
        "todo",
        "fixme",
        "xxx",
        "none",
    }


def test_placeholder_values_are_lowercase() -> None:
    """All entries are lowercase — comparison uses ``.lower()`` on input."""
    for v in known_fp.PLACEHOLDER_VALUES:
        assert v == v.lower()


# ---------------------------------------------------------------------------
# Finding NamedTuple
# ---------------------------------------------------------------------------


def test_finding_has_six_fields_with_snippet_default() -> None:
    """The ``Finding`` namedtuple has six fields, snippet defaults to ''."""
    finding = known_fp.Finding(
        severity="HIGH",
        kind="known-fp-pipe-stub",
        uc_id="UC-1.1.1",
        file="UC-1.1.1.json",
        message="msg",
    )
    assert finding.severity == "HIGH"
    assert finding.kind == "known-fp-pipe-stub"
    assert finding.uc_id == "UC-1.1.1"
    assert finding.file == "UC-1.1.1.json"
    assert finding.message == "msg"
    assert finding.snippet == ""


def test_finding_accepts_explicit_snippet() -> None:
    """Snippet can be set explicitly."""
    f = known_fp.Finding("HIGH", "k", "u", "f", "m", snippet="snippet text")
    assert f.snippet == "snippet text"


# ---------------------------------------------------------------------------
# _classify
# ---------------------------------------------------------------------------


def test_classify_literal_pipe_is_high() -> None:
    """A literal `|` value is the HIGH pipe-stub finding."""
    sev, kind, msg = known_fp._classify("|")
    assert sev == "HIGH"
    assert kind == "known-fp-pipe-stub"
    assert "literal `|`" in msg
    assert "YAML-import" in msg


def test_classify_pipe_with_surrounding_whitespace_is_high() -> None:
    """`  |  ` strips to `|` and is still HIGH."""
    sev, kind, _ = known_fp._classify("  |  ")
    assert sev == "HIGH"
    assert kind == "known-fp-pipe-stub"


def test_classify_empty_string_is_med() -> None:
    """Empty string is the MED empty finding."""
    sev, kind, msg = known_fp._classify("")
    assert sev == "MED"
    assert kind == "known-fp-empty"
    assert "blank" in msg


def test_classify_whitespace_only_is_med() -> None:
    """Whitespace-only string strips to empty → MED."""
    sev, kind, _ = known_fp._classify("   \n\t  ")
    assert sev == "MED"
    assert kind == "known-fp-empty"


@pytest.mark.parametrize(
    "value",
    [
        "-",
        ".",
        "...",
        "tbd",
        "todo",
        "fixme",
        "xxx",
        "none",
    ],
)
def test_classify_placeholder_values_are_low(value: str) -> None:
    """Each documented placeholder triggers the LOW finding."""
    sev, kind, msg = known_fp._classify(value)
    assert sev == "LOW"
    assert kind == "known-fp-placeholder"
    assert "placeholder" in msg
    assert repr(value) in msg


@pytest.mark.parametrize(
    "value",
    ["TBD", "TODO", "Fixme", "XXX", "None", "NONE", "ToDo"],
)
def test_classify_placeholder_case_insensitive(value: str) -> None:
    """Placeholder check uses ``.lower()`` so mixed-case still triggers LOW."""
    sev, kind, _ = known_fp._classify(value)
    assert sev == "LOW"
    assert kind == "known-fp-placeholder"


def test_classify_placeholder_with_surrounding_whitespace_is_low() -> None:
    """`  TBD  ` strips to `TBD` then `.lower()` to `tbd` → LOW."""
    sev, kind, _ = known_fp._classify("  TBD  ")
    assert sev == "LOW"
    assert kind == "known-fp-placeholder"


def test_classify_normal_text_returns_empty_tuple() -> None:
    """A real description passes — empty tuple acceptance path."""
    sev, kind, msg = known_fp._classify("Users running maintenance scripts may trigger this alert.")
    assert sev == ""
    assert kind == ""
    assert msg == ""


def test_classify_n_a_passes() -> None:
    """The canonical 'N/A (no documented false positives)' string passes."""
    sev, kind, msg = known_fp._classify("N/A (no documented false positives)")
    assert (sev, kind, msg) == ("", "", "")


def test_classify_double_pipe_passes() -> None:
    """`||` is not a literal single-pipe — passes (real content)."""
    sev, _, _ = known_fp._classify("||")
    assert sev == ""


def test_classify_text_starting_with_pipe_passes() -> None:
    """`| Users running ...` strips to `| Users running ...` ≠ `|` → passes."""
    sev, _, _ = known_fp._classify("| Users running maintenance scripts")
    assert sev == ""


def test_classify_placeholder_inside_sentence_passes() -> None:
    """`This is a TBD example.` is not just `tbd` → passes."""
    sev, _, _ = known_fp._classify("This is a TBD example.")
    assert sev == ""


def test_classify_question_mark_passes() -> None:
    """`?` is not in PLACEHOLDER_VALUES → passes (probably real, if odd)."""
    sev, _, _ = known_fp._classify("?")
    assert sev == ""


# ---------------------------------------------------------------------------
# main() CLI — happy / empty / scaffolding
# ---------------------------------------------------------------------------


def test_main_empty_content_returns_zero(
    fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Empty content tree → exit 0 + zero counters."""
    assert known_fp.main([]) == 0
    captured = capsys.readouterr()
    assert "Sidecars scanned: 0" in captured.out
    assert "FINDINGS:" not in captured.out


def test_main_missing_field_skipped(make_uc: MakeUC, capsys: pytest.CaptureFixture[str]) -> None:
    """UCs without ``knownFalsePositives`` are not raised against MED."""
    make_uc("1.1.1")
    assert known_fp.main([]) == 0
    captured = capsys.readouterr()
    assert "Sidecars scanned: 1" in captured.out
    assert "MED" not in captured.out.split("Findings by severity:", 1)[1].splitlines()[0]


def test_main_clean_value_passes(make_uc: MakeUC, capsys: pytest.CaptureFixture[str]) -> None:
    """A real description → exit 0 with no findings printed."""
    make_uc("1.1.1", known_fp_value="Real false-positive description here.")
    assert known_fp.main([]) == 0
    captured = capsys.readouterr()
    assert "FINDINGS:" not in captured.out
    assert "Sidecars scanned: 1" in captured.out


def test_main_argv_none_passes_through(
    fake_repo: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``argv=None`` falls through to argparse's ``sys.argv`` default."""
    monkeypatch.setattr("sys.argv", ["audit-known-fp"])
    assert known_fp.main(None) == 0


def test_main_help_exits_cleanly(
    fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """``--help`` exits with code 0 (argparse default)."""
    with pytest.raises(SystemExit) as excinfo:
        known_fp.main(["--help"])
    assert excinfo.value.code == 0
    captured = capsys.readouterr()
    assert "knownFalsePositives" in captured.out
    assert "--check" in captured.out


# ---------------------------------------------------------------------------
# main() — non-string field values via get_text_field
# ---------------------------------------------------------------------------


def test_main_none_value_surfaces_as_med(
    make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
) -> None:
    """A literal JSON ``null`` is still "present" — get_text_field returns ''."""
    make_uc("1.1.1", known_fp_value=None)
    assert known_fp.main([]) == 0
    captured = capsys.readouterr()
    assert "MED=1" in captured.out
    assert "known-fp-empty" in captured.out


def test_main_integer_value_surfaces_as_med(
    make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
) -> None:
    """A non-string value coerces to '' via get_text_field → MED."""
    make_uc("1.1.1", known_fp_value=42)
    assert known_fp.main([]) == 0
    captured = capsys.readouterr()
    assert "MED=1" in captured.out
    assert "known-fp-empty" in captured.out


def test_main_list_value_surfaces_as_med(
    make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
) -> None:
    """A list value coerces to '' via get_text_field → MED."""
    make_uc("1.1.1", known_fp_value=["a", "b"])
    assert known_fp.main([]) == 0
    captured = capsys.readouterr()
    assert "MED=1" in captured.out


# ---------------------------------------------------------------------------
# main() — finding kinds and severity tally
# ---------------------------------------------------------------------------


def test_main_pipe_stub_is_high(make_uc: MakeUC, capsys: pytest.CaptureFixture[str]) -> None:
    """A literal `|` value produces a HIGH known-fp-pipe-stub finding."""
    make_uc("1.1.1", known_fp_value="|")
    assert known_fp.main([]) == 0
    captured = capsys.readouterr()
    assert "HIGH=1" in captured.out
    assert "known-fp-pipe-stub" in captured.out
    assert "UC-1.1.1" in captured.out


def test_main_empty_string_is_med(make_uc: MakeUC, capsys: pytest.CaptureFixture[str]) -> None:
    """Empty string surfaces as MED known-fp-empty."""
    make_uc("1.1.1", known_fp_value="")
    assert known_fp.main([]) == 0
    captured = capsys.readouterr()
    assert "MED=1" in captured.out
    assert "known-fp-empty" in captured.out


def test_main_placeholder_value_is_low(make_uc: MakeUC, capsys: pytest.CaptureFixture[str]) -> None:
    """`TBD` value is LOW known-fp-placeholder."""
    make_uc("1.1.1", known_fp_value="TBD")
    assert known_fp.main([]) == 0
    captured = capsys.readouterr()
    assert "LOW=1" in captured.out
    assert "known-fp-placeholder" in captured.out


def test_main_severity_tally_sorted_alphabetically(
    make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
) -> None:
    """Severity tally is alphabetically sorted (HIGH, LOW, MED)."""
    make_uc("1.1.1", known_fp_value="|")
    make_uc("1.1.2", known_fp_value="")
    make_uc("1.1.3", known_fp_value="TBD")
    assert known_fp.main([]) == 0
    captured = capsys.readouterr()
    line = next(
        line for line in captured.out.splitlines() if line.startswith("Findings by severity")
    )
    assert "HIGH=1" in line
    assert "LOW=1" in line
    assert "MED=1" in line
    high_pos = line.index("HIGH=1")
    low_pos = line.index("LOW=1")
    med_pos = line.index("MED=1")
    assert high_pos < low_pos < med_pos


def test_main_kind_tally_sorted_by_count_desc_then_name(
    make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
) -> None:
    """Kind tally is sorted by count descending, ties broken alphabetically."""
    for i in range(1, 4):
        make_uc(f"1.1.{i}", known_fp_value="|")
    for i in range(4, 7):
        make_uc(f"1.1.{i}", known_fp_value="")
    make_uc("1.1.7", known_fp_value="TBD")
    assert known_fp.main([]) == 0
    captured = capsys.readouterr()
    by_kind_block = captured.out.split("Findings by category:", 1)[1]
    lines = [line for line in by_kind_block.splitlines() if line.strip()]
    assert "known-fp-empty" in lines[0]
    assert "known-fp-pipe-stub" in lines[1]
    assert "known-fp-placeholder" in lines[2]


# ---------------------------------------------------------------------------
# main() — finding sort order
# ---------------------------------------------------------------------------


def test_main_findings_sorted_by_severity_first(
    make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
) -> None:
    """HIGH findings printed before LOW which is before MED, despite UC order."""
    make_uc("1.1.1", known_fp_value="TBD")  # LOW
    make_uc("1.1.2", known_fp_value="")  # MED
    make_uc("1.1.3", known_fp_value="|")  # HIGH
    assert known_fp.main([]) == 0
    captured = capsys.readouterr()
    findings_block = captured.out.split("FINDINGS:", 1)[1]
    high_pos = findings_block.index("[HIGH]")
    med_pos = findings_block.index("[MED]")
    low_pos = findings_block.index("[LOW]")
    assert high_pos < med_pos < low_pos


def test_main_findings_within_severity_sorted_by_file_then_uc(
    make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
) -> None:
    """Within a severity, sort by file name then uc_id."""
    make_uc("1.1.3", known_fp_value="|")
    make_uc("1.1.1", known_fp_value="|")
    make_uc("1.1.2", known_fp_value="|")
    assert known_fp.main([]) == 0
    captured = capsys.readouterr()
    findings_block = captured.out.split("FINDINGS:", 1)[1]
    pos_1 = findings_block.index("UC-1.1.1")
    pos_2 = findings_block.index("UC-1.1.2")
    pos_3 = findings_block.index("UC-1.1.3")
    assert pos_1 < pos_2 < pos_3


# ---------------------------------------------------------------------------
# main() — snippet rendering and truncation
# ---------------------------------------------------------------------------


def test_main_snippet_printed_when_present(
    make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
) -> None:
    """The snippet line is printed under the finding when value is truthy."""
    make_uc("1.1.1", known_fp_value="TBD")
    assert known_fp.main([]) == 0
    captured = capsys.readouterr()
    assert "snippet: TBD" in captured.out


def test_main_snippet_not_printed_when_empty(
    make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
) -> None:
    """An empty value MED finding doesn't emit a snippet line."""
    make_uc("1.1.1", known_fp_value="")
    assert known_fp.main([]) == 0
    captured = capsys.readouterr()
    assert "snippet:" not in captured.out


def test_main_snippet_truncated_at_120_chars(
    make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
) -> None:
    """A long whitespace snippet (still MED via strip→empty) truncates at 120 chars.

    `_classify` decides on the *stripped* value but the ``snippet`` field
    keeps the **raw** value, so a 200-char whitespace string still produces
    a MED finding and exercises the ``snippet[:120]`` truncation.
    """
    long_whitespace = " " * 200
    make_uc("1.1.1", known_fp_value=long_whitespace)
    assert known_fp.main([]) == 0
    captured = capsys.readouterr()
    snippet_line = next(
        line for line in captured.out.splitlines() if line.startswith("        snippet:")
    )
    assert len(snippet_line) == len("        snippet: ") + 120


# ---------------------------------------------------------------------------
# main() — list truncation at 30
# ---------------------------------------------------------------------------


def test_main_finding_list_truncated_at_30(
    make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
) -> None:
    """Findings list is truncated at 30 with a `... and N more` footer."""
    for i in range(1, 33):
        make_uc(f"1.{i // 10 + 1}.{i % 10 + 1}", known_fp_value="|")
    assert known_fp.main([]) == 0
    captured = capsys.readouterr()
    assert "... and 2 more (output truncated)" in captured.out
    high_lines = [line for line in captured.out.splitlines() if line.startswith("[HIGH]")]
    assert len(high_lines) == 30


def test_main_exactly_30_findings_no_truncation_footer(
    make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
) -> None:
    """Exactly 30 findings → all printed, no `... and N more` footer."""
    for i in range(30):
        make_uc(f"1.{i // 10 + 1}.{i % 10 + 1}", known_fp_value="|")
    assert known_fp.main([]) == 0
    captured = capsys.readouterr()
    assert "... and" not in captured.out
    high_lines = [line for line in captured.out.splitlines() if line.startswith("[HIGH]")]
    assert len(high_lines) == 30


# ---------------------------------------------------------------------------
# main() — --check mode exit-code matrix
# ---------------------------------------------------------------------------


def test_main_check_mode_zero_findings_returns_zero(
    fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--check` with no findings returns 0."""
    assert known_fp.main(["--check"]) == 0


def test_main_check_mode_high_returns_one(
    make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--check` with at least one HIGH finding returns 1."""
    make_uc("1.1.1", known_fp_value="|")
    assert known_fp.main(["--check"]) == 1


def test_main_check_mode_med_only_returns_zero(
    make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--check` does NOT fail on MED-only findings."""
    make_uc("1.1.1", known_fp_value="")
    assert known_fp.main(["--check"]) == 0


def test_main_check_mode_low_only_returns_zero(
    make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--check` does NOT fail on LOW-only findings."""
    make_uc("1.1.1", known_fp_value="TBD")
    assert known_fp.main(["--check"]) == 0


def test_main_check_mode_high_among_others_still_returns_one(
    make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
) -> None:
    """A single HIGH alongside MED/LOW is enough to fail `--check`."""
    make_uc("1.1.1", known_fp_value="|")
    make_uc("1.1.2", known_fp_value="")
    make_uc("1.1.3", known_fp_value="TBD")
    assert known_fp.main(["--check"]) == 1


# ---------------------------------------------------------------------------
# main() — missing id field surfaces as UC-<unknown>
# ---------------------------------------------------------------------------


def test_main_missing_id_renders_unknown(
    fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A sidecar with no ``id`` field falls back to ``UC-<unknown>``."""
    cat = fake_repo / "content" / "cat-01-foo"
    cat.mkdir()
    sidecar = cat / "UC-1.1.1.json"
    sidecar.write_text(json.dumps({"knownFalsePositives": "|"}), encoding="utf-8")
    assert known_fp.main([]) == 0
    captured = capsys.readouterr()
    assert "UC-<unknown>" in captured.out
