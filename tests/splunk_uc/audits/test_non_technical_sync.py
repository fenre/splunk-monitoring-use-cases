"""Unit tests for ``splunk_uc.audits.non_technical_sync``.

P16 wave BB: lifts ``src/splunk_uc/audits/non_technical_sync.py``
from ~6% to ~99% combined coverage. Pins every documented contract
of the audit that cross-checks ``non-technical-view.js`` against the
JSON SSOT (``content/cat-NN-<slug>/UC-*.json``):

(a) every UC id referenced from JS exists in some sidecar
(b) every content/cat-NN-*/ folder has a top-level entry in JS
(c) every subcategory ``X.Y`` has at least one representative UC in
    the matching JS area
(d) every JS numeric category key has a matching content folder
"""

from __future__ import annotations

import json
import pathlib
from collections.abc import Callable
from typing import Any

import pytest

from splunk_uc.audits import non_technical_sync as nts

MakeUC = Callable[[int, str, dict[str, Any]], pathlib.Path]
MakeJS = Callable[[str], pathlib.Path]


@pytest.fixture
def fake_repo(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """Build a hermetic repo with content/ + non-technical-view.js."""
    (tmp_path / "content").mkdir()
    monkeypatch.setattr(nts, "REPO", tmp_path)
    monkeypatch.setattr(nts, "JS_PATH", tmp_path / "non-technical-view.js")
    monkeypatch.setattr(nts, "CONTENT", tmp_path / "content")
    return tmp_path


@pytest.fixture
def make_uc(fake_repo: pathlib.Path) -> MakeUC:
    def _make(category: int, uc_id: str, payload: dict[str, Any]) -> pathlib.Path:
        cat_dir = fake_repo / "content" / f"cat-{category:02d}-test-cat"
        cat_dir.mkdir(parents=True, exist_ok=True)
        sidecar = cat_dir / f"UC-{uc_id}.json"
        merged = {"id": uc_id, **payload}
        sidecar.write_text(json.dumps(merged, indent=2), encoding="utf-8")
        return sidecar

    return _make


@pytest.fixture
def make_js(fake_repo: pathlib.Path) -> MakeJS:
    def _make(js_text: str) -> pathlib.Path:
        path: pathlib.Path = nts.JS_PATH
        path.write_text(js_text, encoding="utf-8")
        return path

    return _make


# ---------------------------------------------------------------------------
# Module-level invariants
# ---------------------------------------------------------------------------


class TestModuleConstants:
    def test_re_id_matches_full_uc_id(self) -> None:
        m = nts.RE_ID.search('id: "1.2.3"')
        assert m is not None
        assert m.group(1) == "1"
        assert m.group(2) == "2"
        assert m.group(3) == "3"

    def test_re_id_matches_multi_digit_segments(self) -> None:
        m = nts.RE_ID.search('id: "22.10.105"')
        assert m is not None
        assert m.group(1) == "22"
        assert m.group(2) == "10"
        assert m.group(3) == "105"

    def test_re_id_rejects_two_segments(self) -> None:
        assert nts.RE_ID.search('id: "1.2"') is None

    def test_re_id_allows_extra_whitespace(self) -> None:
        m = nts.RE_ID.search('id:   "1.2.3"')
        assert m is not None

    def test_re_cat_dir_matches_zero_padded(self) -> None:
        m = nts.RE_CAT_DIR.match("cat-01-server-compute")
        assert m is not None
        assert m.group(1) == "01"

    def test_re_cat_dir_rejects_unpadded(self) -> None:
        assert nts.RE_CAT_DIR.match("cat-1-server") is None

    def test_re_cat_dir_rejects_non_cat_prefix(self) -> None:
        assert nts.RE_CAT_DIR.match("foo-01-stuff") is None

    def test_repo_root_resolves_to_real_repo(self) -> None:
        import importlib

        fresh = importlib.reload(nts)
        assert (fresh.REPO / "content").is_dir()


# ---------------------------------------------------------------------------
# extract_top_level_string_keys
# ---------------------------------------------------------------------------


class TestExtractTopLevelStringKeys:
    def test_raises_when_anchor_missing(self) -> None:
        with pytest.raises(ValueError, match=r"window\.NON_TECHNICAL"):
            nts.extract_top_level_string_keys("var x = 1;")

    def test_extracts_single_key(self) -> None:
        js = 'window.NON_TECHNICAL = { "1": { } };'
        assert nts.extract_top_level_string_keys(js) == ["1"]

    def test_extracts_multiple_keys(self) -> None:
        js = 'window.NON_TECHNICAL = { "1": { }, "2": { }, "3": { } };'
        assert nts.extract_top_level_string_keys(js) == ["1", "2", "3"]

    def test_ignores_nested_keys(self) -> None:
        js = 'window.NON_TECHNICAL = { "1": { "nested": "value", "deeper": { "inner": 42 } } };'
        # Only "1" is at depth 1.
        assert nts.extract_top_level_string_keys(js) == ["1"]

    def test_handles_keys_with_whitespace_before_colon(self) -> None:
        js = 'window.NON_TECHNICAL = { "5"  :  { } };'
        assert nts.extract_top_level_string_keys(js) == ["5"]

    def test_skips_string_values_at_depth_1(self) -> None:
        # A bare string that's NOT a key (e.g., comments) shouldn't be
        # picked up. But the parser only looks at strings followed by ":".
        js = 'window.NON_TECHNICAL = { "1": { }, "notkey-without-colon" "still" };'
        # The parser scans on, but the second string isn't followed by ":{".
        result = nts.extract_top_level_string_keys(js)
        assert "1" in result
        assert "notkey-without-colon" not in result

    def test_handles_escaped_quotes_in_key(self) -> None:
        js = r'window.NON_TECHNICAL = { "a\"b": { } };'
        # The parser handles backslash-escapes via j += 2.
        result = nts.extract_top_level_string_keys(js)
        assert len(result) == 1
        assert result[0] == r"a\"b"

    def test_empty_object_returns_empty(self) -> None:
        js = "window.NON_TECHNICAL = { };"
        assert nts.extract_top_level_string_keys(js) == []

    def test_breaks_at_outer_close_brace(self) -> None:
        js = 'window.NON_TECHNICAL = { "1": { } }; var after = { "x": 1 };'
        # After the outer object closes (depth 0), parsing stops.
        assert nts.extract_top_level_string_keys(js) == ["1"]

    def test_key_followed_by_non_brace_value_ignored(self) -> None:
        # The parser only counts keys whose value is "{ ... }".
        js = 'window.NON_TECHNICAL = { "scalar": 42, "obj": { } };'
        result = nts.extract_top_level_string_keys(js)
        assert "obj" in result
        assert "scalar" not in result


# ---------------------------------------------------------------------------
# parse_js_category_blocks
# ---------------------------------------------------------------------------


class TestParseJsCategoryBlocks:
    def test_raises_when_anchor_missing(self) -> None:
        with pytest.raises(ValueError, match=r"window\.NON_TECHNICAL"):
            nts.parse_js_category_blocks("var x = 1;")

    def test_single_block_extracted(self) -> None:
        js = 'window.NON_TECHNICAL = { "1": { id: "1.1.1" } };'
        blocks = nts.parse_js_category_blocks(js)
        assert "1" in blocks
        assert 'id: "1.1.1"' in blocks["1"]

    def test_multiple_blocks_extracted(self) -> None:
        js = 'window.NON_TECHNICAL = { "1": { id: "1.1.1" }, "2": { id: "2.1.1" } };'
        blocks = nts.parse_js_category_blocks(js)
        assert set(blocks.keys()) == {"1", "2"}
        assert 'id: "1.1.1"' in blocks["1"]
        assert 'id: "2.1.1"' in blocks["2"]

    def test_nested_braces_inside_block_preserved(self) -> None:
        js = 'window.NON_TECHNICAL = { "1": { areas: [{ id: "1.1.1" }] } };'
        blocks = nts.parse_js_category_blocks(js)
        assert "1" in blocks
        assert "areas" in blocks["1"]
        assert 'id: "1.1.1"' in blocks["1"]

    def test_empty_object_returns_empty(self) -> None:
        js = "window.NON_TECHNICAL = { };"
        assert nts.parse_js_category_blocks(js) == {}

    def test_escaped_quotes_in_key(self) -> None:
        js = r'window.NON_TECHNICAL = { "a\"b": { id: "1.1.1" } };'
        blocks = nts.parse_js_category_blocks(js)
        assert r"a\"b" in blocks

    def test_handles_whitespace_around_colon(self) -> None:
        js = 'window.NON_TECHNICAL = { "5"   :   { id: "5.1.1" } };'
        blocks = nts.parse_js_category_blocks(js)
        assert "5" in blocks
        assert 'id: "5.1.1"' in blocks["5"]

    def test_scalar_value_keys_ignored(self) -> None:
        js = 'window.NON_TECHNICAL = { "scalar": 42, "obj": { id: "1.1.1" } };'
        blocks = nts.parse_js_category_blocks(js)
        assert "scalar" not in blocks
        assert "obj" in blocks


# ---------------------------------------------------------------------------
# collect_ssot_categories
# ---------------------------------------------------------------------------


class TestCollectSsotCategories:
    def test_empty_content_dir(self, fake_repo: pathlib.Path) -> None:
        cat_dir, ucs, subcats = nts.collect_ssot_categories()
        assert cat_dir == {}
        assert ucs == {}
        assert subcats == {}

    def test_single_uc_collected(self, make_uc: MakeUC) -> None:
        make_uc(1, "1.1.1", {})
        cat_dir, ucs, subcats = nts.collect_ssot_categories()
        assert 1 in cat_dir
        assert ucs == {1: {"1.1.1"}}
        assert subcats == {1: {"1.1"}}

    def test_multiple_subcategories_collected(self, make_uc: MakeUC) -> None:
        make_uc(1, "1.1.1", {})
        make_uc(1, "1.2.1", {})
        make_uc(1, "1.2.2", {})
        _cat_dir, ucs, subcats = nts.collect_ssot_categories()
        assert ucs[1] == {"1.1.1", "1.2.1", "1.2.2"}
        assert subcats[1] == {"1.1", "1.2"}

    def test_skips_unparseable_sidecar(self, make_uc: MakeUC, fake_repo: pathlib.Path) -> None:
        make_uc(1, "1.1.1", {})
        bad = fake_repo / "content" / "cat-01-test-cat" / "UC-1.1.2.json"
        bad.write_text("not valid json", encoding="utf-8")
        _cat_dir, ucs, _subcats = nts.collect_ssot_categories()
        assert ucs[1] == {"1.1.1"}

    def test_skips_uc_with_mismatched_category(self, make_uc: MakeUC) -> None:
        # If a UC sits inside cat-01 but its id starts with "2.", it's skipped.
        make_uc(1, "2.1.1", {})
        _cat_dir, ucs, subcats = nts.collect_ssot_categories()
        assert ucs == {}
        assert subcats == {}

    def test_skips_uc_with_missing_id(self, make_uc: MakeUC, fake_repo: pathlib.Path) -> None:
        sidecar = fake_repo / "content" / "cat-01-test-cat" / "UC-1.1.1.json"
        sidecar.parent.mkdir(parents=True, exist_ok=True)
        sidecar.write_text(json.dumps({}), encoding="utf-8")
        _cat_dir, ucs, _subcats = nts.collect_ssot_categories()
        assert ucs == {}

    def test_skips_uc_with_invalid_id_format(self, fake_repo: pathlib.Path) -> None:
        sidecar = fake_repo / "content" / "cat-01-test-cat" / "UC-bogus.json"
        sidecar.parent.mkdir(parents=True, exist_ok=True)
        sidecar.write_text(json.dumps({"id": "bogus"}), encoding="utf-8")
        _cat_dir, ucs, _subcats = nts.collect_ssot_categories()
        assert ucs == {}

    def test_skips_uc_with_partial_id(self, fake_repo: pathlib.Path) -> None:
        sidecar = fake_repo / "content" / "cat-01-test-cat" / "UC-partial.json"
        sidecar.parent.mkdir(parents=True, exist_ok=True)
        sidecar.write_text(json.dumps({"id": "1.1"}), encoding="utf-8")
        _cat_dir, ucs, _subcats = nts.collect_ssot_categories()
        assert ucs == {}

    def test_skips_cat_00(self, fake_repo: pathlib.Path) -> None:
        cat_dir = fake_repo / "content" / "cat-00-stub"
        cat_dir.mkdir()
        cat_dir_map, ucs, subcats = nts.collect_ssot_categories()
        assert 0 not in cat_dir_map
        assert ucs == {}
        assert subcats == {}

    def test_skips_non_cat_dirs(self, fake_repo: pathlib.Path) -> None:
        (fake_repo / "content" / "not-cat-dir").mkdir()
        (fake_repo / "content" / "stuff").mkdir()
        cat_dir, _ucs, _subcats = nts.collect_ssot_categories()
        assert cat_dir == {}

    def test_skips_unpadded_cat_dirs(self, fake_repo: pathlib.Path) -> None:
        # cat-1- (single digit) doesn't match the zero-padded regex.
        (fake_repo / "content" / "cat-1-unpadded").mkdir()
        cat_dir, _ucs, _subcats = nts.collect_ssot_categories()
        assert cat_dir == {}

    def test_skips_non_directory_entries(self, fake_repo: pathlib.Path) -> None:
        (fake_repo / "content" / "cat-01-stray.txt").write_text("stray", encoding="utf-8")
        cat_dir, _ucs, _subcats = nts.collect_ssot_categories()
        assert cat_dir == {}


# ---------------------------------------------------------------------------
# main() CLI
# ---------------------------------------------------------------------------


_BASIC_JS = """\
window.NON_TECHNICAL = {
    "1": {
        outcomes: ["Cat 1 outcome"],
        areas: [
            {name: "Area", description: "Desc", ucs: [
                {id: "1.1.1", why: "Why"}
            ]}
        ]
    }
};
"""


class TestMain:
    def test_clean_run_returns_zero(
        self,
        make_uc: MakeUC,
        make_js: MakeJS,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        make_uc(1, "1.1.1", {})
        make_js(_BASIC_JS)
        rc = nts.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "No issues found." in out

    def test_summary_includes_counts(
        self,
        make_uc: MakeUC,
        make_js: MakeJS,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        make_uc(1, "1.1.1", {})
        make_js(_BASIC_JS)
        nts.main([])
        out = capsys.readouterr().out
        assert "JS categories (numeric keys): 1" in out
        assert "JS UC id references: 1" in out
        assert "SSOT category folders (cat-NN-*): 1" in out
        assert "SSOT UC sidecars total (unique): 1" in out

    def test_issue_a_uc_in_js_missing_in_ssot(
        self,
        make_js: MakeJS,
        capsys: pytest.CaptureFixture[str],
        fake_repo: pathlib.Path,
    ) -> None:
        # JS references UC 1.1.1 but no SSOT sidecar exists.
        # Provide an SSOT folder so issue (b) doesn't dominate.
        (fake_repo / "content" / "cat-01-test-cat").mkdir()
        make_js(_BASIC_JS)
        rc = nts.main([])
        out = capsys.readouterr().out
        assert rc == 0  # The audit never fails the build with non-zero.
        assert "(a) JS references UC id '1.1.1'" in out

    def test_issue_b_content_folder_missing_in_js(
        self,
        make_uc: MakeUC,
        make_js: MakeJS,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Make a cat-02 folder with a UC, but JS only has "1".
        make_uc(2, "2.1.1", {})
        make_js(_BASIC_JS)
        rc = nts.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "(b) Content folder cat-02-test-cat" in out

    def test_issue_c_subcategory_missing_in_js(
        self,
        make_uc: MakeUC,
        make_js: MakeJS,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # SSOT has 1.2.1 but JS only references 1.1.1.
        make_uc(1, "1.1.1", {})
        make_uc(1, "1.2.1", {})
        make_js(_BASIC_JS)
        rc = nts.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "(c) JSON SSOT has subcategory 1.2" in out

    def test_issue_d_js_category_without_content_folder(
        self,
        make_js: MakeJS,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # JS has "5" but no content/cat-05-*/ folder.
        js = 'window.NON_TECHNICAL = { "5": { areas: [{ ucs: [{id: "5.1.1"}] }] } };'
        make_js(js)
        rc = nts.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert '(d) non-technical-view.js has category "5"' in out

    def test_non_numeric_js_keys_ignored_by_audit(
        self,
        make_uc: MakeUC,
        make_js: MakeJS,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # JS has "_meta" which isn't a numeric category.
        js = (
            "window.NON_TECHNICAL = { "
            '"_meta": { foo: "bar" }, '
            '"1": { areas: [{ ucs: [{id: "1.1.1"}] }] } '
            "};"
        )
        make_uc(1, "1.1.1", {})
        make_js(js)
        rc = nts.main([])
        out = capsys.readouterr().out
        assert rc == 0
        # Only the numeric "1" should be counted.
        assert "JS categories (numeric keys): 1" in out

    def test_help_flag(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as exc:
            nts.main(["--help"])
        assert exc.value.code == 0
        out = capsys.readouterr().out
        assert "non-technical-view.js" in out

    def test_extra_issue_when_block_extraction_disagrees(
        self,
        make_js: MakeJS,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Malformed JS where the outer object is unclosed: the
        # ``extract_top_level_string_keys`` parser finds ``"1"`` as a
        # key, but ``parse_js_category_blocks`` never encounters the
        # matching ``}`` so no block is recorded. The "(extra)" issue
        # fires.
        js = 'window.NON_TECHNICAL = { "1": { id: "1.1.1"'  # unclosed
        make_js(js)
        rc = nts.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "(extra) Category key '1' listed but block not extracted" in out

    def test_handles_combined_issues(
        self,
        make_uc: MakeUC,
        make_js: MakeJS,
        capsys: pytest.CaptureFixture[str],
        fake_repo: pathlib.Path,
    ) -> None:
        # All four issue types active:
        # - SSOT has cat-02 (b)
        # - JS has "5" (d)
        # - JS references "1.1.99" not in SSOT (a)
        # - SSOT has 1.2 not in JS (c)
        make_uc(1, "1.1.1", {})
        make_uc(1, "1.2.1", {})
        make_uc(2, "2.1.1", {})
        js = (
            "window.NON_TECHNICAL = { "
            '"1": { areas: [{ ucs: [{id: "1.1.1"}, {id: "1.1.99"}] }] }, '
            '"5": { areas: [] } '
            "};"
        )
        make_js(js)
        rc = nts.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "(a)" in out
        assert "(b)" in out
        assert "(c)" in out
        assert "(d)" in out
        assert "Issues found:" in out
