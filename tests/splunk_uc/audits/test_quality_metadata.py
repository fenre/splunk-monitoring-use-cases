"""Unit tests pinning ``splunk_uc.audits.quality_metadata``.

The audit reports per-UC quality-metadata coverage off the built
``catalog.json``: percentage of UCs carrying a ``References``,
``Status``, ``Last reviewed``, ``Splunk versions``, ``Reviewer``, and
``Known false positives`` field. The last is only counted across the
security-relevant categories (9, 10, 14, 17, 22).

Coverage thresholds default to warn-only; the ``--strict`` flag flips
the exit code to 1 when any coverage measurement falls below its
target.

These tests are hermetic — each one builds a synthetic ``catalog.json``
under ``tmp_path`` and monkey-patches ``qm.CATALOG`` so the audit reads
the fixture instead of the live dist artefact.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any, Protocol

import pytest

from splunk_uc.audits import quality_metadata as qm


class WriteCatalog(Protocol):
    """Factory protocol for writing a synthetic ``catalog.json``."""

    def __call__(self, payload: dict[str, Any]) -> pathlib.Path: ...


@pytest.fixture
def fake_catalog(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """Build a fake catalog path and rewire ``qm.CATALOG``."""
    path = tmp_path / "catalog.json"
    monkeypatch.setattr(qm, "CATALOG", str(path))
    return path


@pytest.fixture
def write_catalog(fake_catalog: pathlib.Path) -> WriteCatalog:
    """Return a factory that writes the catalog payload."""

    def _make(payload: dict[str, Any]) -> pathlib.Path:
        fake_catalog.write_text(json.dumps(payload), encoding="utf-8")
        return fake_catalog

    return _make


def _build_uc(**overrides: Any) -> dict[str, Any]:
    """Return a UC dict with default fields and any overrides."""
    return overrides


def _build_catalog(*, cats: list[tuple[int, list[dict[str, Any]]]]) -> dict[str, Any]:
    """Build a catalog payload from a list of ``(cat_id, ucs)`` pairs."""
    data: list[dict[str, Any]] = []
    for cat_id, ucs in cats:
        data.append(
            {
                "i": cat_id,
                "s": [{"u": ucs}],
            }
        )
    return {"DATA": data}


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------


def test_script_dir_resolves_to_audits_directory() -> None:
    """``SCRIPT_DIR`` resolves to the audits/ package directory."""
    assert pathlib.Path(qm.SCRIPT_DIR).name == "audits"


def test_repo_root_resolves_to_three_parents_up() -> None:
    """``REPO_ROOT`` walks three parents up to land at the repo root."""
    repo_root = pathlib.Path(qm.REPO_ROOT)
    assert repo_root.is_absolute()
    assert (repo_root / "src" / "splunk_uc" / "audits").is_dir()


def test_catalog_prefers_dist_path_when_exists() -> None:
    """``CATALOG`` resolves to either dist/catalog.json or legacy fallback.

    The module-level ``CATALOG = _CATALOG_DIST if exists else _CATALOG_LEGACY``
    is evaluated at import time. We can't directly retest the if-branch
    here but we can pin that the resolved value is one of the two
    documented paths.
    """
    valid_paths = {qm._CATALOG_DIST, qm._CATALOG_LEGACY}
    assert qm.CATALOG in valid_paths


def test_security_cats_pinned_set() -> None:
    """``SECURITY_CATS`` is the documented frozen set of category IDs."""
    assert qm.SECURITY_CATS == {9, 10, 14, 17, 22}


def test_thresholds_pin_documented_values() -> None:
    """All six thresholds match the documented contract."""
    assert qm.THRESHOLDS == {
        "refs": 100.0,
        "status": 50.0,
        "reviewed": 30.0,
        "sver": 25.0,
        "rby": 25.0,
        "kfp_security": 60.0,
    }


def test_field_label_pins_documented_labels() -> None:
    """All six field labels match the documented contract."""
    assert qm.FIELD_LABEL == {
        "refs": "References",
        "status": "Status",
        "reviewed": "Last reviewed",
        "sver": "Splunk versions",
        "rby": "Reviewer",
        "kfp_security": "Known false positives (security cats)",
    }


def test_thresholds_and_field_label_have_identical_keys() -> None:
    """Both dicts share the same six keys — pinned against drift."""
    assert set(qm.THRESHOLDS.keys()) == set(qm.FIELD_LABEL.keys())


# ---------------------------------------------------------------------------
# load_catalog
# ---------------------------------------------------------------------------


def test_load_catalog_returns_parsed_payload(write_catalog: WriteCatalog) -> None:
    """A present catalog.json is parsed into a dict."""
    payload = {"DATA": [{"i": 1, "s": []}]}
    write_catalog(payload)
    assert qm.load_catalog() == payload


def test_load_catalog_exits_2_when_missing(
    fake_catalog: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Missing catalog.json exits with code 2 and writes to stderr."""
    with pytest.raises(SystemExit) as exc:
        qm.load_catalog()
    assert exc.value.code == 2
    captured = capsys.readouterr()
    assert "FAIL:" in captured.err
    assert "not found" in captured.err
    assert "Run 'make build'" in captured.err


def test_load_catalog_handles_unicode_payload(
    write_catalog: WriteCatalog,
) -> None:
    """UTF-8 content round-trips cleanly."""
    payload = {"DATA": [{"i": 1, "s": [{"u": [{"n": "éàñ 🚀"}]}]}]}
    write_catalog(payload)
    result = qm.load_catalog()
    assert result["DATA"][0]["s"][0]["u"][0]["n"] == "éàñ 🚀"


# ---------------------------------------------------------------------------
# iter_ucs
# ---------------------------------------------------------------------------


def test_iter_ucs_yields_cat_id_and_uc_pairs() -> None:
    """Iteration yields ``(cat_id, uc_dict)`` tuples."""
    catalog = _build_catalog(cats=[(1, [{"i": "1.1.1"}]), (2, [{"i": "2.1.1"}])])
    pairs = list(qm.iter_ucs(catalog))
    assert pairs == [(1, {"i": "1.1.1"}), (2, {"i": "2.1.1"})]


def test_iter_ucs_handles_missing_data_key() -> None:
    """Missing ``DATA`` key yields no UCs."""
    assert list(qm.iter_ucs({})) == []


def test_iter_ucs_handles_category_without_subcategories() -> None:
    """A category with empty ``s`` yields nothing."""
    catalog = {"DATA": [{"i": 1, "s": []}]}
    assert list(qm.iter_ucs(catalog)) == []


def test_iter_ucs_handles_subcategory_without_ucs() -> None:
    """A subcategory with empty ``u`` yields nothing."""
    catalog = {"DATA": [{"i": 1, "s": [{"u": []}]}]}
    assert list(qm.iter_ucs(catalog)) == []


def test_iter_ucs_yields_multiple_ucs_per_subcategory() -> None:
    """Multiple UCs in one subcategory all surface."""
    catalog = {"DATA": [{"i": 1, "s": [{"u": [{"i": "1.1.1"}, {"i": "1.1.2"}]}]}]}
    pairs = list(qm.iter_ucs(catalog))
    assert len(pairs) == 2
    assert pairs[0][0] == 1
    assert pairs[1][0] == 1


def test_iter_ucs_handles_missing_category_id() -> None:
    """Missing ``i`` field defaults to 0 via ``.get('i', 0)``."""
    catalog = {"DATA": [{"s": [{"u": [{"i": "x"}]}]}]}
    pairs = list(qm.iter_ucs(catalog))
    assert pairs == [(0, {"i": "x"})]


# ---------------------------------------------------------------------------
# compute_coverage
# ---------------------------------------------------------------------------


def test_compute_coverage_returns_empty_counts_for_empty_catalog() -> None:
    """An empty catalog → all counts at 0, total/sec_total 0."""
    counts, total, sec_total = qm.compute_coverage({"DATA": []})
    assert total == 0
    assert sec_total == 0
    for key in qm.FIELD_LABEL:
        assert counts[key]["present"] == 0


def test_compute_coverage_counts_string_field_present() -> None:
    """A non-empty string field counts as 'present'."""
    catalog = _build_catalog(cats=[(1, [{"refs": "https://example.com", "status": "verified"}])])
    counts, total, _ = qm.compute_coverage(catalog)
    assert total == 1
    assert counts["refs"]["present"] == 1
    assert counts["status"]["present"] == 1


def test_compute_coverage_skips_empty_string_field() -> None:
    """An empty or whitespace-only string does NOT count as present."""
    catalog = _build_catalog(cats=[(1, [{"refs": "", "status": "   "}])])
    counts, _, _ = qm.compute_coverage(catalog)
    assert counts["refs"]["present"] == 0
    assert counts["status"]["present"] == 0


def test_compute_coverage_counts_non_empty_list_field() -> None:
    """A non-empty list field counts as 'present'."""
    catalog = _build_catalog(cats=[(1, [{"refs": ["a", "b"]}])])
    counts, _, _ = qm.compute_coverage(catalog)
    assert counts["refs"]["present"] == 1


def test_compute_coverage_skips_empty_list_field() -> None:
    """An empty list does NOT count as present."""
    catalog = _build_catalog(cats=[(1, [{"refs": []}])])
    counts, _, _ = qm.compute_coverage(catalog)
    assert counts["refs"]["present"] == 0


def test_compute_coverage_skips_non_string_non_list_field() -> None:
    """Non-string non-list values (e.g. int, dict) don't count."""
    catalog = _build_catalog(cats=[(1, [{"refs": 42, "status": {"foo": "bar"}}])])
    counts, _, _ = qm.compute_coverage(catalog)
    assert counts["refs"]["present"] == 0
    assert counts["status"]["present"] == 0


def test_compute_coverage_skips_missing_field() -> None:
    """A missing field doesn't count (`.get(key)` returns None)."""
    catalog = _build_catalog(cats=[(1, [{}])])
    counts, _, _ = qm.compute_coverage(catalog)
    for key in ("refs", "status", "reviewed", "sver", "rby"):
        assert counts[key]["present"] == 0


def test_compute_coverage_tracks_security_total() -> None:
    """sec_total accumulates only for security categories."""
    catalog = _build_catalog(
        cats=[(1, [{"i": "1.1.1"}]), (9, [{"i": "9.1.1"}]), (22, [{"i": "22.1.1"}])]
    )
    _, total, sec_total = qm.compute_coverage(catalog)
    assert total == 3
    assert sec_total == 2


def test_compute_coverage_kfp_only_counted_for_security_cats() -> None:
    """``kfp`` is only counted for UCs in SECURITY_CATS."""
    catalog = _build_catalog(cats=[(1, [{"kfp": "noise"}]), (9, [{"kfp": "noise"}])])
    counts, total, sec_total = qm.compute_coverage(catalog)
    assert total == 2
    assert sec_total == 1
    # Only cat 9 contributes.
    assert counts["kfp_security"]["present"] == 1


def test_compute_coverage_kfp_skipped_when_empty(
    fake_catalog: pathlib.Path,
) -> None:
    """An empty ``kfp`` on a security cat does NOT count as present."""
    catalog = _build_catalog(cats=[(9, [{"kfp": ""}])])
    counts, _, _ = qm.compute_coverage(catalog)
    assert counts["kfp_security"]["present"] == 0


def test_compute_coverage_kfp_skipped_when_non_string(
    fake_catalog: pathlib.Path,
) -> None:
    """Non-string ``kfp`` (e.g. list) does NOT count for security cats."""
    catalog = _build_catalog(cats=[(9, [{"kfp": ["item"]}])])
    counts, _, _ = qm.compute_coverage(catalog)
    assert counts["kfp_security"]["present"] == 0


def test_compute_coverage_counts_all_five_string_or_list_fields() -> None:
    """All five fields (refs, status, reviewed, sver, rby) accumulate."""
    catalog = _build_catalog(
        cats=[
            (
                1,
                [
                    {
                        "refs": "url",
                        "status": "verified",
                        "reviewed": "2026-05-19",
                        "sver": "9.0",
                        "rby": "@reviewer",
                    }
                ],
            )
        ]
    )
    counts, _, _ = qm.compute_coverage(catalog)
    for key in ("refs", "status", "reviewed", "sver", "rby"):
        assert counts[key]["present"] == 1


# ---------------------------------------------------------------------------
# main() — happy paths
# ---------------------------------------------------------------------------


def test_main_returns_0_when_all_targets_met(
    write_catalog: WriteCatalog, capsys: pytest.CaptureFixture[str]
) -> None:
    """A catalog with every field on every UC → exit 0 with success message."""
    catalog = _build_catalog(
        cats=[
            (
                9,
                [
                    {
                        "refs": "url",
                        "status": "verified",
                        "reviewed": "2026-05-19",
                        "sver": "9.0",
                        "rby": "@reviewer",
                        "kfp": "false positives noted",
                    }
                ],
            )
        ]
    )
    write_catalog(catalog)
    assert qm.main([]) == 0
    captured = capsys.readouterr()
    assert "All coverage targets met." in captured.out


def test_main_argv_none_uses_sys_argv_default(
    write_catalog: WriteCatalog,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``argv=None`` falls through to argparse's ``sys.argv`` default."""
    monkeypatch.setattr("sys.argv", ["audit-quality-metadata"])
    write_catalog({"DATA": []})
    qm.main(None)


def test_main_help_exits_clean(capsys: pytest.CaptureFixture[str]) -> None:
    """``--help`` exits with code 0 and prints argparse help."""
    with pytest.raises(SystemExit) as exc:
        qm.main(["--help"])
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "--strict" in captured.out


# ---------------------------------------------------------------------------
# main() — coverage rendering
# ---------------------------------------------------------------------------


def test_main_renders_total_uc_count(
    write_catalog: WriteCatalog, capsys: pytest.CaptureFixture[str]
) -> None:
    """Header shows ``total UCs:`` count and ``security-cat UCs:`` count."""
    catalog = _build_catalog(cats=[(1, [{"i": "1.1.1"}]), (9, [{"i": "9.1.1"}])])
    write_catalog(catalog)
    qm.main([])
    captured = capsys.readouterr()
    assert "total UCs: 2" in captured.out
    assert "security-cat UCs: 1" in captured.out


def test_main_renders_dashed_separator_lines(
    write_catalog: WriteCatalog, capsys: pytest.CaptureFixture[str]
) -> None:
    """Output uses 70-char ``-`` separator before and after the table."""
    write_catalog({"DATA": []})
    qm.main([])
    captured = capsys.readouterr()
    assert "-" * 70 in captured.out


def test_main_renders_progress_bar_for_each_field(
    write_catalog: WriteCatalog, capsys: pytest.CaptureFixture[str]
) -> None:
    """One row per field with a ``[##....]`` progress bar."""
    write_catalog({"DATA": []})
    qm.main([])
    captured = capsys.readouterr()
    # 6 fields → 6 rows with [bar] markers
    bar_line_count = sum(
        1 for line in captured.out.splitlines() if "[" in line and "]" in line and "%" in line
    )
    assert bar_line_count == 6


def test_main_progress_bar_at_zero_percent_shows_all_dots(
    write_catalog: WriteCatalog, capsys: pytest.CaptureFixture[str]
) -> None:
    """0% coverage shows the bar as all dots (no hashes)."""
    write_catalog({"DATA": [{"i": 1, "s": [{"u": [{"i": "1.1.1"}]}]}]})
    qm.main([])
    captured = capsys.readouterr()
    # At 0% coverage every bar should be 20 dots.
    assert "[" + "." * 20 + "]" in captured.out


def test_main_progress_bar_at_100_percent_shows_all_hashes(
    write_catalog: WriteCatalog, capsys: pytest.CaptureFixture[str]
) -> None:
    """100% coverage shows the bar as all hashes (no dots)."""
    catalog = _build_catalog(
        cats=[
            (
                9,
                [
                    {
                        "refs": "u",
                        "status": "s",
                        "reviewed": "r",
                        "sver": "v",
                        "rby": "b",
                        "kfp": "k",
                    }
                ],
            )
        ]
    )
    write_catalog(catalog)
    qm.main([])
    captured = capsys.readouterr()
    # At 100% coverage every bar should be 20 hashes.
    assert "[" + "#" * 20 + "]" in captured.out


def test_main_renders_status_marker_ok_or_below(
    write_catalog: WriteCatalog, capsys: pytest.CaptureFixture[str]
) -> None:
    """Each row carries an ``OK`` or ``BELOW`` status marker."""
    write_catalog({"DATA": []})
    qm.main([])
    captured = capsys.readouterr()
    # Empty catalog → all 6 fields at 0% → all BELOW
    assert captured.out.count(" BELOW") == 6


def test_main_renders_present_over_denom(
    write_catalog: WriteCatalog, capsys: pytest.CaptureFixture[str]
) -> None:
    """Each row carries the ``(N/D)`` present-over-denom fraction."""
    catalog = _build_catalog(cats=[(1, [{"refs": "u"}])])
    write_catalog(catalog)
    qm.main([])
    captured = capsys.readouterr()
    assert "(1/1)" in captured.out


def test_main_kfp_denom_is_security_total_not_total(
    write_catalog: WriteCatalog, capsys: pytest.CaptureFixture[str]
) -> None:
    """KFP row uses ``sec_total`` not ``total`` as the denominator."""
    catalog = _build_catalog(
        cats=[
            (1, [{"i": "1.1.1"}]),
            (9, [{"i": "9.1.1", "kfp": "noise"}]),
        ]
    )
    write_catalog(catalog)
    qm.main([])
    captured = capsys.readouterr()
    # KFP: 1 present out of 1 security cat → 100.0%
    kfp_line = next(line for line in captured.out.splitlines() if "Known false positives" in line)
    assert "(1/1)" in kfp_line


# ---------------------------------------------------------------------------
# main() — failure surfacing
# ---------------------------------------------------------------------------


def test_main_lists_failed_targets_when_below_threshold(
    write_catalog: WriteCatalog, capsys: pytest.CaptureFixture[str]
) -> None:
    """Each below-threshold field surfaces in the failure list."""
    write_catalog({"DATA": [{"i": 1, "s": [{"u": [{"i": "x"}]}]}]})
    qm.main([])
    captured = capsys.readouterr()
    assert "coverage target(s) below threshold" in captured.out
    for label in qm.FIELD_LABEL.values():
        assert f"- {label}" in captured.out


def test_main_strict_returns_1_when_any_target_below(
    write_catalog: WriteCatalog,
) -> None:
    """``--strict`` flips exit code to 1 when any target falls short."""
    write_catalog({"DATA": [{"i": 1, "s": [{"u": [{"i": "x"}]}]}]})
    assert qm.main(["--strict"]) == 1


def test_main_warn_only_returns_0_with_strict_hint(
    write_catalog: WriteCatalog, capsys: pytest.CaptureFixture[str]
) -> None:
    """Without ``--strict``, below-threshold exits 0 with the hint message."""
    write_catalog({"DATA": [{"i": 1, "s": [{"u": [{"i": "x"}]}]}]})
    assert qm.main([]) == 0
    captured = capsys.readouterr()
    assert "(warn-only; pass --strict to fail)" in captured.out


def test_main_strict_does_not_emit_warn_hint(
    write_catalog: WriteCatalog, capsys: pytest.CaptureFixture[str]
) -> None:
    """``--strict`` mode does NOT print the warn-only hint."""
    write_catalog({"DATA": [{"i": 1, "s": [{"u": [{"i": "x"}]}]}]})
    assert qm.main(["--strict"]) == 1
    captured = capsys.readouterr()
    assert "(warn-only; pass --strict to fail)" not in captured.out


def test_main_propagates_load_catalog_exit_2(
    fake_catalog: pathlib.Path,
) -> None:
    """Missing catalog.json propagates the ``SystemExit(2)`` from load_catalog."""
    with pytest.raises(SystemExit) as exc:
        qm.main([])
    assert exc.value.code == 2


# ---------------------------------------------------------------------------
# main() — empty-catalog edge case
# ---------------------------------------------------------------------------


def test_main_empty_catalog_no_division_by_zero(
    write_catalog: WriteCatalog, capsys: pytest.CaptureFixture[str]
) -> None:
    """Empty catalog → 0.0% for every field, no ZeroDivisionError."""
    write_catalog({"DATA": []})
    assert qm.main([]) == 0
    captured = capsys.readouterr()
    # 6 fields all rendered at 0.0%
    assert captured.out.count("  0.0%") == 6
