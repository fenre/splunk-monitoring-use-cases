"""Unit tests for ``splunk_uc.audits.repo_consistency``.

P16 wave O: lifts ``src/splunk_uc/audits/repo_consistency.py`` from
7.19% to ≥95% combined coverage. Pins every documented contract of the
INDEX.md / CAT_GROUPS / SPLUNK_APPS cross-source consistency audit.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

from splunk_uc.audits import repo_consistency as rc

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------


class TestConstants:
    def test_repo_root_points_at_real_repo(self) -> None:
        assert os.path.isdir(rc.REPO_ROOT)
        assert os.path.isdir(os.path.join(rc.REPO_ROOT, "content"))

    def test_index_paths_resolve(self) -> None:
        assert rc.CONTENT_DIR == os.path.join(rc.REPO_ROOT, "content")
        assert rc.INDEX_PATH == os.path.join(rc.REPO_ROOT, "content", "INDEX.md")
        assert rc.INDEX_HTML == os.path.join(rc.REPO_ROOT, "index.html")

    def test_expected_cats_1_through_23(self) -> None:
        assert rc.EXPECTED_CATS == set(range(1, 24))

    def test_required_splunk_app_keys(self) -> None:
        assert rc.REQUIRED_SPLUNK_APP_KEYS == ("name", "id", "url", "tas", "desc")

    def test_regex_patterns_compile(self) -> None:
        assert rc.RE_CAT_HEADER.match("## 5. Identity & Access").group(1) == "5"
        assert rc.RE_CAT_HEADER.match("## 5. Identity & Access").group(2) == "Identity & Access"
        assert rc.RE_ICON.match("- **Icon:** shield").group(1) == "shield"
        assert rc.RE_STARTER.match("- UC-1.1.1 · Some Title (crawl)").group(1) == "1.1.1"


# ---------------------------------------------------------------------------
# parse_si_paths_keys
# ---------------------------------------------------------------------------


class TestParseSiPathsKeys:
    def test_var_si_paths_assignment(self) -> None:
        # The regex requires unquoted keys (matches `\w+:` after leading whitespace).
        html = """
var SI_PATHS = {
    shield: "M0 0L10 10",
    lock: "M0 0L20 20",
};
"""
        keys = rc.parse_si_paths_keys(html)
        assert keys == {"shield", "lock"}

    def test_var_si_paths_without_space(self) -> None:
        html = """
var SI_PATHS={
    shield: "M0 0L10 10",
};
"""
        keys = rc.parse_si_paths_keys(html)
        assert keys == {"shield"}

    def test_var_si_assignment(self) -> None:
        html = """
var SI = {
    shield: "path",
};
"""
        keys = rc.parse_si_paths_keys(html)
        assert keys == {"shield"}

    def test_var_si_without_space(self) -> None:
        html = """
var SI={
    shield: "path",
};
"""
        keys = rc.parse_si_paths_keys(html)
        assert keys == {"shield"}

    def test_missing_prefix_returns_empty(self) -> None:
        html = "// no SI block here"
        assert rc.parse_si_paths_keys(html) == set()

    def test_handles_single_quoted_values(self) -> None:
        html = """
var SI_PATHS = {
    foo: 'M0 0L10 10',
    bar: 'M0 0L20 20',
};
"""
        keys = rc.parse_si_paths_keys(html)
        assert keys == {"foo", "bar"}

    def test_nested_braces_in_value(self) -> None:
        # The depth tracker walks brace pairs, so balanced inner braces
        # should not terminate parsing prematurely.
        html = """
var SI_PATHS = {
    outer: 'M0 0L{10}10',
    inner: 'M0',
};
"""
        keys = rc.parse_si_paths_keys(html)
        # The regex hunts for `key: 'value'`; nested {} are inside strings.
        assert "outer" in keys
        assert "inner" in keys

    def test_unterminated_block_returns_empty(self) -> None:
        # No closing brace before EOF — depth never returns to zero.
        html = "var SI_PATHS = {"
        assert rc.parse_si_paths_keys(html) == set()


# ---------------------------------------------------------------------------
# parse_index
# ---------------------------------------------------------------------------


def _write_index(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


class TestParseIndex:
    def test_single_category_with_icon_and_starter(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        idx = tmp_path / "INDEX.md"
        _write_index(
            idx,
            "## 1. IAM\n"
            "- **Icon:** shield\n"
            "- **Quick Start:**\n"
            "- UC-1.1.1 · Login monitoring (crawl)\n"
            "- UC-1.1.2 · MFA monitoring (walk)\n",
        )
        monkeypatch.setattr(rc, "INDEX_PATH", str(idx))
        cats = rc.parse_index()
        assert len(cats) == 1
        assert cats[0]["num"] == "1"
        assert cats[0]["name"] == "IAM"
        assert cats[0]["icon"] == "shield"
        assert cats[0]["starters"] == ["1.1.1", "1.1.2"]

    def test_empty_index_returns_empty(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        idx = tmp_path / "INDEX.md"
        _write_index(idx, "")
        monkeypatch.setattr(rc, "INDEX_PATH", str(idx))
        assert rc.parse_index() == []

    def test_non_header_lines_before_first_header_skipped(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        idx = tmp_path / "INDEX.md"
        _write_index(
            idx,
            "# Big title\n"
            "Random preamble paragraph.\n"
            "- **Icon:** shield  (ignored, no category yet)\n"
            "## 1. IAM\n"
            "- **Icon:** shield\n",
        )
        monkeypatch.setattr(rc, "INDEX_PATH", str(idx))
        cats = rc.parse_index()
        assert len(cats) == 1
        assert cats[0]["icon"] == "shield"

    def test_multiple_categories(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        idx = tmp_path / "INDEX.md"
        _write_index(
            idx,
            "## 1. IAM\n- **Icon:** shield\n## 2. Endpoint\n- **Icon:** laptop\n",
        )
        monkeypatch.setattr(rc, "INDEX_PATH", str(idx))
        cats = rc.parse_index()
        assert [c["num"] for c in cats] == ["1", "2"]

    def test_starter_section_terminated_by_blank_line(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        idx = tmp_path / "INDEX.md"
        _write_index(
            idx,
            "## 1. IAM\n"
            "- **Quick Start:**\n"
            "- UC-1.1.1 · Login (crawl)\n"
            "\n"
            "Some paragraph that terminates the starters section.\n",
        )
        monkeypatch.setattr(rc, "INDEX_PATH", str(idx))
        cats = rc.parse_index()
        assert cats[0]["starters"] == ["1.1.1"]

    def test_starter_section_continues_through_blank_line(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Blank lines themselves do not terminate the starter section (the
        # terminator is a non-empty non-list line).
        idx = tmp_path / "INDEX.md"
        _write_index(
            idx,
            "## 1. IAM\n"
            "- **Quick Start:**\n"
            "- UC-1.1.1 · Login (crawl)\n"
            "\n"
            "- UC-1.1.2 · MFA (walk)\n",
        )
        monkeypatch.setattr(rc, "INDEX_PATH", str(idx))
        cats = rc.parse_index()
        assert cats[0]["starters"] == ["1.1.1", "1.1.2"]

    def test_starter_with_optional_status(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        idx = tmp_path / "INDEX.md"
        _write_index(
            idx,
            "## 1. IAM\n- **Quick Start:**\n- UC-1.1.1 · Login (crawl, production)\n",
        )
        monkeypatch.setattr(rc, "INDEX_PATH", str(idx))
        cats = rc.parse_index()
        assert cats[0]["starters"] == ["1.1.1"]

    def test_unmatched_line_inside_category_before_starters_skipped(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Pins the false-branch of ``if in_starters:`` (line 94→76 in
        ``parse_index``): when a non-empty line that doesn't match any
        section marker appears after ``## N.`` and before
        ``- **Quick Start:**``, ``in_starters`` is still False, so the
        loop simply continues to the next line."""
        idx = tmp_path / "INDEX.md"
        _write_index(
            idx,
            "## 1. IAM\n"
            "Some descriptive paragraph belonging to category 1.\n"
            "- **Icon:** shield\n"
            "- **Quick Start:**\n"
            "- UC-1.1.1 \u00b7 Login (crawl)\n",
        )
        monkeypatch.setattr(rc, "INDEX_PATH", str(idx))
        cats = rc.parse_index()
        assert len(cats) == 1
        assert cats[0]["icon"] == "shield"
        assert cats[0]["starters"] == ["1.1.1"]


# ---------------------------------------------------------------------------
# Module-import side effect: ``sys.path`` membership of ``tools/``
# ---------------------------------------------------------------------------


class TestToolsDirSysPathBootstrap:
    def test_reimport_when_tools_dir_already_in_sys_path_is_a_noop(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Pins the false-branch of ``if _TOOLS_DIR.is_dir() and
        str(_TOOLS_DIR) not in sys.path`` (line 37→40 in
        ``repo_consistency``): once the module has been imported during
        the test session, ``_TOOLS_DIR`` is already in ``sys.path``, so
        reloading the module must skip the ``sys.path.insert`` and fall
        through to the next module-level statement (the regex
        compilations starting at line 40)."""
        import importlib
        import sys

        tools_dir = str(Path(rc.REPO_ROOT) / "tools")
        assert tools_dir in sys.path, (
            "preconditioned to pin the False branch: the module's "
            "initial import already populated sys.path"
        )
        path_before = list(sys.path)
        reloaded = importlib.reload(rc)
        assert sys.path.count(tools_dir) == path_before.count(tools_dir), (
            "reload must not append a duplicate tools_dir entry"
        )
        assert reloaded.RE_CAT_HEADER is not None
        assert reloaded.REPO_ROOT == rc.REPO_ROOT

    def test_reimport_when_tools_dir_missing_re_inserts(self) -> None:
        """Pins the True branch of the module-level guard (line 37 → line
        38): when ``_TOOLS_DIR`` is a directory but absent from
        ``sys.path`` at import time, the module must invoke
        ``sys.path.insert(0, str(_TOOLS_DIR))`` so that any downstream
        ``import`` of a sibling ``tools/`` helper resolves.

        Like the matching compliance-mappings test, this branch is taken
        on a cold interpreter start but not by any prior test observation
        (every test runs hot, with ``tools/`` already present). To pin the
        True arm hermetically we remove the entry, reload the module, and
        re-assert insertion happened. The ``try/finally`` restores the
        pre-test ``sys.path`` so this test is order-independent. The
        outer ``and`` short-circuit also requires ``_TOOLS_DIR.is_dir()``
        to be True — guaranteed by the on-disk ``tools/`` directory at
        the repo root."""
        import importlib
        import sys

        tools_dir = str(Path(rc.REPO_ROOT) / "tools")
        original = list(sys.path)
        try:
            while tools_dir in sys.path:
                sys.path.remove(tools_dir)
            assert tools_dir not in sys.path
            reloaded = importlib.reload(rc)
            assert tools_dir in sys.path, (
                "module-level guard must re-insert _TOOLS_DIR when it is "
                "absent from sys.path at import time"
            )
            assert reloaded.RE_CAT_HEADER is not None
        finally:
            sys.path[:] = original


# ---------------------------------------------------------------------------
# extract_build_assignments
# ---------------------------------------------------------------------------


class TestExtractBuildAssignments:
    def test_returns_dict_and_list(self) -> None:
        # This depends on the real tools/build/enrichment.py — sanity check.
        cat_groups, splunk_apps = rc.extract_build_assignments()
        assert isinstance(cat_groups, dict)
        assert isinstance(splunk_apps, list)

    def test_cat_groups_contains_all_expected_cats(self) -> None:
        cat_groups, _ = rc.extract_build_assignments()
        all_cats: set[int] = set()
        for ids in cat_groups.values():
            all_cats.update(ids)
        # Every expected category should appear in some group.
        assert rc.EXPECTED_CATS.issubset(all_cats)

    def test_cat_groups_not_dict_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Inject a stub enrichment module with CAT_GROUPS as the wrong type.
        import sys
        import types

        stub = types.ModuleType("build.enrichment")
        stub.CAT_GROUPS = ["not", "a", "dict"]  # type: ignore[attr-defined]
        stub.SPLUNK_APPS = []  # type: ignore[attr-defined]
        # Inject the parent "build" package too so the dotted import works.
        parent = types.ModuleType("build")
        monkeypatch.setitem(sys.modules, "build", parent)
        monkeypatch.setitem(sys.modules, "build.enrichment", stub)
        with pytest.raises(RuntimeError, match="CAT_GROUPS is not a dict"):
            rc.extract_build_assignments()

    def test_splunk_apps_not_list_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import sys
        import types

        stub = types.ModuleType("build.enrichment")
        stub.CAT_GROUPS = {}  # type: ignore[attr-defined]
        stub.SPLUNK_APPS = "not a list"  # type: ignore[attr-defined]
        parent = types.ModuleType("build")
        monkeypatch.setitem(sys.modules, "build", parent)
        monkeypatch.setitem(sys.modules, "build.enrichment", stub)
        with pytest.raises(RuntimeError, match="SPLUNK_APPS is not a list"):
            rc.extract_build_assignments()


# ---------------------------------------------------------------------------
# main() — orchestrator
# ---------------------------------------------------------------------------


@pytest.fixture
def isolated_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Build a minimal-but-valid repo skeleton with all expected categories."""
    content = tmp_path / "content"
    content.mkdir()
    # Create all 23 expected category folders.
    for n in range(1, 24):
        (content / f"cat-{n:02d}-test").mkdir()

    index_html = tmp_path / "index.html"
    si_paths_block = "var SI_PATHS = {\n"
    for icon in ("shield", "laptop", "cloud", "lock", "key"):
        si_paths_block += f'    {icon}: "M0 0L10 10",\n'
    si_paths_block += "};\n"
    index_html.write_text(si_paths_block, encoding="utf-8")

    index_md = content / "INDEX.md"
    md_lines = []
    for n in range(1, 24):
        md_lines.append(f"## {n}. Category {n}")
        md_lines.append("- **Icon:** shield")
    index_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    monkeypatch.setattr(rc, "REPO_ROOT", str(tmp_path))
    monkeypatch.setattr(rc, "CONTENT_DIR", str(content))
    monkeypatch.setattr(rc, "INDEX_PATH", str(index_md))
    monkeypatch.setattr(rc, "INDEX_HTML", str(index_html))
    return tmp_path


class TestMainHappyPath:
    def test_returns_zero_when_no_issues(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Stub extract_build_assignments to return valid registries
        # covering every expected cat.
        def fake_extract() -> tuple[dict[str, list[int]], list[Any]]:
            return {"core": list(range(1, 24))}, [
                {
                    "name": "Splunk ES",
                    "id": "263",
                    "url": "https://splunkbase.splunk.com/app/263",
                    "tas": [],
                    "desc": "Enterprise Security",
                }
            ]

        monkeypatch.setattr(rc, "extract_build_assignments", fake_extract)
        rc_code = rc.main([])
        assert rc_code == 0
        out = capsys.readouterr().out
        assert "No issues found." in out


class TestMainFailureModes:
    def test_fatal_missing_index(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(rc, "INDEX_PATH", str(isolated_repo / "DOES_NOT_EXIST.md"))
        rc_code = rc.main([])
        assert rc_code == 1
        out = capsys.readouterr().out
        assert "FATAL: Missing" in out

    def test_unparseable_si_paths_warns(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Wipe SI_PATHS block from index.html → warning fires + audit
        # treats the WARN as an issue and returns rc=2 (the audit makes
        # no distinction between warnings and errors in the exit code).
        (isolated_repo / "index.html").write_text("// no SI block\n", encoding="utf-8")

        def fake_extract() -> tuple[dict[str, list[int]], list[Any]]:
            return {"core": list(range(1, 24))}, [
                {"name": "X", "id": "1", "url": "u", "tas": [], "desc": "d"}
            ]

        monkeypatch.setattr(rc, "extract_build_assignments", fake_extract)
        rc_code = rc.main([])
        out = capsys.readouterr().out
        assert "icon checks skipped" in out
        # The WARN message is treated as an issue → rc=2.
        assert rc_code == 2

    def test_duplicate_category_header_flagged(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Append a duplicate category 1 header
        md = (isolated_repo / "content" / "INDEX.md").read_text(encoding="utf-8")
        md += "## 1. Duplicate IAM\n"
        (isolated_repo / "content" / "INDEX.md").write_text(md, encoding="utf-8")

        def fake_extract() -> tuple[dict[str, list[int]], list[Any]]:
            return {"core": list(range(1, 24))}, []

        monkeypatch.setattr(rc, "extract_build_assignments", fake_extract)
        rc_code = rc.main([])
        out = capsys.readouterr().out
        assert "Duplicate category header" in out
        assert rc_code == 2

    def test_missing_category_header_flagged(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Write an INDEX.md missing category 5
        md_lines = []
        for n in range(1, 24):
            if n == 5:
                continue
            md_lines.append(f"## {n}. Category {n}")
            md_lines.append("- **Icon:** shield")
        (isolated_repo / "content" / "INDEX.md").write_text(
            "\n".join(md_lines) + "\n", encoding="utf-8"
        )

        def fake_extract() -> tuple[dict[str, list[int]], list[Any]]:
            return {"core": list(range(1, 24))}, []

        monkeypatch.setattr(rc, "extract_build_assignments", fake_extract)
        rc_code = rc.main([])
        out = capsys.readouterr().out
        assert "Missing category header for 5" in out
        assert rc_code == 2

    def test_unexpected_category_number_flagged(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        md = (isolated_repo / "content" / "INDEX.md").read_text(encoding="utf-8")
        md += "## 99. Bogus Category\n- **Icon:** shield\n"
        (isolated_repo / "content" / "INDEX.md").write_text(md, encoding="utf-8")

        def fake_extract() -> tuple[dict[str, list[int]], list[Any]]:
            return {"core": list(range(1, 24))}, []

        monkeypatch.setattr(rc, "extract_build_assignments", fake_extract)
        rc_code = rc.main([])
        out = capsys.readouterr().out
        assert "Unexpected category number 99" in out
        assert rc_code == 2

    def test_missing_category_folder_flagged(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Remove category 1's folder.
        import shutil

        shutil.rmtree(isolated_repo / "content" / "cat-01-test")

        def fake_extract() -> tuple[dict[str, list[int]], list[Any]]:
            return {"core": list(range(1, 24))}, []

        monkeypatch.setattr(rc, "extract_build_assignments", fake_extract)
        rc_code = rc.main([])
        out = capsys.readouterr().out
        assert "no matching folder content/cat-01-" in out
        assert rc_code == 2

    def test_multiple_category_folders_flagged(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        (isolated_repo / "content" / "cat-01-duplicate").mkdir()

        def fake_extract() -> tuple[dict[str, list[int]], list[Any]]:
            return {"core": list(range(1, 24))}, []

        monkeypatch.setattr(rc, "extract_build_assignments", fake_extract)
        rc_code = rc.main([])
        out = capsys.readouterr().out
        assert "multiple cat-01-* folders" in out
        assert rc_code == 2

    def test_unknown_icon_flagged(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        md = (isolated_repo / "content" / "INDEX.md").read_text(encoding="utf-8")
        md = md.replace("- **Icon:** shield", "- **Icon:** bogus_icon", 1)
        (isolated_repo / "content" / "INDEX.md").write_text(md, encoding="utf-8")

        def fake_extract() -> tuple[dict[str, list[int]], list[Any]]:
            return {"core": list(range(1, 24))}, []

        monkeypatch.setattr(rc, "extract_build_assignments", fake_extract)
        rc_code = rc.main([])
        out = capsys.readouterr().out
        assert "is not a key in index.html SI_PATHS" in out
        assert rc_code == 2

    def test_quick_start_uc_not_in_folder_flagged(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        md = (isolated_repo / "content" / "INDEX.md").read_text(encoding="utf-8")
        md = md.replace(
            "## 1. Category 1",
            "## 1. Category 1\n- **Quick Start:**\n- UC-1.1.1 · Missing UC (crawl)",
            1,
        )
        (isolated_repo / "content" / "INDEX.md").write_text(md, encoding="utf-8")

        def fake_extract() -> tuple[dict[str, list[int]], list[Any]]:
            return {"core": list(range(1, 24))}, []

        monkeypatch.setattr(rc, "extract_build_assignments", fake_extract)
        rc_code = rc.main([])
        out = capsys.readouterr().out
        assert "Quick Start UC UC-1.1.1" in out
        assert "not found" in out
        assert rc_code == 2

    def test_quick_start_uc_present_no_flag(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Add a starter pointing to a UC file we create.
        (isolated_repo / "content" / "cat-01-test" / "UC-1.1.1.json").write_text(
            "{}", encoding="utf-8"
        )
        md = (isolated_repo / "content" / "INDEX.md").read_text(encoding="utf-8")
        md = md.replace(
            "## 1. Category 1",
            "## 1. Category 1\n- **Quick Start:**\n- UC-1.1.1 · Present UC (crawl)",
            1,
        )
        (isolated_repo / "content" / "INDEX.md").write_text(md, encoding="utf-8")

        def fake_extract() -> tuple[dict[str, list[int]], list[Any]]:
            return {"core": list(range(1, 24))}, []

        monkeypatch.setattr(rc, "extract_build_assignments", fake_extract)
        rc_code = rc.main([])
        out = capsys.readouterr().out
        assert "Quick Start UC UC-1.1.1" not in out
        assert rc_code == 0

    def test_cat_groups_import_failure_flagged(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def fake_extract() -> tuple[dict[str, list[int]], list[Any]]:
            raise RuntimeError("synthetic import error")

        monkeypatch.setattr(rc, "extract_build_assignments", fake_extract)
        rc_code = rc.main([])
        out = capsys.readouterr().out
        assert "Failed to import CAT_GROUPS" in out
        assert rc_code == 2

    def test_cat_groups_missing_category_flagged(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def fake_extract() -> tuple[dict[str, list[int]], list[Any]]:
            # Cover everything but category 5
            return {"core": [n for n in range(1, 24) if n != 5]}, []

        monkeypatch.setattr(rc, "extract_build_assignments", fake_extract)
        rc_code = rc.main([])
        out = capsys.readouterr().out
        assert "CAT_GROUPS: Category 5 is not in any group" in out
        assert rc_code == 2

    def test_cat_groups_duplicate_category_flagged(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def fake_extract() -> tuple[dict[str, list[int]], list[Any]]:
            return {"core": list(range(1, 24)), "extra": [5, 5]}, []

        monkeypatch.setattr(rc, "extract_build_assignments", fake_extract)
        rc_code = rc.main([])
        out = capsys.readouterr().out
        assert "Category 5 appears" in out
        assert "must be exactly once" in out
        assert rc_code == 2

    def test_cat_groups_unexpected_id_flagged(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def fake_extract() -> tuple[dict[str, list[int]], list[Any]]:
            return {"core": [*list(range(1, 24)), 99]}, []

        monkeypatch.setattr(rc, "extract_build_assignments", fake_extract)
        rc_code = rc.main([])
        out = capsys.readouterr().out
        assert "Unexpected category id 99" in out
        assert "contains invalid category 99" in out
        assert rc_code == 2

    def test_cat_folder_bad_name_flagged(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # A folder starting with "cat-" but not matching cat-NN-*
        (isolated_repo / "content" / "cat-bad-name").mkdir()

        def fake_extract() -> tuple[dict[str, list[int]], list[Any]]:
            return {"core": list(range(1, 24))}, []

        monkeypatch.setattr(rc, "extract_build_assignments", fake_extract)
        rc_code = rc.main([])
        out = capsys.readouterr().out
        assert "Unexpected name pattern" in out
        assert rc_code == 2

    def test_cat_folder_not_in_cat_groups_union(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def fake_extract() -> tuple[dict[str, list[int]], list[Any]]:
            # Cover everything but cat 5; but the cat-05 folder still exists on disk.
            return {"core": [n for n in range(1, 24) if n != 5]}, []

        monkeypatch.setattr(rc, "extract_build_assignments", fake_extract)
        rc.main([])
        out = capsys.readouterr().out
        assert "cat-05-test implies category 5" in out
        assert "not in CAT_GROUPS union" in out

    def test_uc_file_with_invalid_category_id(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Place a UC file in cat-01-test with a UC id whose category is 99 (out of range).
        (isolated_repo / "content" / "cat-01-test" / "UC-99.1.1.json").write_text(
            "{}", encoding="utf-8"
        )

        def fake_extract() -> tuple[dict[str, list[int]], list[Any]]:
            return {"core": list(range(1, 24))}, []

        monkeypatch.setattr(rc, "extract_build_assignments", fake_extract)
        rc_code = rc.main([])
        out = capsys.readouterr().out
        assert "UC-99.1.1 category 99 not in 1-23" in out
        assert rc_code == 2

    def test_uc_file_with_category_not_in_cat_groups(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        (isolated_repo / "content" / "cat-01-test" / "UC-5.1.1.json").write_text(
            "{}", encoding="utf-8"
        )

        def fake_extract() -> tuple[dict[str, list[int]], list[Any]]:
            return {"core": [n for n in range(1, 24) if n != 5]}, []

        monkeypatch.setattr(rc, "extract_build_assignments", fake_extract)
        rc_code = rc.main([])
        out = capsys.readouterr().out
        assert "UC-5.1.1 category 5 not in CAT_GROUPS" in out
        assert rc_code == 2

    def test_uc_file_with_malformed_id_skipped(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # UC file whose name doesn't match X.Y.Z — should be silently skipped
        # by the second deep-walk loop in main().
        (isolated_repo / "content" / "cat-01-test" / "UC-bad-id.json").write_text(
            "{}", encoding="utf-8"
        )

        def fake_extract() -> tuple[dict[str, list[int]], list[Any]]:
            return {"core": list(range(1, 24))}, []

        monkeypatch.setattr(rc, "extract_build_assignments", fake_extract)
        rc_code = rc.main([])
        out = capsys.readouterr().out
        assert "UC-bad-id" not in out  # not flagged
        assert rc_code == 0

    def test_non_uc_file_in_cat_folder_skipped(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # README.md and other non-UC files in cat-NN-*/ folders are silently
        # skipped by the deep walker (exercises line 245 — the
        # `continue` for files not matching the UC-*.json shape).
        (isolated_repo / "content" / "cat-01-test" / "README.md").write_text(
            "doc", encoding="utf-8"
        )

        def fake_extract() -> tuple[dict[str, list[int]], list[Any]]:
            return {"core": list(range(1, 24))}, []

        monkeypatch.setattr(rc, "extract_build_assignments", fake_extract)
        rc_code = rc.main([])
        out = capsys.readouterr().out
        assert "README.md" not in out
        assert rc_code == 0

    def test_uc_with_non_three_part_id_skipped(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Two-part id (e.g. "UC-1.2.json") fails the X.Y.Z regex and is
        # silently skipped by the deep walker (exercises the `continue`
        # branch at line 245 / `if not mm:`).
        (isolated_repo / "content" / "cat-01-test" / "UC-1.2.json").write_text(
            "{}", encoding="utf-8"
        )

        def fake_extract() -> tuple[dict[str, list[int]], list[Any]]:
            return {"core": list(range(1, 24))}, []

        monkeypatch.setattr(rc, "extract_build_assignments", fake_extract)
        rc_code = rc.main([])
        out = capsys.readouterr().out
        assert "UC-1.2" not in out
        assert rc_code == 0

    def test_splunk_app_missing_required_field(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def fake_extract() -> tuple[dict[str, list[int]], list[Any]]:
            return {"core": list(range(1, 24))}, [
                {"name": "Incomplete app", "id": "999"}  # missing url/tas/desc
            ]

        monkeypatch.setattr(rc, "extract_build_assignments", fake_extract)
        rc_code = rc.main([])
        out = capsys.readouterr().out
        assert "missing required field" in out
        assert rc_code == 2

    def test_splunk_app_not_a_dict(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def fake_extract() -> tuple[dict[str, list[int]], list[Any]]:
            return {"core": list(range(1, 24))}, ["not a dict"]

        monkeypatch.setattr(rc, "extract_build_assignments", fake_extract)
        rc_code = rc.main([])
        out = capsys.readouterr().out
        assert "entry is not a dict" in out
        assert rc_code == 2

    def test_splunk_apps_duplicate_id(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def fake_extract() -> tuple[dict[str, list[int]], list[Any]]:
            return {"core": list(range(1, 24))}, [
                {
                    "name": "A",
                    "id": "100",
                    "url": "u",
                    "tas": [],
                    "desc": "d",
                },
                {
                    "name": "B",
                    "id": "100",
                    "url": "u",
                    "tas": [],
                    "desc": "d",
                },
            ]

        monkeypatch.setattr(rc, "extract_build_assignments", fake_extract)
        rc_code = rc.main([])
        out = capsys.readouterr().out
        assert "duplicate app id 100" in out
        assert rc_code == 2

    def test_splunk_app_without_id_does_not_dedupe(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def fake_extract() -> tuple[dict[str, list[int]], list[Any]]:
            return {"core": list(range(1, 24))}, [
                {"name": "No-id A", "url": "u", "tas": [], "desc": "d"},
                {"name": "No-id B", "url": "u", "tas": [], "desc": "d"},
            ]

        monkeypatch.setattr(rc, "extract_build_assignments", fake_extract)
        rc.main([])
        out = capsys.readouterr().out
        # Should flag missing id field but NOT report a duplicate.
        assert "missing required field" in out
        assert "duplicate app id" not in out


# ---------------------------------------------------------------------------
# Argparse / script entry
# ---------------------------------------------------------------------------


class TestArgparse:
    def test_help_exits_zero(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as exc:
            rc.main(["--help"])
        assert exc.value.code == 0
        out = capsys.readouterr().out
        assert "usage:" in out.lower()
