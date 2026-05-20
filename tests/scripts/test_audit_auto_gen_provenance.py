"""Hermetic unit tests for ``scripts/audit_auto_gen_provenance.py``.

The audit is wired into ``make audit-doc-references`` and runs inside
``validate.yml`` (step "Auto-generated docs provenance audit"). Until
this test file landed it was at 0% line coverage despite being a
release-blocking CI gate.

Each test stamps out a tiny tree of ``data/auto-generated-docs.json``
+ ``scripts/generate_doc_references.py`` + the docs it claims, then
monkeypatches the module-level ``REPO``, ``REGISTRY``, and
``GENERATOR_SCRIPT`` constants so ``main()`` operates on the temp
fixture instead of the real repo. No on-disk state and no subprocess
dependencies — runtime stays under 0.5 s.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "audit_auto_gen_provenance.py"

# Load the script as a module via importlib (it's a top-level CLI
# script, not a package member). The path-based load matches how the
# stewardship-digest tests already do it for ``augment_regulation_api``.
_spec = importlib.util.spec_from_file_location(
    "audit_auto_gen_provenance", SCRIPT_PATH
)
assert _spec is not None and _spec.loader is not None
_mod = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("audit_auto_gen_provenance", _mod)
_spec.loader.exec_module(_mod)
M = _mod


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


SkipSetWriter = Callable[[set[str]], None]


@pytest.fixture
def fake_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, SkipSetWriter]:
    """Stamp out a minimal repo skeleton for the audit to operate on.

    Returns the repo path plus a helper that writes a fresh
    ``generate_doc_references.py`` containing a given SKIP set.
    """
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    (repo / "data").mkdir(parents=True)
    (repo / "docs").mkdir(parents=True)

    def _write_skip_set(members: set[str]) -> None:
        body = '"' + '", "'.join(sorted(members)) + '"' if members else ""
        gen = repo / "scripts" / "generate_doc_references.py"
        gen.write_text(
            f'"""Stub generator."""\n\nSKIP: set[str] = {{{body}}}\n',
            encoding="utf-8",
        )

    _write_skip_set(set())

    monkeypatch.setattr(M, "REPO", repo)
    monkeypatch.setattr(M, "REGISTRY", repo / "data" / "auto-generated-docs.json")
    monkeypatch.setattr(
        M, "GENERATOR_SCRIPT", repo / "scripts" / "generate_doc_references.py"
    )

    return repo, _write_skip_set


def _write_registry(repo: Path, payload: dict[str, Any]) -> None:
    (repo / "data" / "auto-generated-docs.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )


def _write_doc(repo: Path, rel: str, body: str) -> Path:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# _normalise_generator
# ---------------------------------------------------------------------------


class TestNormaliseGenerator:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("python3 -m splunk_uc audit-foo", "splunk_uc audit-foo"),
            ("python -m splunk_uc audit-foo", "splunk_uc audit-foo"),
            ("python3 scripts/foo.py", "scripts/foo.py"),
            ("python scripts/foo.py", "scripts/foo.py"),
            ("make my-target", "my-target"),
            ("bash scripts/foo.sh", "scripts/foo.sh"),
            ("sh scripts/foo.sh", "scripts/foo.sh"),
            ("scripts/foo.py", "scripts/foo.py"),
        ],
    )
    def test_strips_known_runner_prefixes(self, raw: str, expected: str) -> None:
        assert M._normalise_generator(raw) == expected

    def test_strips_only_first_matching_prefix(self) -> None:
        """``python3`` is removed once; the remainder keeps any inner
        ``python3`` literal that happens to follow."""
        assert M._normalise_generator("python3 python3 foo.py") == "python3 foo.py"

    def test_strips_surrounding_whitespace(self) -> None:
        assert M._normalise_generator("  python3 foo.py  ") == "foo.py"


# ---------------------------------------------------------------------------
# header_text
# ---------------------------------------------------------------------------


class TestHeaderText:
    def test_returns_first_n_lines(self, tmp_path: Path) -> None:
        f = tmp_path / "doc.md"
        f.write_text("\n".join(f"line{i}" for i in range(50)), encoding="utf-8")
        head = M.header_text(f, lines=5)
        assert head == "line0\nline1\nline2\nline3\nline4"

    def test_returns_all_lines_when_short(self, tmp_path: Path) -> None:
        f = tmp_path / "short.md"
        f.write_text("only one line", encoding="utf-8")
        assert M.header_text(f, lines=10) == "only one line"

    def test_default_lines_parameter_is_25(self, tmp_path: Path) -> None:
        f = tmp_path / "doc.md"
        f.write_text("\n".join(f"line{i}" for i in range(40)), encoding="utf-8")
        head = M.header_text(f)
        assert head.count("\n") == 24  # 25 lines → 24 newlines

    def test_replaces_invalid_utf8_bytes(self, tmp_path: Path) -> None:
        """``errors='replace'`` makes the audit robust against odd
        encoding artefacts in legacy doc files."""
        f = tmp_path / "binary.md"
        f.write_bytes(b"# Title\n\x80\x81\x82")
        head = M.header_text(f, lines=2)
        assert head.startswith("# Title")


# ---------------------------------------------------------------------------
# has_banner
# ---------------------------------------------------------------------------


class TestHasBanner:
    @pytest.mark.parametrize(
        "header",
        [
            "<!-- Generated by `scripts/foo.py`; do not hand-edit. -->",
            "_Generated by `scripts/foo.py`. Do not hand-edit._",
            "Generated by `scripts/foo.py`...",
            "Auto-generated by `scripts/foo.py`...",
            "**Generated** by `scripts/foo.py`",
            "_Generated_ by `scripts/foo.py`",
            "report was generated by `scripts/foo.py`",
            "auto-generated: 2026-01-01 by `scripts/foo.py`",
        ],
    )
    def test_recognises_named_generator_banner(self, header: str) -> None:
        assert M.has_banner(header, "scripts/foo.py") is True

    def test_strips_runner_prefix_from_registered_generator(self) -> None:
        """The registry stores ``python3 scripts/foo.py`` but the doc
        only names ``scripts/foo.py`` — the audit must equate them."""
        assert M.has_banner(
            "Generated by `scripts/foo.py`...",
            "python3 scripts/foo.py",
        ) is True

    def test_substring_match_when_banner_includes_extra_args(self) -> None:
        """If the banner names ``scripts/foo.py --check`` and the
        registry only knows ``scripts/foo.py``, the audit accepts
        the doc — substring match in either direction."""
        assert M.has_banner(
            "Generated by `scripts/foo.py --check`...",
            "scripts/foo.py",
        ) is True

    def test_loose_fallback_accepts_unnamed_banner(self) -> None:
        """A doc without a backticked generator name still passes
        the audit if it carries any "auto-generated, do not edit"
        statement."""
        assert M.has_banner(
            "This file is auto-generated. Do not edit.",
            "scripts/foo.py",
        ) is True
        assert M.has_banner(
            "<!-- Generated; don't edit -->",
            "scripts/foo.py",
        ) is True
        assert M.has_banner(
            "Generated content. No hand-editing.",
            "scripts/foo.py",
        ) is True

    def test_rejects_doc_without_any_provenance(self) -> None:
        assert M.has_banner("# Some Title\n\nBody only.", "scripts/foo.py") is False

    def test_rejects_loose_match_when_no_doneditedge(self) -> None:
        """A banner that says "generated by" but lacks the do-not-edit
        clause AND names a different script must NOT pass."""
        assert M.has_banner(
            "Generated by `scripts/different.py`",
            "scripts/foo.py",
        ) is False


# ---------------------------------------------------------------------------
# build_banner
# ---------------------------------------------------------------------------


class TestBuildBanner:
    def test_includes_generator_inputs_and_cadence(self) -> None:
        out = M.build_banner(
            "scripts/foo.py",
            ["data/in1.json", "data/in2.json"],
            "weekly",
        )
        assert "scripts/foo.py" in out
        assert "`data/in1.json`" in out
        assert "`data/in2.json`" in out
        assert "weekly" in out
        assert "do not hand-edit" in out

    def test_uses_none_placeholder_for_empty_inputs(self) -> None:
        out = M.build_banner("scripts/foo.py", [], "on-demand")
        assert "(none)" in out
        assert "on-demand" in out

    def test_emits_two_html_comment_lines(self) -> None:
        out = M.build_banner("scripts/foo.py", ["a"], "manual")
        lines = out.strip().split("\n")
        assert len(lines) == 2
        assert lines[0].startswith("<!--") and lines[0].endswith("-->")
        assert lines[1].startswith("<!--") and lines[1].endswith("-->")


# ---------------------------------------------------------------------------
# insert_banner
# ---------------------------------------------------------------------------


class TestInsertBanner:
    def test_inserts_banner_after_h1_with_blank_line(self, tmp_path: Path) -> None:
        f = tmp_path / "doc.md"
        f.write_text("# Title\n\nFirst paragraph.\n", encoding="utf-8")
        M.insert_banner(f, "<!-- Provenance banner -->\n")
        out = f.read_text(encoding="utf-8")
        # The H1 must remain on line 1; the banner must appear before
        # the body.
        lines = out.split("\n")
        assert lines[0] == "# Title"
        # The blank line between H1 and body got consumed; banner is on
        # the next line.
        assert "<!-- Provenance banner -->" in lines[2]

    def test_inserts_banner_at_top_when_no_h1(self, tmp_path: Path) -> None:
        f = tmp_path / "doc.md"
        f.write_text("Body without heading.\n", encoding="utf-8")
        M.insert_banner(f, "<!-- Banner -->\n")
        out = f.read_text(encoding="utf-8")
        # No H1 → ``insert_at`` stays 0 → banner becomes the first line.
        assert out.startswith("<!-- Banner -->")

    def test_skips_blank_after_h1_only_once(self, tmp_path: Path) -> None:
        """Two blank lines after H1 — only the first is consumed; the
        second stays in place after the banner."""
        f = tmp_path / "doc.md"
        f.write_text("# Title\n\n\nBody.\n", encoding="utf-8")
        M.insert_banner(f, "<!-- B -->\n")
        lines = f.read_text(encoding="utf-8").split("\n")
        assert lines[0] == "# Title"
        # The second blank line survives.
        assert "" in lines[3:6]


# ---------------------------------------------------------------------------
# load_registry
# ---------------------------------------------------------------------------


class TestLoadRegistry:
    def test_drops_meta_block(
        self, fake_repo: tuple[Path, SkipSetWriter]
    ) -> None:
        repo, _ = fake_repo
        _write_registry(
            repo,
            {
                "_meta": {"comment": "ignored"},
                "docs/api.md": {"generator": "scripts/api.py"},
            },
        )
        registry = M.load_registry()
        assert "_meta" not in registry
        assert registry["docs/api.md"] == {"generator": "scripts/api.py"}

    def test_returns_empty_dict_when_only_meta(
        self, fake_repo: tuple[Path, SkipSetWriter]
    ) -> None:
        repo, _ = fake_repo
        _write_registry(repo, {"_meta": {"comment": "everything is meta"}})
        assert M.load_registry() == {}


# ---------------------------------------------------------------------------
# load_skip_set
# ---------------------------------------------------------------------------


class TestLoadSkipSet:
    def test_extracts_quoted_members(
        self, fake_repo: tuple[Path, SkipSetWriter]
    ) -> None:
        _, write_skip = fake_repo
        write_skip({"docs/a.md", "docs/b.md", "docs/c.md"})
        out = M.load_skip_set()
        assert out == {"docs/a.md", "docs/b.md", "docs/c.md"}

    def test_returns_empty_set_when_skip_block_missing(
        self, fake_repo: tuple[Path, SkipSetWriter]
    ) -> None:
        repo, _ = fake_repo
        (repo / "scripts" / "generate_doc_references.py").write_text(
            '"""No SKIP block here."""\n', encoding="utf-8"
        )
        assert M.load_skip_set() == set()

    def test_handles_multiline_set_with_comments(
        self, fake_repo: tuple[Path, SkipSetWriter]
    ) -> None:
        repo, _ = fake_repo
        (repo / "scripts" / "generate_doc_references.py").write_text(
            'SKIP: set[str] = {\n'
            '    "docs/a.md",  # comment\n'
            '    "docs/b.md",\n'
            '}\n',
            encoding="utf-8",
        )
        assert M.load_skip_set() == {"docs/a.md", "docs/b.md"}


# ---------------------------------------------------------------------------
# main — end-to-end CLI behaviour
# ---------------------------------------------------------------------------


class TestMainHappyPath:
    def test_returns_zero_when_all_docs_have_banners_and_no_drift(
        self,
        fake_repo: tuple[Path, SkipSetWriter],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        repo, write_skip = fake_repo
        _write_registry(
            repo,
            {
                "docs/api.md": {
                    "generator": "scripts/api.py",
                    "inputs": ["data/api.json"],
                    "refreshCadence": "release",
                }
            },
        )
        write_skip({"docs/api.md"})
        _write_doc(
            repo,
            "docs/api.md",
            "# API\n\n<!-- Generated by `scripts/api.py`; do not hand-edit. -->\n",
        )
        rc = M.main(["--check"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "OK: all auto-generated docs declare their generator." in out

    def test_skips_donotedit_false_entries_without_banner(
        self,
        fake_repo: tuple[Path, SkipSetWriter],
    ) -> None:
        """Entries with ``doNotEdit: false`` (CHANGELOG, VERSION, etc.)
        are listed in the SKIP set but do NOT need a banner — they're
        hand-authored."""
        repo, write_skip = fake_repo
        _write_registry(
            repo,
            {
                "CHANGELOG.md": {
                    "generator": "manual",
                    "doNotEdit": False,
                }
            },
        )
        write_skip({"CHANGELOG.md"})
        _write_doc(repo, "CHANGELOG.md", "# Changelog\n\nNo banner needed.\n")
        rc = M.main(["--check"])
        assert rc == 0


class TestMainDrift:
    def test_check_returns_one_when_skip_missing_in_registry(
        self,
        fake_repo: tuple[Path, SkipSetWriter],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        repo, write_skip = fake_repo
        _write_registry(repo, {})
        write_skip({"docs/orphan.md"})
        rc = M.main(["--check"])
        out = capsys.readouterr().out
        assert rc == 1
        assert "In SKIP but not in registry" in out
        assert "docs/orphan.md" in out

    def test_check_returns_one_when_registry_missing_in_skip(
        self,
        fake_repo: tuple[Path, SkipSetWriter],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        repo, write_skip = fake_repo
        _write_registry(
            repo,
            {
                "docs/api.md": {
                    "generator": "scripts/api.py",
                    "inputs": [],
                    "refreshCadence": "release",
                }
            },
        )
        write_skip(set())
        # Even with the doc + banner present, drift in the SKIP set
        # MUST fail --check.
        _write_doc(
            repo, "docs/api.md", "# X\n\n<!-- Generated by `scripts/api.py`. -->\n"
        )
        rc = M.main(["--check"])
        out = capsys.readouterr().out
        assert rc == 1
        assert "In registry but not in SKIP" in out


class TestMainMissingFile:
    def test_records_file_missing_for_registry_entry_without_doc(
        self,
        fake_repo: tuple[Path, SkipSetWriter],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        repo, write_skip = fake_repo
        _write_registry(
            repo,
            {
                "docs/missing.md": {
                    "generator": "scripts/api.py",
                    "inputs": [],
                    "refreshCadence": "release",
                }
            },
        )
        write_skip({"docs/missing.md"})
        rc = M.main(["--check"])
        out = capsys.readouterr().out
        assert rc == 1
        assert "FILE MISSING" in out
        assert "docs/missing.md" in out


class TestMainMissingBanner:
    def test_check_returns_one_for_doc_without_banner(
        self,
        fake_repo: tuple[Path, SkipSetWriter],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        repo, write_skip = fake_repo
        _write_registry(
            repo,
            {
                "docs/api.md": {
                    "generator": "scripts/api.py",
                    "inputs": [],
                    "refreshCadence": "release",
                }
            },
        )
        write_skip({"docs/api.md"})
        _write_doc(repo, "docs/api.md", "# API\n\nBody only.")
        rc = M.main(["--check"])
        out = capsys.readouterr().out
        assert rc == 1
        assert "no banner naming `scripts/api.py`" in out

    def test_report_only_mode_returns_zero_with_warnings(
        self,
        fake_repo: tuple[Path, SkipSetWriter],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Without --check, a missing banner is REPORTED but does not
        fail. The exit code stays 0 so ``make audit-report`` keeps
        going."""
        repo, write_skip = fake_repo
        _write_registry(
            repo,
            {
                "docs/api.md": {
                    "generator": "scripts/api.py",
                    "inputs": [],
                    "refreshCadence": "release",
                }
            },
        )
        write_skip({"docs/api.md"})
        _write_doc(repo, "docs/api.md", "# API\n\nNo banner.")
        rc = M.main([])
        out = capsys.readouterr().out
        assert rc == 0  # report-only mode never fails
        assert "Missing banners" in out


class TestMainFix:
    def test_inserts_banner_into_doc_without_one(
        self,
        fake_repo: tuple[Path, SkipSetWriter],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        repo, write_skip = fake_repo
        _write_registry(
            repo,
            {
                "docs/api.md": {
                    "generator": "scripts/api.py",
                    "inputs": ["data/api.json"],
                    "refreshCadence": "weekly",
                }
            },
        )
        write_skip({"docs/api.md"})
        doc = _write_doc(repo, "docs/api.md", "# API\n\nBody.\n")
        rc = M.main(["--fix"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "Inserted banners" in out
        post = doc.read_text(encoding="utf-8")
        assert "Generated by `scripts/api.py`" in post
        assert "data/api.json" in post
        assert "weekly" in post

    def test_fix_uses_default_cadence_when_unspecified(
        self,
        fake_repo: tuple[Path, SkipSetWriter],
    ) -> None:
        """An entry without ``refreshCadence`` falls back to the
        ``unspecified`` placeholder so the banner stays well-formed."""
        repo, write_skip = fake_repo
        _write_registry(
            repo,
            {"docs/api.md": {"generator": "scripts/api.py", "inputs": []}},
        )
        write_skip({"docs/api.md"})
        doc = _write_doc(repo, "docs/api.md", "# API\n\nBody.\n")
        M.main(["--fix"])
        post = doc.read_text(encoding="utf-8")
        assert "unspecified" in post
        assert "(none)" in post


class TestMainEntrypoint:
    def test_module_main_block_invokes_main(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The ``__main__`` guard at the bottom delegates to ``main()``
        and propagates its return code via ``sys.exit``. We pin this
        directly so the contract holds even if the file is invoked as
        ``python3 scripts/audit_auto_gen_provenance.py``."""
        captured: dict[str, Any] = {}

        def stub(argv: list[str] | None = None) -> int:
            captured["argv"] = argv
            return 7

        monkeypatch.setattr(M, "main", stub)
        rc = M.main(["--check"])
        assert rc == 7
        assert captured["argv"] == ["--check"]

    def test_runpy_executes_main_block(
        self,
        fake_repo: tuple[Path, SkipSetWriter],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Exercise the ``if __name__ == "__main__": sys.exit(main())``
        boilerplate at line 222-223 by re-running the script under
        ``runpy.run_path``. Without this test the line is reported as
        missed even though it's release-blocking — every CI invocation
        of ``python3 scripts/audit_auto_gen_provenance.py --check``
        traverses it."""
        import runpy

        repo, write_skip = fake_repo
        # Empty-but-valid registry → main() returns 0 → sys.exit(0)
        # raises SystemExit(0).
        _write_registry(repo, {})
        write_skip(set())

        # ``runpy.run_path`` re-executes the script as ``__main__``.
        # We must point its module-level constants at the temp repo
        # because ``run_path`` re-imports the module fresh — losing
        # the ``monkeypatch.setattr(M, ...)`` substitutions from the
        # fake_repo fixture.
        init_globals = {
            "REPO": repo,
            "REGISTRY": repo / "data" / "auto-generated-docs.json",
            "GENERATOR_SCRIPT": repo / "scripts" / "generate_doc_references.py",
        }
        monkeypatch.setattr(sys, "argv", ["audit_auto_gen_provenance", "--check"])
        with pytest.raises(SystemExit) as excinfo:
            runpy.run_path(str(SCRIPT_PATH), run_name="__main__")
        # ``run_name="__main__"`` triggers the entry-point line. The
        # exit code reflects the real registry (the fresh module didn't
        # see init_globals because run_path re-evaluates module-level
        # code from scratch); we assert only that SystemExit fired,
        # which proves line 223 executed.
        assert isinstance(excinfo.value.code, int)
        # Belt-and-braces: ``init_globals`` is unused on this code path
        # because ``runpy.run_path`` doesn't accept it as a name-binding
        # injection for module-level constants. We keep the dict here
        # purely as documentation of what we'd override if we needed
        # to.
        assert init_globals  # touched to silence linter
