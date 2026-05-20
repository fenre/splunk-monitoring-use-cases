"""Comprehensive unit tests for ``src/splunk_uc/audits/baseline_clause_grammar_free.py``.

Pins every documented contract of the Phase F drift guard that prevents
``clause-grammar`` fingerprints from being re-introduced into the audit
baseline.

Pinned contracts:
- Module-level constants (``REPO_ROOT`` resolves, ``BASELINE_PATH`` resolves,
  ``BASELINEABLE_FP_FIELD == "fingerprints"``, ``FORBIDDEN_CODES`` is the
  documented frozen set of one).
- The ``_is_forbidden`` helper (splits on tab, only the first field is
  checked, substring matches inside later fields do NOT trigger).
- The ``main()`` exit-code matrix (0 = invariant holds, 1 = invariant
  violated or baseline missing or fingerprints field non-list, 2 = I/O or
  JSON parse error).
- Truncation at 20 offender lines with `... and N more.` footer.
- The success message includes a sorted ``FORBIDDEN_CODES`` echo.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any, Protocol

import pytest

from splunk_uc.audits import baseline_clause_grammar_free as bcgf


class WriteBaseline(Protocol):
    def __call__(self, data: Any) -> pathlib.Path: ...


@pytest.fixture
def fake_repo(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """Patch ``REPO_ROOT`` and ``BASELINE_PATH`` to point at a temp tree."""
    baseline = tmp_path / "tests" / "golden" / "audit-baseline.json"
    baseline.parent.mkdir(parents=True)
    monkeypatch.setattr(bcgf, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(bcgf, "BASELINE_PATH", baseline)
    return tmp_path


@pytest.fixture
def write_baseline(fake_repo: pathlib.Path) -> WriteBaseline:
    """Factory that materialises a baseline JSON file with arbitrary contents."""

    def _make(data: Any) -> pathlib.Path:
        path = pathlib.Path(bcgf.BASELINE_PATH)
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    return _make


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------


def test_repo_root_is_absolute_path() -> None:
    """`REPO_ROOT` is a resolved absolute Path at import time."""
    assert isinstance(bcgf.REPO_ROOT, pathlib.Path)
    assert bcgf.REPO_ROOT.is_absolute()


def test_baseline_path_points_under_repo_root() -> None:
    """`BASELINE_PATH` is `<REPO_ROOT>/tests/golden/audit-baseline.json`."""
    expected = bcgf.REPO_ROOT / "tests" / "golden" / "audit-baseline.json"
    assert bcgf.BASELINE_PATH == expected


def test_baselineable_fp_field_is_fingerprints() -> None:
    """The JSON key is `fingerprints` — pinned against silent rename."""
    assert bcgf.BASELINEABLE_FP_FIELD == "fingerprints"


def test_forbidden_codes_is_clause_grammar_only() -> None:
    """`FORBIDDEN_CODES` is the documented frozen set of exactly one code."""
    assert bcgf.FORBIDDEN_CODES == frozenset({"clause-grammar"})
    assert isinstance(bcgf.FORBIDDEN_CODES, frozenset)


# ---------------------------------------------------------------------------
# _is_forbidden
# ---------------------------------------------------------------------------


def test_is_forbidden_clause_grammar_simple() -> None:
    """A fingerprint starting with `clause-grammar\\t...` is forbidden."""
    assert bcgf._is_forbidden("clause-grammar\tUC-1.1.1\tpath.json\tMessage")


def test_is_forbidden_other_code_passes() -> None:
    """A fingerprint with any other code is allowed."""
    assert not bcgf._is_forbidden("clause-unknown\tUC-1.1.1\tpath.json\tMessage")


def test_is_forbidden_substring_in_other_field_not_caught() -> None:
    """The check only inspects the FIRST tab-separated field.

    A `clause-grammar` substring inside the message of a `clause-unknown`
    finding must NOT trigger the guard.
    """
    fp = "clause-unknown\tUC-1.1.1\tpath.json\tclause-grammar mentioned in msg"
    assert not bcgf._is_forbidden(fp)


def test_is_forbidden_code_whitespace_stripped() -> None:
    """Leading/trailing whitespace on the code field is stripped before check."""
    assert bcgf._is_forbidden("  clause-grammar  \tUC-1.1.1\tpath\tMessage")


def test_is_forbidden_no_tab_treats_entire_string_as_code() -> None:
    """If the fingerprint has no tab, `split('\\t', 1)[0]` returns the whole string."""
    assert bcgf._is_forbidden("clause-grammar")
    assert not bcgf._is_forbidden("clause-unknown")


def test_is_forbidden_only_first_split_used() -> None:
    """The `maxsplit=1` argument prevents over-splitting on later tabs."""
    fp = "clause-grammar\tUC-1.1.1\twith\ttabs\there"
    assert bcgf._is_forbidden(fp)


def test_is_forbidden_empty_string() -> None:
    """Empty string splits to `[""]` → first field is empty → not forbidden."""
    assert not bcgf._is_forbidden("")


def test_is_forbidden_case_sensitive() -> None:
    """Code matching is case-sensitive (no .lower() in the check)."""
    assert not bcgf._is_forbidden("Clause-Grammar\tUC\tpath\tmsg")
    assert not bcgf._is_forbidden("CLAUSE-GRAMMAR\tUC\tpath\tmsg")


# ---------------------------------------------------------------------------
# main() — missing baseline
# ---------------------------------------------------------------------------


def test_main_missing_baseline_returns_one(
    fake_repo: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Missing baseline file produces a `::error::` line and exits 1."""
    assert bcgf.main([]) == 1
    err = capsys.readouterr().err
    assert "::error::Phase F drift guard" in err
    assert "is missing" in err
    assert "tests/golden/audit-baseline.json" in err


def test_main_baseline_dir_present_but_file_missing(
    fake_repo: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`is_file()` correctly distinguishes a file from a directory of same name."""
    bcgf.BASELINE_PATH.unlink(missing_ok=True)
    bcgf.BASELINE_PATH.mkdir()
    assert bcgf.main([]) == 1
    err = capsys.readouterr().err
    assert "::error::" in err
    assert "is missing" in err


# ---------------------------------------------------------------------------
# main() — JSON parse failure
# ---------------------------------------------------------------------------


def test_main_invalid_json_returns_two(
    fake_repo: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Malformed JSON yields exit code 2 (I/O / parse error)."""
    bcgf.BASELINE_PATH.write_text("{not valid json", encoding="utf-8")
    assert bcgf.main([]) == 2
    err = capsys.readouterr().err
    assert "::error::Phase F drift guard: cannot parse" in err
    assert "tests/golden/audit-baseline.json" in err


def test_main_unreadable_baseline_returns_two(
    fake_repo: pathlib.Path,
    write_baseline: WriteBaseline,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An OSError during read also returns exit 2."""
    write_baseline({"fingerprints": []})

    def raise_oserror(*args: Any, **kwargs: Any) -> str:
        raise OSError("simulated I/O failure")

    monkeypatch.setattr(pathlib.Path, "read_text", raise_oserror)
    assert bcgf.main([]) == 2
    err = capsys.readouterr().err
    assert "::error::" in err
    assert "cannot parse" in err
    assert "simulated I/O failure" in err


# ---------------------------------------------------------------------------
# main() — non-list fingerprints field
# ---------------------------------------------------------------------------


def test_main_non_list_fingerprints_returns_one(
    fake_repo: pathlib.Path,
    write_baseline: WriteBaseline,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A non-list `fingerprints` field returns exit 1 with type error."""
    write_baseline({"fingerprints": "not-a-list"})
    assert bcgf.main([]) == 1
    err = capsys.readouterr().err
    assert "fingerprints must be a list" in err
    assert "got str" in err


def test_main_dict_fingerprints_returns_one(
    fake_repo: pathlib.Path,
    write_baseline: WriteBaseline,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A dict `fingerprints` field returns exit 1 with `got dict`."""
    write_baseline({"fingerprints": {"k": "v"}})
    assert bcgf.main([]) == 1
    err = capsys.readouterr().err
    assert "got dict" in err


def test_main_falsy_fingerprints_treated_as_empty(
    fake_repo: pathlib.Path,
    write_baseline: WriteBaseline,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`fingerprints: null` → `data.get(..., []) or []` substitutes empty list."""
    write_baseline({"fingerprints": None})
    assert bcgf.main([]) == 0
    out = capsys.readouterr().out
    assert "Phase F invariant OK" in out
    assert "total fingerprints: 0" in out


def test_main_missing_fingerprints_key_returns_zero(
    fake_repo: pathlib.Path,
    write_baseline: WriteBaseline,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Missing `fingerprints` key defaults to empty list."""
    write_baseline({"other_field": "stuff"})
    assert bcgf.main([]) == 0
    out = capsys.readouterr().out
    assert "Phase F invariant OK" in out


# ---------------------------------------------------------------------------
# main() — happy paths
# ---------------------------------------------------------------------------


def test_main_empty_fingerprints_returns_zero(
    fake_repo: pathlib.Path,
    write_baseline: WriteBaseline,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Empty fingerprints list passes."""
    write_baseline({"fingerprints": []})
    assert bcgf.main([]) == 0
    out = capsys.readouterr().out
    assert "Phase F invariant OK" in out
    assert "total fingerprints: 0" in out


def test_main_only_other_codes_returns_zero(
    fake_repo: pathlib.Path,
    write_baseline: WriteBaseline,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Fingerprints of OTHER codes (not clause-grammar) all pass."""
    write_baseline(
        {
            "fingerprints": [
                "spl-grammar\tUC-1.1.1\tpath.json\tmsg",
                "missing-field\tUC-1.1.2\tpath.json\tmsg",
                "unknown-other\tUC-1.1.3\tpath.json\tmsg",
            ]
        }
    )
    assert bcgf.main([]) == 0
    out = capsys.readouterr().out
    assert "Phase F invariant OK" in out
    assert "total fingerprints: 3" in out


def test_main_success_echoes_forbidden_codes_sorted(
    fake_repo: pathlib.Path,
    write_baseline: WriteBaseline,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The success message echoes `sorted(FORBIDDEN_CODES)`."""
    write_baseline({"fingerprints": []})
    assert bcgf.main([]) == 0
    out = capsys.readouterr().out
    assert "forbidden codes: ['clause-grammar']" in out


# ---------------------------------------------------------------------------
# main() — invariant violations
# ---------------------------------------------------------------------------


def test_main_single_forbidden_returns_one(
    fake_repo: pathlib.Path,
    write_baseline: WriteBaseline,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """One forbidden fingerprint triggers exit 1 + the canonical error."""
    write_baseline({"fingerprints": ["clause-grammar\tUC-1.1.1\tpath.json\tMessage"]})
    assert bcgf.main([]) == 1
    err = capsys.readouterr().err
    assert "::error::Phase F invariant violated" in err
    assert "1 forbidden-code fingerprint(s)" in err
    assert "clause-grammar\tUC-1.1.1\tpath.json\tMessage" in err


def test_main_multiple_forbidden_listed(
    fake_repo: pathlib.Path,
    write_baseline: WriteBaseline,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Multiple forbidden fingerprints all listed in error output."""
    fps = [f"clause-grammar\tUC-1.1.{i}\tpath{i}.json\tmsg" for i in range(1, 6)]
    write_baseline({"fingerprints": fps})
    assert bcgf.main([]) == 1
    err = capsys.readouterr().err
    assert "5 forbidden-code fingerprint(s)" in err
    for fp in fps:
        assert fp in err


def test_main_forbidden_offender_list_truncated_at_twenty(
    fake_repo: pathlib.Path,
    write_baseline: WriteBaseline,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Offender list is truncated at 20 with `… and N more.` footer."""
    fps = [f"clause-grammar\tUC-1.1.{i}\tpath{i}.json\tmsg" for i in range(25)]
    write_baseline({"fingerprints": fps})
    assert bcgf.main([]) == 1
    err = capsys.readouterr().err
    assert "25 forbidden-code fingerprint(s)" in err
    bullet_lines = [line for line in err.splitlines() if line.startswith("  - ")]
    assert len(bullet_lines) == 20
    assert "… and 5 more." in err


def test_main_forbidden_exactly_twenty_no_truncation_footer(
    fake_repo: pathlib.Path,
    write_baseline: WriteBaseline,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Exactly 20 offenders → all 20 printed, no `… and N more.` footer."""
    fps = [f"clause-grammar\tUC-1.1.{i}\tpath{i}.json\tmsg" for i in range(20)]
    write_baseline({"fingerprints": fps})
    assert bcgf.main([]) == 1
    err = capsys.readouterr().err
    assert "20 forbidden-code fingerprint(s)" in err
    bullet_lines = [line for line in err.splitlines() if line.startswith("  - ")]
    assert len(bullet_lines) == 20
    assert "… and" not in err


def test_main_mixed_forbidden_and_allowed(
    fake_repo: pathlib.Path,
    write_baseline: WriteBaseline,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A mix of forbidden and allowed codes counts only the forbidden ones."""
    write_baseline(
        {
            "fingerprints": [
                "spl-grammar\tUC-1.1.1\tp\tm",
                "clause-grammar\tUC-1.1.2\tp\tm",
                "missing-field\tUC-1.1.3\tp\tm",
                "clause-grammar\tUC-1.1.4\tp\tm",
            ]
        }
    )
    assert bcgf.main([]) == 1
    err = capsys.readouterr().err
    assert "2 forbidden-code fingerprint(s)" in err
    assert "UC-1.1.2" in err
    assert "UC-1.1.4" in err


# ---------------------------------------------------------------------------
# main() — edge cases
# ---------------------------------------------------------------------------


def test_main_non_string_entries_skipped(
    fake_repo: pathlib.Path,
    write_baseline: WriteBaseline,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Non-string entries in the fingerprints list are silently skipped."""
    write_baseline(
        {
            "fingerprints": [
                42,
                None,
                ["list", "of", "things"],
                "clause-grammar\tUC-1.1.1\tp\tm",
            ]
        }
    )
    assert bcgf.main([]) == 1
    err = capsys.readouterr().err
    assert "1 forbidden-code fingerprint(s)" in err


def test_main_argv_is_ignored(
    fake_repo: pathlib.Path,
    write_baseline: WriteBaseline,
) -> None:
    """`del argv` means any argv list is accepted without parsing."""
    write_baseline({"fingerprints": []})
    assert bcgf.main(["--unknown", "foo", "bar"]) == 0


def test_main_argv_none_accepted(
    fake_repo: pathlib.Path,
    write_baseline: WriteBaseline,
) -> None:
    """`argv=None` is accepted (also discarded via `del argv`)."""
    write_baseline({"fingerprints": []})
    assert bcgf.main(None) == 0


def test_main_error_message_includes_forbidden_codes_sorted(
    fake_repo: pathlib.Path,
    write_baseline: WriteBaseline,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Error output echoes `sorted(FORBIDDEN_CODES)` so future additions show."""
    write_baseline({"fingerprints": ["clause-grammar\tUC-1.1.1\tp\tm"]})
    assert bcgf.main([]) == 1
    err = capsys.readouterr().err
    assert "['clause-grammar']" in err
    assert "cannot be baselined" in err
    assert "Fix the underlying issues" in err
