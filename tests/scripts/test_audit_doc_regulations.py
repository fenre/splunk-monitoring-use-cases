"""Hermetic unit tests for ``scripts/audit_doc_regulations.py``.

The audit walks ``docs/`` + ``DEFAULT_EXTRA`` markdown files for
regulation acronyms and clause overshoots, and writes a stable
``data/doc-regulation-mentions.json`` report. Until this file landed
the script was at 0% line coverage despite being a maintained
audit step.

Each test stamps out a tiny markdown corpus + a fake cat-22 sidecar
under ``tmp_path`` and monkeypatches the module-level ``REPO``,
``DOCS_DIR``, ``CAT_DIR``, and ``STATUS_PATH`` constants so the
public functions operate on the temp tree. No subprocess use, no
network, no on-disk state — runtime stays under 0.5 s.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "audit_doc_regulations.py"

# Load via importlib (top-level CLI script, not a package member).
_spec = importlib.util.spec_from_file_location("audit_doc_regulations", SCRIPT_PATH)
assert _spec is not None and _spec.loader is not None
_mod = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("audit_doc_regulations", _mod)
_spec.loader.exec_module(_mod)
M = _mod


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Stamp out a minimal repo with the directories the audit walks."""
    repo = tmp_path / "repo"
    (repo / "docs").mkdir(parents=True)
    (repo / "content" / "cat-22-regulatory-compliance").mkdir(parents=True)
    (repo / "data").mkdir(parents=True)

    monkeypatch.setattr(M, "REPO", repo)
    monkeypatch.setattr(M, "DOCS_DIR", repo / "docs")
    monkeypatch.setattr(M, "CAT_DIR", repo / "content" / "cat-22-regulatory-compliance")
    monkeypatch.setattr(M, "STATUS_PATH", repo / "data" / "doc-regulation-mentions.json")
    return repo


def _write_md(repo: Path, rel: str, body: str) -> Path:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p


def _write_uc(repo: Path, name: str, payload: dict[str, Any]) -> Path:
    p = repo / "content" / "cat-22-regulatory-compliance" / name
    p.write_text(json.dumps(payload), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# clean_prose
# ---------------------------------------------------------------------------


class TestCleanProse:
    def test_strips_yaml_frontmatter(self) -> None:
        text = "---\ntitle: foo\nslug: bar\n---\nBody text.\n"
        out = M.clean_prose(text)
        assert "title: foo" not in out
        assert "Body text." in out

    def test_strips_autogen_references_block(self) -> None:
        text = (
            "Real prose.\n\n"
            "<!-- BEGIN AUTOGEN: references -->\n"
            "Generated bibliography content with FAKEREG references.\n"
            "<!-- END AUTOGEN: references -->\n\n"
            "More real prose."
        )
        out = M.clean_prose(text)
        assert "FAKEREG" not in out
        assert "Real prose." in out
        assert "More real prose." in out

    def test_strips_fenced_code_blocks_with_indentation(self) -> None:
        """The FENCE_RE accepts up to 3 leading spaces/tabs of
        indentation and replaces the fenced block with whitespace
        of equal length so line / column offsets stay stable."""
        text = "Prose.\n   ```python\nFAKEREG_TOKEN = 1\n   ```\nAfter.\n"
        out = M.clean_prose(text)
        assert "FAKEREG_TOKEN" not in out
        assert "Prose." in out
        assert "After." in out

    def test_strips_inline_code(self) -> None:
        text = "Use the `FAKEREG_INSIDE` constant or ``FAKEREG2``."
        out = M.clean_prose(text)
        assert "FAKEREG_INSIDE" not in out
        assert "FAKEREG2" not in out

    def test_strips_html_tags_keeping_inner_text(self) -> None:
        text = "<sup>NOTE</sup> See <a href='x'>GDPR</a> Article 5."
        out = M.clean_prose(text)
        assert "<sup>" not in out
        assert "</a>" not in out
        # Inner anchor text survives because HTML_TAG_RE strips only
        # the tags, not the content between them.
        assert "GDPR" in out
        assert "Article 5" in out

    def test_collapses_markdown_links_to_label_text(self) -> None:
        text = "See [the PCI DSS standard](https://example.com/pci) for details."
        out = M.clean_prose(text)
        assert "https://example.com/pci" not in out
        assert "the PCI DSS standard" in out

    def test_returns_input_unchanged_when_no_markup(self) -> None:
        text = "Plain prose with no fences, frontmatter, or HTML."
        assert M.clean_prose(text) == text


# ---------------------------------------------------------------------------
# collect_docs
# ---------------------------------------------------------------------------


class TestCollectDocs:
    def test_walks_docs_dir_recursively(self, fake_repo: Path) -> None:
        _write_md(fake_repo, "docs/a.md", "# A")
        _write_md(fake_repo, "docs/sub/b.md", "# B")
        _write_md(fake_repo, "docs/sub/deep/c.md", "# C")
        out = M.collect_docs()
        names = {p.name for p in out}
        assert names == {"a.md", "b.md", "c.md"}

    def test_includes_default_extra_root_files_when_present(
        self, fake_repo: Path
    ) -> None:
        _write_md(fake_repo, "README.md", "# README")
        _write_md(fake_repo, "AGENTS.md", "# AGENTS")
        _write_md(fake_repo, "api/README.md", "# API")
        out = M.collect_docs()
        names = {p.name for p in out}
        # Both AGENTS.md and api/README.md (different paths, same
        # basename "README.md") are listed; collect_docs dedups by
        # resolved path, not name.
        assert "AGENTS.md" in names
        assert "README.md" in names

    def test_skips_default_extra_files_that_dont_exist(
        self, fake_repo: Path
    ) -> None:
        # No README.md, no AGENTS.md, and no docs/ entries.
        out = M.collect_docs()
        assert out == []

    def test_returns_sorted_unique_resolved_paths(self, fake_repo: Path) -> None:
        _write_md(fake_repo, "docs/z.md", "# Z")
        _write_md(fake_repo, "docs/a.md", "# A")
        out = M.collect_docs()
        # Sorted ascending by string.
        as_strs = [str(p) for p in out]
        assert as_strs == sorted(as_strs)

    def test_skips_non_markdown_files(self, fake_repo: Path) -> None:
        _write_md(fake_repo, "docs/keep.md", "# Keep")
        (fake_repo / "docs" / "skip.txt").write_text("text", encoding="utf-8")
        (fake_repo / "docs" / "skip.json").write_text("{}", encoding="utf-8")
        out = M.collect_docs()
        assert {p.name for p in out} == {"keep.md"}

    def test_skips_directory_with_md_extension(self, fake_repo: Path) -> None:
        """Cover the ``if p.is_file():`` False arm (line 81->80).

        ``Path.rglob("*.md")`` matches *any* path with a ``.md`` suffix —
        including a directory literally named ``fakedir.md``. The
        ``is_file()`` guard at line 81 of ``collect_docs`` is the only
        thing keeping such an entry out of the result; this test exercises
        the False arm.
        """
        _write_md(fake_repo, "docs/real.md", "# real")
        (fake_repo / "docs" / "fakedir.md").mkdir()
        out = M.collect_docs()
        names = {p.name for p in out}
        assert "real.md" in names
        assert "fakedir.md" not in names

    def test_no_docs_dir_falls_through_to_extras(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Cover the ``if DOCS_DIR.is_dir():`` False arm (line 79->83).

        When ``DOCS_DIR`` does not exist on disk, ``collect_docs`` must
        fall straight through to the ``DEFAULT_EXTRA`` loop. We point
        ``REPO`` at a fresh tmpdir whose ``docs/`` directory was never
        created, drop a ``README.md`` into the root, and confirm only
        the extras are returned.
        """
        repo = tmp_path / "no_docs_repo"
        repo.mkdir()
        (repo / "README.md").write_text("# README", encoding="utf-8")
        monkeypatch.setattr(M, "REPO", repo)
        monkeypatch.setattr(M, "DOCS_DIR", repo / "docs")  # does NOT exist
        out = M.collect_docs()
        names = {p.name for p in out}
        assert "README.md" in names


# ---------------------------------------------------------------------------
# load_catalog_acronyms
# ---------------------------------------------------------------------------


class TestLoadCatalogAcronyms:
    def test_extracts_acronyms_from_string_fields(self, fake_repo: Path) -> None:
        _write_uc(
            fake_repo,
            "UC-22.1.1.json",
            {
                "id": "22.1.1",
                "title": "GDPR Article 5 baseline",
                "description": "HIPAA Security Rule alignment for PCIDSS coverage.",
                "value": "Bridges to NIS2 reporting.",
                "implementation": "Use NIST CSF 2.0 mappings.",
                "visualization": "Glass table for SOX controls.",
            },
        )
        counts = M.load_catalog_acronyms()
        # Each ACRONYM_RE-matching uppercase ≥4-letter token in the
        # joined field text is counted. The regex ignores 3-letter
        # acronyms (SOX), so verify it catches the ≥4 ones.
        assert counts["GDPR"] >= 1
        assert counts["HIPAA"] >= 1
        assert counts["NIST"] >= 1
        # Three-letter tokens like SOX are NOT picked up by the
        # ACRONYM_RE ({4,12} bound).
        assert "SOX" not in counts

    def test_extracts_from_aliases_and_tag_lists(self, fake_repo: Path) -> None:
        _write_uc(
            fake_repo,
            "UC-22.1.2.json",
            {
                "id": "22.1.2",
                "title": "Auth controls",
                "aliases": ["HITRUST mapping", "SOC2 Type II"],
                "tags": ["FINRA", "FFIEC"],
                "complianceTags": ["PCIDSS"],
                "frameworks": ["DORA"],
            },
        )
        counts = M.load_catalog_acronyms()
        assert counts["HITRUST"] >= 1
        assert counts["FINRA"] >= 1
        assert counts["FFIEC"] >= 1
        assert counts["PCIDSS"] >= 1
        assert counts["DORA"] >= 1

    def test_skips_malformed_json_files(self, fake_repo: Path) -> None:
        good = fake_repo / "content" / "cat-22-regulatory-compliance" / "UC-22.1.1.json"
        good.write_text(json.dumps({"title": "GDPR", "tags": ["DORA"]}))
        bad = fake_repo / "content" / "cat-22-regulatory-compliance" / "UC-22.bad.json"
        bad.write_text("{not valid json", encoding="utf-8")
        # The audit must continue past the malformed file rather than
        # crashing — `try/except (OSError, json.JSONDecodeError)`.
        counts = M.load_catalog_acronyms()
        assert counts["DORA"] >= 1

    def test_returns_empty_when_cat_dir_missing(
        self, fake_repo: Path
    ) -> None:
        # Remove the cat-22 directory.
        cat_dir = fake_repo / "content" / "cat-22-regulatory-compliance"
        for child in cat_dir.iterdir():
            child.unlink()
        cat_dir.rmdir()
        counts = M.load_catalog_acronyms()
        assert counts == Counter()

    def test_ignores_non_string_field_values(self, fake_repo: Path) -> None:
        """Non-string ``title`` / ``description`` / etc. values must
        be silently skipped (the type guard at line 130)."""
        _write_uc(
            fake_repo,
            "UC-22.1.3.json",
            {
                "title": 12345,  # not a string
                "description": ["DORA", "ISO27001"],  # not a string
                "value": None,
                "tags": "not a list",  # not a list — skipped
                "complianceTags": ["GDPR"],
            },
        )
        counts = M.load_catalog_acronyms()
        # Only the "complianceTags" list is read; "tags" string and
        # non-string title/description/value are skipped.
        assert counts.get("GDPR", 0) >= 1
        # Confirm the non-string content was NOT scanned.
        assert "DORA" not in counts


# ---------------------------------------------------------------------------
# build_known_set
# ---------------------------------------------------------------------------


class TestBuildKnownSet:
    def test_unions_catalogue_generic_and_extra_known(self, fake_repo: Path) -> None:
        _write_uc(
            fake_repo,
            "UC-22.1.1.json",
            {"title": "Custom HOMEMADE-REG framework", "tags": ["MADEUP"]},
        )
        known = M.build_known_set()
        # From catalogue
        assert "MADEUP" in known
        assert "HOMEMADE" in known
        # From generic non-reg
        assert "API" in known
        assert "JSON" in known
        # From extra known regs
        assert "GDPR" in known
        assert "DORA" in known

    def test_includes_uppercase_variants(self, fake_repo: Path) -> None:
        # Build with an empty catalogue → only generic + extra.
        known = M.build_known_set()
        assert "ATT&CK" in known
        # Already uppercase, but the .upper() pass exercises the
        # comprehension at line 242.
        assert "ATT&CK".upper() in known


# ---------------------------------------------------------------------------
# CLAUSE_REFERENCE_RE / _build_clause_regex
# ---------------------------------------------------------------------------


class TestClauseRegex:
    def test_matches_canonical_form(self) -> None:
        m = M.CLAUSE_REFERENCE_RE.search("GDPR Article 124")
        assert m is not None
        assert m.group("acronym").upper() == "GDPR"
        assert m.group("keyword").lower() == "article"
        assert int(m.group("num")) == 124

    def test_does_not_match_short_keyword_variants(self) -> None:
        """``Art. 5`` is a common shorthand but the regex builds only
        from the literal keywords in ``REGULATION_CLAUSE_BOUNDS``
        (``article``, ``requirement``, ``control``). Pin the
        intentional non-match so a future contributor knows the
        shorthand is NOT supported."""
        assert M.CLAUSE_REFERENCE_RE.search("GDPR Art. 5") is None
        assert M.CLAUSE_REFERENCE_RE.search("PCI req. 12") is None

    def test_does_not_match_keyword_not_in_bounds(self) -> None:
        """The regex compiles from ``REGULATION_CLAUSE_BOUNDS``; only
        the registered keywords (``article``, ``requirement``,
        ``control``) are recognised. ``Section`` is NOT registered."""
        m = M.CLAUSE_REFERENCE_RE.search("GDPR Section 5")
        assert m is None

    def test_matches_with_hyphen_separator(self) -> None:
        m = M.CLAUSE_REFERENCE_RE.search("GDPR-article 5")
        assert m is not None
        assert m.group("num") == "5"

    def test_matches_with_nbsp_separator(self) -> None:
        m = M.CLAUSE_REFERENCE_RE.search("GDPR\u00a0article 5")
        assert m is not None

    def test_pci_requirement_form(self) -> None:
        m = M.CLAUSE_REFERENCE_RE.search("PCI requirement 13")
        assert m is not None
        assert m.group("acronym").upper() == "PCI"
        assert m.group("keyword").lower() == "requirement"
        assert int(m.group("num")) == 13

    def test_iso27001_control_form(self) -> None:
        m = M.CLAUSE_REFERENCE_RE.search("ISO27001 control 9")
        assert m is not None
        assert int(m.group("num")) == 9


# ---------------------------------------------------------------------------
# audit
# ---------------------------------------------------------------------------


class TestAudit:
    def test_records_unknown_acronyms_with_path_and_line(
        self, fake_repo: Path
    ) -> None:
        # Cat-22 catalogue says we cover GDPR; FAKEREG is unknown.
        _write_uc(fake_repo, "UC-22.1.1.json", {"tags": ["GDPR"]})
        doc = _write_md(
            fake_repo,
            "docs/intro.md",
            "# Intro\n\nWe align with GDPR and the FAKEREG2024 standard.\n",
        )
        result = M.audit([doc])
        ua = result["unknown_acronyms"]
        # GDPR is known via the EXTRA_KNOWN_REGS allowlist; FAKEREG2024
        # is not.
        assert "GDPR" not in ua
        assert "FAKEREG2024" in ua
        sample = ua["FAKEREG2024"]["samples"][0]
        assert sample["path"] == "docs/intro.md"
        assert sample["line"] == 3

    def test_clause_overshoot_detected_for_gdpr_article_124(
        self, fake_repo: Path
    ) -> None:
        doc = _write_md(
            fake_repo,
            "docs/test.md",
            "# X\n\nSee GDPR Article 124 for guidance.\n",
        )
        result = M.audit([doc])
        co = result["clause_overshoots"]
        assert any(
            entry["regulation"] == "GDPR"
            and entry["max_documented"] == 99
            and entry["clause"] == "Article 124"
            for entry in co
        )

    def test_clause_within_bound_not_flagged(
        self, fake_repo: Path
    ) -> None:
        doc = _write_md(
            fake_repo,
            "docs/test.md",
            "# X\n\nSee GDPR Article 5 and Article 99.\n",
        )
        result = M.audit([doc])
        assert result["clause_overshoots"] == []

    def test_unbound_acronym_clause_pair_is_silently_ignored(
        self, fake_repo: Path
    ) -> None:
        """The audit's clause sweep silently skips ``(acronym, keyword)``
        pairs that the regex matches but the bounds dict doesn't index.

        Pin the ``if max_idx is None: continue`` branch at line 338-339.

        ``CLAUSE_REFERENCE_RE`` is built from the *union* of acronyms
        and the *union* of keywords in ``REGULATION_CLAUSE_BOUNDS``.
        It therefore matches cross-products such as ``(PCI, article)``
        — both halves are in their respective unions — even though
        ``REGULATION_CLAUSE_BOUNDS`` only registers
        ``("PCI", "requirement")``. That cross-product hit is the
        natural trigger for the defensive ``max_idx is None`` skip.
        """
        doc = _write_md(
            fake_repo,
            "docs/test.md",
            # ``PCI`` is bound to ``requirement`` only (max 12). The
            # ``article`` keyword is in the regex's keyword union (via
            # GDPR/NIS2/...). ``(PCI, article)`` is NOT in the bounds
            # dict → ``max_idx`` is None → the entry MUST be skipped.
            "# X\n\nPCI Article 99 — should not be flagged.\n",
        )
        result = M.audit([doc])
        co = result["clause_overshoots"]
        # Confirm: no PCI/article entry is recorded.
        assert not any(
            e["regulation"] == "PCI" and e["clause"].startswith("Article")
            for e in co
        )

    def test_meta_block_reports_counts(self, fake_repo: Path) -> None:
        doc = _write_md(
            fake_repo,
            "docs/test.md",
            "# X\n\nUnknown FAKEREG2024 token. GDPR Article 124.\n",
        )
        result = M.audit([doc])
        meta = result["_meta"]
        assert meta["tool"] == "scripts/audit_doc_regulations.py"
        assert meta["schema"] == 1
        assert meta["docs_scanned"] == 1
        assert meta["unknown_acronyms"] == 1
        assert meta["clause_overshoots"] == 1

    def test_known_acronym_in_inline_code_not_counted(
        self, fake_repo: Path
    ) -> None:
        """``clean_prose`` strips inline ``code`` regions, so an
        acronym appearing only inside backticks must not be flagged."""
        doc = _write_md(
            fake_repo,
            "docs/test.md",
            "# X\n\nSee `FAKEREG2024` — the constant.\n",
        )
        result = M.audit([doc])
        assert "FAKEREG2024" not in result["unknown_acronyms"]

    def test_ignores_acronyms_under_4_chars(self, fake_repo: Path) -> None:
        """ACRONYM_RE bounds at 4-12 letters, so ``SOX`` (3 letters)
        is not a candidate — even though SOX is a real regulation, the
        regex is intentionally tight to avoid noise."""
        doc = _write_md(
            fake_repo,
            "docs/test.md",
            "# X\n\nSOX controls and III. references.\n",
        )
        result = M.audit([doc])
        assert "SOX" not in result["unknown_acronyms"]


# ---------------------------------------------------------------------------
# write_status
# ---------------------------------------------------------------------------


class TestWriteStatus:
    def test_creates_parent_dir_and_writes_pretty_json(
        self, fake_repo: Path
    ) -> None:
        # Remove the data dir to force mkdir(parents=True).
        data_dir = fake_repo / "data"
        for child in data_dir.iterdir():
            child.unlink()
        data_dir.rmdir()
        payload = {"_meta": {"docs_scanned": 5}, "x": 1}
        M.write_status(payload)
        text = M.STATUS_PATH.read_text(encoding="utf-8")
        assert text.endswith("\n")
        # Pretty-printed (indent=2) and key-sorted.
        loaded = json.loads(text)
        assert loaded == payload

    def test_writes_keys_in_sorted_order(self, fake_repo: Path) -> None:
        payload = {"z": 1, "a": 2, "m": 3}
        M.write_status(payload)
        text = M.STATUS_PATH.read_text(encoding="utf-8")
        # Sorted-key serialisation puts 'a' before 'm' before 'z'.
        assert text.find('"a"') < text.find('"m"') < text.find('"z"')


# ---------------------------------------------------------------------------
# summarise
# ---------------------------------------------------------------------------


class TestSummarise:
    def test_prints_empty_message_when_no_unknown(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        payload = {
            "_meta": {"docs_scanned": 3},
            "unknown_acronyms": {},
            "clause_overshoots": [],
        }
        M.summarise(payload, top=10)
        out = capsys.readouterr().out
        assert "Scanned 3 markdown files." in out
        assert "Unknown regulation-like acronyms: 0" in out
        # Empty branch wording.
        assert "(none — every acronym matched" in out

    def test_prints_top_n_acronyms_sorted_by_count(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        payload = {
            "_meta": {"docs_scanned": 1},
            "unknown_acronyms": {
                "FAKEA": {
                    "count": 5,
                    "samples": [{"path": "docs/a.md", "line": 1}],
                },
                "FAKEB": {
                    "count": 10,
                    "samples": [{"path": "docs/b.md", "line": 2}],
                },
                "FAKEC": {
                    "count": 1,
                    "samples": [{"path": "docs/c.md", "line": 3}],
                },
            },
            "clause_overshoots": [],
        }
        M.summarise(payload, top=2)
        out = capsys.readouterr().out
        # FAKEB (10) and FAKEA (5) are the top 2; FAKEC (1) drops.
        assert "FAKEB" in out
        assert "FAKEA" in out
        assert "FAKEC" not in out
        # Output ordering: highest count first.
        assert out.find("FAKEB") < out.find("FAKEA")

    def test_prints_clause_overshoots_with_sample_lines(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        payload = {
            "_meta": {"docs_scanned": 1},
            "unknown_acronyms": {},
            "clause_overshoots": [
                {
                    "path": "docs/x.md",
                    "line": 7,
                    "regulation": "GDPR",
                    "clause": "Article 124",
                    "max_documented": 99,
                    "raw": "GDPR Article 124",
                }
            ],
        }
        M.summarise(payload, top=10)
        out = capsys.readouterr().out
        assert "Clause-overshoot suspects" in out
        assert "docs/x.md:7" in out
        assert "GDPR Article 124" in out
        assert "max documented: 99" in out

    def test_caps_clause_overshoots_at_50_per_run(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        payload = {
            "_meta": {"docs_scanned": 1},
            "unknown_acronyms": {},
            "clause_overshoots": [
                {
                    "path": f"docs/file-{i}.md",
                    "line": i,
                    "regulation": "GDPR",
                    "clause": f"Article {i + 100}",
                    "max_documented": 99,
                    "raw": f"GDPR Article {i + 100}",
                }
                for i in range(60)
            ],
        }
        M.summarise(payload, top=10)
        out = capsys.readouterr().out
        # First and 50th present; 51st (file-50) absent because the
        # output is bounded by ``[:50]``.
        assert "docs/file-0.md" in out
        assert "docs/file-49.md" in out
        assert "docs/file-50.md" not in out

    def test_caps_acronym_samples_at_three_per_token(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Each unknown acronym shows at most 3 sample paths even if
        the entry stores 5 (line 386)."""
        payload = {
            "_meta": {"docs_scanned": 1},
            "unknown_acronyms": {
                "FAKE": {
                    "count": 5,
                    "samples": [
                        {"path": f"docs/f-{i}.md", "line": i + 1}
                        for i in range(5)
                    ],
                }
            },
            "clause_overshoots": [],
        }
        M.summarise(payload, top=10)
        out = capsys.readouterr().out
        # First three samples printed; 4th and 5th NOT.
        assert "docs/f-0.md:1" in out
        assert "docs/f-2.md:3" in out
        assert "docs/f-3.md:4" not in out
        assert "docs/f-4.md:5" not in out


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


class TestMain:
    def test_default_run_writes_status_file_and_returns_zero(
        self,
        fake_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _write_md(fake_repo, "docs/intro.md", "# Intro\n\nGDPR Article 5 baseline.\n")
        rc = M.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "Scanning" in out
        assert "Status written" in out
        # The status file MUST exist with valid JSON.
        text = M.STATUS_PATH.read_text(encoding="utf-8")
        loaded = json.loads(text)
        assert loaded["_meta"]["tool"] == "scripts/audit_doc_regulations.py"

    def test_top_argument_limits_summary(
        self,
        fake_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _write_md(
            fake_repo,
            "docs/intro.md",
            "# X\n\nFAKEA FAKEA FAKEA FAKEB FAKEC.\n",
        )
        rc = M.main(["--top", "1"])
        assert rc == 0
        out = capsys.readouterr().out
        # FAKEA (3 occurrences) printed; FAKEB and FAKEC (1 each)
        # dropped because --top=1.
        assert "FAKEA" in out
        # Both lower-count tokens absent from the printed summary.
        # We only check FAKEC because FAKEB and FAKEC have equal
        # counts (1 each) and Counter ordering is implementation-
        # dependent at ties.
        # …actually neither should appear given top=1.
        assert "FAKEB" not in out
        assert "FAKEC" not in out

    def test_main_returns_zero_when_no_docs_to_scan(
        self,
        fake_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Empty docs/ + no DEFAULT_EXTRA files.
        rc = M.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "Scanning 0 markdown files" in out
        # An empty audit still writes the status file.
        assert M.STATUS_PATH.exists()


# ---------------------------------------------------------------------------
# __main__ guard (line 413) — end-to-end script smoke test
# ---------------------------------------------------------------------------
#
# The naive ``runpy.run_path(scripts/audit_doc_regulations.py)`` approach
# would re-import the module fresh — losing the monkeypatch on ``REPO`` /
# ``CAT_DIR`` / ``STATUS_PATH`` — and call ``main()`` against the real
# repo, polluting ``data/doc-regulation-mentions.json``.
#
# The safe alternative below: copy the script into a fake repo rooted at
# ``tmp_path`` (so ``Path(__file__).resolve().parent.parent`` becomes
# ``tmp_path``) and runpy-exec that copy. ``main()`` writes its status
# file under ``tmp_path/data/doc-regulation-mentions.json`` and never
# touches the real repo.
#
# COVERAGE CAVEAT: ``coverage`` attributes hits by absolute file path, so
# this test exercises the ``__main__`` guard of the COPY — not the
# original. Line 413 of ``scripts/audit_doc_regulations.py`` therefore
# stays at "uncovered" in the per-file report (1 stmt / 137 = 99 %),
# but the actual CLI bootstrap contract IS exercised end-to-end here.
# Branch coverage on the original file is 100 % (48 / 48).
#
# Documented as an acceptable tradeoff: covering the original ``sys.exit
# (main())`` line would require running the script against the real
# repo, which is unsafe. This smoke test provides equivalent behavioural
# assurance without the side-effect risk.


class TestMainGuard:
    def test_runpy_invocation_executes_main(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import runpy
        import shutil
        import sys

        repo = tmp_path / "fake_repo"
        (repo / "docs").mkdir(parents=True)
        (repo / "content" / "cat-22-regulatory-compliance").mkdir(parents=True)
        (repo / "data").mkdir(parents=True)
        scripts_dir = repo / "scripts"
        scripts_dir.mkdir()

        real_script = (
            Path(__file__).resolve().parent.parent.parent
            / "scripts"
            / "audit_doc_regulations.py"
        )
        script_copy = scripts_dir / "audit_doc_regulations.py"
        shutil.copy(real_script, script_copy)

        (repo / "docs" / "trivial.md").write_text(
            "# trivial\n\nNo regulation tokens here.\n",
            encoding="utf-8",
        )

        # argparse defaults to ``sys.argv[1:]`` — clear it so pytest's own
        # CLI args (``-v``, paths, ``::``-selectors) don't leak into main().
        monkeypatch.setattr(sys, "argv", [str(script_copy)])

        with pytest.raises(SystemExit) as excinfo:
            runpy.run_path(str(script_copy), run_name="__main__")
        assert excinfo.value.code == 0

        status_file = repo / "data" / "doc-regulation-mentions.json"
        assert status_file.is_file()
        payload = json.loads(status_file.read_text(encoding="utf-8"))
        assert isinstance(payload.get("_meta"), dict)
        assert payload["_meta"]["tool"] == "scripts/audit_doc_regulations.py"
        assert isinstance(payload.get("unknown_acronyms"), dict)
        assert isinstance(payload.get("clause_overshoots"), list)
