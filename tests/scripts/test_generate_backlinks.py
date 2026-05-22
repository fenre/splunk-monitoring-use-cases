"""Unit-level coverage for ``scripts/generate_backlinks.py``.

This script powers the "What links here" wiki view at
``docs/backlinks.md``. It is wired into the Makefile in three
places:

* ``backlinks`` target (write mode)
* ``sync-generated`` (umbrella write mode)
* ``sync-generated-check`` (``--check`` drift-guard gate, also
  run as a CI step)

A regression in this script would either (a) silently bit-rot
``docs/backlinks.md`` or (b) FAIL the drift-guard gate when a
documentation change touches a backlink target. Both routes
catch on the same code path, so we lock it tightly here.

What this suite locks
---------------------

* ``collect_md_files`` — finds ``docs/**/*.md`` recursively;
  appends each extra file in the hard-coded list when it exists
  on disk (silently skips missing entries); returns a
  deduplicated, sorted, resolved-path list.
* ``to_repo_rel`` — strips REPO prefix; normalises OS separator
  to forward slash.
* ``collect_inbound`` — happy path with cross-references; strips
  the auto-generated sources footer so its own outbound links
  don't recurse; strips fenced code blocks and inline code so
  example snippets containing ``[label](url.md)`` syntax don't
  pollute the graph; skips non-``.md`` targets; skips
  ``http://``, ``mailto:``, ``file:``, and protocol-relative
  ``//`` URLs; skips targets outside REPO (``ValueError`` from
  ``relative_to``); skips targets not in the node set; skips
  self-references; deduplicates ``(src, tgt)`` pairs within a
  single source.
* ``render`` — emits the report header; emits ``No inbound links
  yet.`` for targets with zero inbound; computes
  ``pages_with_inbound`` and ``total_edges``; deduplicates by
  source within a single target; computes relative paths from
  the ``docs/`` directory; handles the cross-prefix ``ValueError``
  arm of ``os.path.relpath`` (different drive letters on win32,
  which we synthesise here by monkey-patching).
* ``main`` — write mode writes the rendered output; ``--check``
  mode returns 0 on match, 1 on stale, 1 on missing.
* ``__main__`` guard — script-entry invocation.

Run
---

``pytest tests/scripts/test_generate_backlinks.py``

Coverage check
--------------

``coverage run --branch --source=scripts.generate_backlinks \\
    -m pytest tests/scripts/test_generate_backlinks.py && \\
  coverage report --include='scripts/generate_backlinks.py' \\
    --show-missing``
"""
from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path

import pytest

import scripts.generate_backlinks as gb

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def isolated_repo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    """Redirect ``REPO`` and ``OUTPUT`` to a tmp tree.

    The script reads ``REPO`` and ``OUTPUT`` as module-level
    constants computed at import time. We patch them after the
    module has been imported so every function in the script
    sees the redirected paths."""
    repo = tmp_path / "repo"
    (repo / "docs").mkdir(parents=True)
    monkeypatch.setattr(gb, "REPO", repo)
    monkeypatch.setattr(gb, "OUTPUT", repo / "docs" / "backlinks.md")
    return repo


def _write(p: Path, body: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")


# ---------------------------------------------------------------------------
# collect_md_files
# ---------------------------------------------------------------------------


class TestCollectMdFiles:
    def test_recursive_glob_under_docs(
        self, isolated_repo: Path
    ) -> None:
        _write(isolated_repo / "docs" / "a.md", "# A")
        _write(isolated_repo / "docs" / "sub" / "b.md", "# B")
        _write(isolated_repo / "docs" / "ignored.txt", "x")
        nodes = gb.collect_md_files()
        rels = {gb.to_repo_rel(p) for p in nodes}
        assert "docs/a.md" in rels
        assert "docs/sub/b.md" in rels
        assert "docs/ignored.txt" not in rels

    def test_extras_appended_when_present(
        self, isolated_repo: Path
    ) -> None:
        _write(isolated_repo / "AGENTS.md", "# Agents")
        _write(isolated_repo / "README.md", "# Readme")
        nodes = gb.collect_md_files()
        rels = {gb.to_repo_rel(p) for p in nodes}
        assert "AGENTS.md" in rels
        assert "README.md" in rels

    def test_missing_extras_silently_skipped(
        self, isolated_repo: Path
    ) -> None:
        # No extras present. Should not raise.
        nodes = gb.collect_md_files()
        # Empty (zero docs/ files, zero extras) — must not error.
        assert nodes == []

    def test_returns_sorted_deduplicated_resolved_paths(
        self, isolated_repo: Path
    ) -> None:
        # Two paths that resolve to the same file (symlink would
        # be ideal but we just verify no duplicates surface).
        _write(isolated_repo / "docs" / "zeta.md", "# Z")
        _write(isolated_repo / "docs" / "alpha.md", "# A")
        nodes = gb.collect_md_files()
        # Sorted by absolute path → alpha first, zeta second.
        rels = [gb.to_repo_rel(p) for p in nodes]
        assert rels == ["docs/alpha.md", "docs/zeta.md"]

    def test_skips_directory_with_md_extension(
        self, isolated_repo: Path
    ) -> None:
        """Covers the False arm of ``if p.is_file()`` — when
        ``rglob('*.md')`` returns a directory whose name happens
        to end with ``.md`` (a real-world case for some doc
        layouts)."""
        # Directory named like a markdown file.
        (isolated_repo / "docs" / "fakedir.md").mkdir()
        # Real file alongside it.
        _write(isolated_repo / "docs" / "real.md", "# real")
        nodes = gb.collect_md_files()
        rels = {gb.to_repo_rel(p) for p in nodes}
        assert "docs/real.md" in rels
        # The directory was skipped — it does not appear as a node.
        assert "docs/fakedir.md" not in rels


# ---------------------------------------------------------------------------
# to_repo_rel
# ---------------------------------------------------------------------------


class TestToRepoRel:
    def test_strips_repo_prefix(self, isolated_repo: Path) -> None:
        p = isolated_repo / "docs" / "foo.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.touch()
        assert gb.to_repo_rel(p) == "docs/foo.md"

    def test_normalises_separator_to_forward_slash(
        self,
        isolated_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """If ``os.sep`` were ``\\``, the function would convert it
        to ``/``. We can't change ``os.sep`` at runtime, but the
        replace() is unconditional so it always runs; assert it
        produces a forward-slash path."""
        p = isolated_repo / "docs" / "x" / "y.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.touch()
        out = gb.to_repo_rel(p)
        assert "\\" not in out
        assert out == "docs/x/y.md"


# ---------------------------------------------------------------------------
# collect_inbound
# ---------------------------------------------------------------------------


class TestCollectInbound:
    def test_happy_path_records_inbound_edges(
        self, isolated_repo: Path
    ) -> None:
        _write(isolated_repo / "docs" / "a.md", "# A\nSee [B](b.md).")
        _write(isolated_repo / "docs" / "b.md", "# B")
        inbound = gb.collect_inbound(gb.collect_md_files())
        assert "docs/b.md" in inbound
        assert inbound["docs/b.md"] == [("docs/a.md", "B")]

    def test_strips_autogen_footer(self, isolated_repo: Path) -> None:
        """If the footer were left in scope, the FOOTER label would
        be captured. Stripping the footer means only the real
        link's label ("Real-B") is captured."""
        a_body = (
            "# A\n\n[Real-B](b.md)\n\n"
            f"{gb.AUTOGEN_BEGIN}\n"
            "Footer: [Footer-B](b.md)\n"
            f"{gb.AUTOGEN_END}\n"
        )
        _write(isolated_repo / "docs" / "a.md", a_body)
        _write(isolated_repo / "docs" / "b.md", "# B")
        inbound = gb.collect_inbound(gb.collect_md_files())
        # Only the real link's label survives — dedup means one
        # entry total, and the Footer-B label is NOT what we see.
        assert inbound["docs/b.md"] == [("docs/a.md", "Real-B")]

    def test_strips_fenced_code_blocks(
        self, isolated_repo: Path
    ) -> None:
        a_body = (
            "# A\n\nReal: [B](b.md)\n\n"
            "```\nIn fence: [Fake](b.md)\n```\n"
        )
        _write(isolated_repo / "docs" / "a.md", a_body)
        _write(isolated_repo / "docs" / "b.md", "# B")
        inbound = gb.collect_inbound(gb.collect_md_files())
        assert len(inbound["docs/b.md"]) == 1
        assert inbound["docs/b.md"][0][1] == "B"

    def test_strips_inline_code(self, isolated_repo: Path) -> None:
        a_body = (
            "# A\n\nReal: [B](b.md)\n\n"
            "Inline: `[Inline-fake](b.md)`\n"
        )
        _write(isolated_repo / "docs" / "a.md", a_body)
        _write(isolated_repo / "docs" / "b.md", "# B")
        inbound = gb.collect_inbound(gb.collect_md_files())
        assert len(inbound["docs/b.md"]) == 1

    def test_skips_non_md_targets(
        self, isolated_repo: Path
    ) -> None:
        _write(
            isolated_repo / "docs" / "a.md",
            "[png](b.png)\n[real](b.md)\n",
        )
        _write(isolated_repo / "docs" / "b.md", "# B")
        inbound = gb.collect_inbound(gb.collect_md_files())
        assert len(inbound["docs/b.md"]) == 1

    def test_skips_external_urls(self, isolated_repo: Path) -> None:
        _write(
            isolated_repo / "docs" / "a.md",
            (
                "[http](http://example.com/x.md)\n"
                "[mailto](mailto:foo@bar.md)\n"
                "[file](file:///etc/passwd.md)\n"
                "[scheme-rel](//cdn.example.com/x.md)\n"
                "[real](b.md)\n"
            ),
        )
        _write(isolated_repo / "docs" / "b.md", "# B")
        inbound = gb.collect_inbound(gb.collect_md_files())
        # Only the real link survives.
        assert len(inbound["docs/b.md"]) == 1

    def test_skips_target_outside_repo(
        self,
        isolated_repo: Path,
        tmp_path: Path,
    ) -> None:
        """A link that points outside REPO via ../../ triggers the
        ValueError arm of relative_to()."""
        _write(
            isolated_repo / "docs" / "a.md",
            "[outside](../../escape.md)\n",
        )
        # Create the outside file so the path actually resolves
        # (but it's outside REPO).
        _write(tmp_path / "escape.md", "outside")
        inbound = gb.collect_inbound(gb.collect_md_files())
        # No edges — the outside link was rejected.
        assert all(not v for v in inbound.values())

    def test_skips_target_not_in_node_set(
        self, isolated_repo: Path
    ) -> None:
        """Link to docs/missing.md when missing.md isn't created
        is dropped by the ``if rel not in by_path`` arm."""
        _write(isolated_repo / "docs" / "a.md", "[m](missing.md)")
        inbound = gb.collect_inbound(gb.collect_md_files())
        # missing.md never created → no entry in by_path → dropped.
        assert "docs/missing.md" not in inbound

    def test_skips_self_reference(
        self, isolated_repo: Path
    ) -> None:
        _write(
            isolated_repo / "docs" / "a.md",
            "[Self](a.md)\n[real](b.md)\n",
        )
        _write(isolated_repo / "docs" / "b.md", "# B")
        inbound = gb.collect_inbound(gb.collect_md_files())
        # a.md is NOT in its own inbound list.
        assert "docs/a.md" not in inbound

    def test_deduplicates_within_source(
        self, isolated_repo: Path
    ) -> None:
        _write(
            isolated_repo / "docs" / "a.md",
            "[B once](b.md)\n[B twice](b.md)\n",
        )
        _write(isolated_repo / "docs" / "b.md", "# B")
        inbound = gb.collect_inbound(gb.collect_md_files())
        # Only one edge despite two links a.md → b.md.
        assert len(inbound["docs/b.md"]) == 1

    def test_truncates_label_to_80_chars(
        self, isolated_repo: Path
    ) -> None:
        long_label = "x" * 150
        _write(
            isolated_repo / "docs" / "a.md",
            f"[{long_label}](b.md)",
        )
        _write(isolated_repo / "docs" / "b.md", "# B")
        inbound = gb.collect_inbound(gb.collect_md_files())
        assert len(inbound["docs/b.md"][0][1]) == 80

    def test_strips_anchor_before_target_lookup(
        self, isolated_repo: Path
    ) -> None:
        _write(
            isolated_repo / "docs" / "a.md",
            "[B-section](b.md#section)\n",
        )
        _write(isolated_repo / "docs" / "b.md", "# B")
        inbound = gb.collect_inbound(gb.collect_md_files())
        # Anchor is stripped → b.md is the target.
        assert "docs/b.md" in inbound

    def test_skips_empty_target(self, isolated_repo: Path) -> None:
        """A link like ``[label](#anchor-only)`` has empty target
        after the ``split('#')[0]`` strip — covered by the
        ``if not tgt`` guard."""
        _write(
            isolated_repo / "docs" / "a.md",
            "[anchor-only](#section)\n[real](b.md)\n",
        )
        _write(isolated_repo / "docs" / "b.md", "# B")
        inbound = gb.collect_inbound(gb.collect_md_files())
        # Only b.md, anchor-only is dropped.
        assert len(inbound["docs/b.md"]) == 1


# ---------------------------------------------------------------------------
# render
# ---------------------------------------------------------------------------


class TestRender:
    def test_header_and_counts_present(
        self, isolated_repo: Path
    ) -> None:
        _write(isolated_repo / "docs" / "a.md", "[B](b.md)")
        _write(isolated_repo / "docs" / "b.md", "# B")
        nodes = gb.collect_md_files()
        inbound = gb.collect_inbound(nodes)
        out = gb.render(inbound, nodes)
        assert "# Backlinks — What links here" in out
        # "2 pages indexed; 1 have at least one inbound link; 1 edges"
        assert "2 pages indexed" in out
        assert "1 have at least one" in out
        assert "1 unique source→target edges" in out

    def test_target_with_no_inbound_shows_placeholder(
        self, isolated_repo: Path
    ) -> None:
        # Two pages, no cross-links.
        _write(isolated_repo / "docs" / "a.md", "# A")
        _write(isolated_repo / "docs" / "b.md", "# B")
        nodes = gb.collect_md_files()
        inbound = gb.collect_inbound(nodes)
        out = gb.render(inbound, nodes)
        assert "_No inbound links yet._" in out
        # Counts reflect zero inbound.
        assert "0 have at least one" in out
        assert "0 unique source→target edges" in out

    def test_deduplicates_source_within_target(
        self, isolated_repo: Path
    ) -> None:
        """When collect_inbound dedups but the render output also
        de-dups again (seen_src), exercise that path by giving
        the same target two edges from the same source via a
        synthetic ``inbound`` dict."""
        _write(isolated_repo / "docs" / "a.md", "[b](b.md)")
        _write(isolated_repo / "docs" / "b.md", "# B")
        nodes = gb.collect_md_files()
        # Inject two duplicate entries to exercise the seen_src dedup.
        inbound: dict = {
            "docs/b.md": [
                ("docs/a.md", "B once"),
                ("docs/a.md", "B twice"),
            ]
        }
        out = gb.render(inbound, nodes)
        # Only one bullet should appear for docs/a.md.
        assert out.count("- [`docs/a.md`]") == 1

    def test_relpath_value_error_arm_falls_back_to_src(
        self,
        isolated_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Force ``os.path.relpath`` to raise ``ValueError`` (the
        cross-drive case on win32) and assert render() falls back
        to the raw ``src`` string."""
        _write(isolated_repo / "docs" / "a.md", "[b](b.md)")
        _write(isolated_repo / "docs" / "b.md", "# B")
        nodes = gb.collect_md_files()
        inbound = gb.collect_inbound(nodes)

        real_relpath = os.path.relpath

        def _raise(*args, **kwargs):
            raise ValueError("simulated cross-drive case")

        monkeypatch.setattr(os.path, "relpath", _raise)
        try:
            out = gb.render(inbound, nodes)
        finally:
            monkeypatch.setattr(os.path, "relpath", real_relpath)
        # Fallback: rel = src, so the link text equals the raw src.
        assert "(docs/a.md)" in out


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


class TestMain:
    def test_write_mode_creates_output(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _write(isolated_repo / "docs" / "a.md", "[b](b.md)")
        _write(isolated_repo / "docs" / "b.md", "# B")
        rc = gb.main([])
        assert rc == 0
        assert gb.OUTPUT.exists()
        printed = capsys.readouterr().out
        assert "Wrote" in printed
        assert "edges" in printed

    def test_check_mode_pass_when_up_to_date(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _write(isolated_repo / "docs" / "a.md", "[b](b.md)")
        _write(isolated_repo / "docs" / "b.md", "# B")
        # Run write mode TWICE so the second invocation accounts
        # for docs/backlinks.md being in the node set after the
        # first write. The second-pass output is the fixed-point
        # the --check gate compares against in real CI.
        assert gb.main([]) == 0
        assert gb.main([]) == 0
        capsys.readouterr()  # drain
        rc = gb.main(["--check"])
        assert rc == 0
        printed = capsys.readouterr().out
        assert "OK" in printed
        assert "up to date" in printed

    def test_check_mode_fail_when_missing(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _write(isolated_repo / "docs" / "a.md", "[b](b.md)")
        _write(isolated_repo / "docs" / "b.md", "# B")
        # Do NOT write the output first.
        rc = gb.main(["--check"])
        assert rc == 1
        printed = capsys.readouterr().out
        assert "FAIL" in printed
        assert "does not exist" in printed

    def test_check_mode_fail_when_stale(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _write(isolated_repo / "docs" / "a.md", "[b](b.md)")
        _write(isolated_repo / "docs" / "b.md", "# B")
        # Write a stale version.
        gb.OUTPUT.write_text("stale content", encoding="utf-8")
        rc = gb.main(["--check"])
        assert rc == 1
        printed = capsys.readouterr().out
        assert "FAIL" in printed
        assert "stale" in printed

    def test_main_with_none_argv_uses_sys_argv(
        self,
        isolated_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When argv is None argparse falls back to sys.argv[1:]."""
        _write(isolated_repo / "docs" / "a.md", "[b](b.md)")
        _write(isolated_repo / "docs" / "b.md", "# B")
        monkeypatch.setattr(sys, "argv", ["generate_backlinks"])
        rc = gb.main(None)
        assert rc == 0
        assert gb.OUTPUT.exists()


# ---------------------------------------------------------------------------
# __main__ guard
# ---------------------------------------------------------------------------


class TestMainGuard:
    def test_runpy_invokes_main_via_guard(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Use runpy with run_name='__main__' so the ``if __name__
        == '__main__': sys.exit(main())`` line is exercised
        in-process (subprocess coverage wouldn't merge)."""
        repo = tmp_path / "repo"
        (repo / "docs").mkdir(parents=True)
        # Redirect the module-level REPO/OUTPUT before runpy reloads.
        # runpy.run_path reloads the module, so we need to monkey-patch
        # the path via env var the script doesn't have. Instead, we
        # redirect REPO/OUTPUT by adjusting __file__ resolution: place
        # the script at a tmp-relative location.
        script_src = (Path(gb.__file__).resolve())
        script_dst = repo / "scripts" / "generate_backlinks.py"
        script_dst.parent.mkdir(parents=True, exist_ok=True)
        script_dst.write_text(script_src.read_text(), encoding="utf-8")
        _write(repo / "docs" / "a.md", "[b](b.md)")
        _write(repo / "docs" / "b.md", "# B")
        monkeypatch.setattr(sys, "argv", ["generate_backlinks"])
        try:
            ns = runpy.run_path(
                str(script_dst), run_name="__main__"
            )
        except SystemExit as exc:
            assert exc.code == 0
        else:
            # Some runpy paths don't propagate sys.exit — still OK.
            assert "main" in ns
        assert (repo / "docs" / "backlinks.md").exists()
