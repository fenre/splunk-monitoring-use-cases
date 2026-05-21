"""Unit tests for ``scripts/generate_doc_references.py``.

Coverage philosophy:

* **Pure helpers** — exhaustive matrix tests against ``url_excluded``,
  ``normalize_url``, ``humanise_url``, ``strip_code_regions``,
  ``strip_autogen_block``, ``_resolve_accessed_date``,
  ``_scan_protected_spans`` / ``_in_protected``,
  ``_inline_marker_html``, ``render_citation``. These have no
  filesystem dependencies and are unit-testable directly.
* **Loaders** — ``load_library``, ``load_mappings``,
  ``load_inline_phrases`` are exercised by monkey-patching the
  module-level ``LIBRARY_PATH``, ``MAPPINGS_PATH``,
  ``INLINE_PHRASES_PATH`` to point at hermetic ``tmp_path`` fixtures.
* **Resolvers** — ``get_doc_mapping``, ``auto_resolve_keywords``,
  ``extract_additional_urls``, ``build_repo_graph``.
* **Renderers / appliers** — ``render_section``,
  ``inject_inline_citations``, ``apply_to_file`` against a synthetic
  doc tree under ``tmp_path``.
* **CLI** — ``main()`` is driven via ``argv`` lists; we exercise
  ``--validate-library`` (happy + dangling), ``--check`` (clean +
  drift), ``--dry-run``, ``--only`` (glob filter), ``SKIP`` set
  behaviour, and the default write path.

Hermeticism contract:

* Every test that touches the filesystem uses ``tmp_path``.
* Every test that depends on the *current* date is monkey-patched
  via ``SOURCE_REFS_ACCESSED_DATE`` or by clearing the
  ``_ACCESSED_DATE_RESOLVED`` cache.
* ``REPO`` and the four ``*_PATH`` module globals are re-rooted into
  ``tmp_path`` via the ``_patch_paths`` helper so the script never
  reads the real repository during the test run.
"""
from __future__ import annotations

import importlib
import json
import re
import sys
import types
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"


# ---------------------------------------------------------------------------
# Module loader — import generate_doc_references as a fresh module per test
# so module-level path globals can be monkey-patched cleanly without leaking
# state between cases.
# ---------------------------------------------------------------------------


@pytest.fixture()
def gdr(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    """Load the script as a module, ensuring a clean import each test."""
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    # Force a re-import so module-level constants (LIBRARY_PATH etc.) are
    # recomputed if the import cache is stale across runs.
    if "generate_doc_references" in sys.modules:
        del sys.modules["generate_doc_references"]
    module = importlib.import_module("generate_doc_references")
    # Reset the accessed-date cache between tests — otherwise tests that
    # depend on the resolved date may see stale state from a sibling.
    monkeypatch.setattr(module, "_ACCESSED_DATE_RESOLVED", None)
    return module


def _patch_paths(
    module: types.ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> dict[str, Path]:
    """Re-root all hard-coded filesystem paths into ``tmp_path``.

    Returns a dict of {logical_name: Path} for convenience.
    """
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    library = data_dir / "source-references.json"
    mappings = data_dir / "source-mappings.json"
    inline = data_dir / "inline-citation-phrases.json"
    monkeypatch.setattr(module, "REPO", tmp_path)
    monkeypatch.setattr(module, "LIBRARY_PATH", library)
    monkeypatch.setattr(module, "MAPPINGS_PATH", mappings)
    monkeypatch.setattr(module, "INLINE_PHRASES_PATH", inline)
    return {
        "repo": tmp_path,
        "data": data_dir,
        "library": library,
        "mappings": mappings,
        "inline": inline,
    }


def _seed_library(
    library_path: Path,
    *,
    records: dict[str, dict] | None = None,
    accessed: str | None = "2026-05-11",
) -> None:
    """Write a minimal but well-shaped library file."""
    payload: dict[str, Any] = {
        "_meta": {
            "schemaVersion": "1.0",
            "description": "test fixture",
        }
    }
    if accessed is not None:
        payload["_meta"]["accessedDate"] = accessed
    # 'splunk' section keeps the script's invariant ("non-underscore key
    # holds a dict of source records") truthful.
    payload["splunk"] = records or {
        "splunk-doc": {
            "authority": "Splunk Inc.",
            "year": 2026,
            "title": "Splunk Enterprise Documentation",
            "publisher": "Splunk LLC, a Cisco company",
            "type": "documentation",
            "url": "https://docs.splunk.com/Documentation/Splunk",
        },
    }
    library_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _seed_mappings(
    mappings_path: Path,
    *,
    docs: dict[str, dict[str, list[str]]] | None = None,
    keywords: dict[str, list[str]] | None = None,
) -> None:
    payload: dict[str, Any] = {
        "_meta": {"description": "test fixture"},
    }
    if keywords is not None:
        payload["_topic_keywords"] = dict(keywords, _comment="ignore me")
    for doc, mapping in (docs or {}).items():
        payload[doc] = mapping
    mappings_path.write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )


def _seed_inline_phrases(
    inline_path: Path,
    payload: dict[str, list[str]] | None,
) -> None:
    if payload is None:
        return  # caller wants the file absent
    obj: dict[str, Any] = {"_meta": {"description": "test fixture"}}
    obj.update(payload)
    inline_path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Module-level constants and regexes.
# ---------------------------------------------------------------------------


class TestModuleConstants:
    def test_marker_strings_are_html_comments(
        self, gdr: types.ModuleType
    ) -> None:
        assert gdr.BEGIN_MARKER.startswith("<!--")
        assert gdr.END_MARKER.startswith("<!--")
        assert gdr.BEGIN_MARKER != gdr.END_MARKER

    def test_section_headings_use_h2_h3(
        self, gdr: types.ModuleType
    ) -> None:
        assert gdr.SECTION_HEADING.startswith("## ")
        assert gdr.SUBSECTION_PRIMARY.startswith("### ")
        assert gdr.SUBSECTION_SUPPORTING.startswith("### ")
        assert gdr.SUBSECTION_ADDITIONAL.startswith("### ")
        assert gdr.SUBSECTION_REPO_OUT.startswith("### ")
        assert gdr.SUBSECTION_REPO_IN.startswith("### ")

    def test_max_auto_supporting_is_a_positive_int(
        self, gdr: types.ModuleType
    ) -> None:
        assert isinstance(gdr.MAX_AUTO_SUPPORTING, int)
        assert gdr.MAX_AUTO_SUPPORTING > 0

    def test_max_repo_links_per_direction_is_positive(
        self, gdr: types.ModuleType
    ) -> None:
        assert isinstance(gdr.MAX_REPO_LINKS_PER_DIRECTION, int)
        assert gdr.MAX_REPO_LINKS_PER_DIRECTION > 0

    def test_skip_set_includes_known_generated_pages(
        self, gdr: types.ModuleType
    ) -> None:
        # These are pages whose body is rewritten by other scripts; we
        # must never glue a References footer onto them.
        for known in [
            "docs/backlinks.md",
            "CHANGELOG.md",
            "VERSION",
            "docs/compliance-coverage.md",
            "docs/compliance-gaps.md",
            "docs/provenance-coverage.md",
            "docs/scorecard.md",
            "docs/splunk-cloud-compat.md",
            "docs/samples-coverage.md",
            "docs/license-inventory.md",
            "docs/uc-migration-report.md",
        ]:
            assert known in gdr.SKIP

    def test_url_exclude_patterns_match_known_noise(
        self, gdr: types.ModuleType
    ) -> None:
        noise = [
            "https://img.shields.io/badge/foo",
            "https://example.com/x",
            "http://localhost:8080",
            "http://127.0.0.1/test",
            "http://[2001:db8::1]/api",
            "https://yourdomain.tld/foo",
        ]
        for url in noise:
            assert any(
                re.match(pat, url) for pat in gdr.URL_EXCLUDE_PATTERNS
            ), f"expected {url!r} to match an exclude pattern"


class TestRegexes:
    def test_link_re_captures_label_and_url(
        self, gdr: types.ModuleType
    ) -> None:
        m = gdr.LINK_RE.search("see [foo](https://example.com/x)")
        assert m is not None
        assert m.group(1) == "foo"
        assert m.group(2) == "https://example.com/x"

    def test_any_link_re_matches_relative_targets(
        self, gdr: types.ModuleType
    ) -> None:
        m = gdr.ANY_LINK_RE.search("[doc](other.md)")
        assert m is not None
        assert m.group(2) == "other.md"

    def test_url_re_does_not_bleed_across_parens(
        self, gdr: types.ModuleType
    ) -> None:
        # Reproduces the historical [label](url](url) bug — the bare-
        # URL pattern must not slurp the `)` or `(`.
        matches = list(
            gdr.URL_RE.finditer(
                "see [docs](https://example.com/x) and "
                "https://example.com/y inline"
            )
        )
        urls = [m.group(0) for m in matches]
        # Both the markdown-link URL and the bare URL appear, but
        # neither contains parens.
        assert all("(" not in u and ")" not in u for u in urls)

    def test_marker_block_re_is_dotall(
        self, gdr: types.ModuleType
    ) -> None:
        body = f"prefix\n{gdr.BEGIN_MARKER}\nx\ny\n{gdr.END_MARKER}\nsuffix"
        assert gdr.MARKER_BLOCK_RE.search(body) is not None

    def test_inline_cite_re_matches_canonical_marker(
        self, gdr: types.ModuleType
    ) -> None:
        marker = '<sup class="ref">[<a href="#ref-7">7</a>]</sup>'
        assert gdr.INLINE_CITE_RE.fullmatch(marker) is not None
        # Should NOT match a sup without the class attribute.
        assert not gdr.INLINE_CITE_RE.search(
            '<sup>[<a href="#ref-7">7</a>]</sup>'
        )


# ---------------------------------------------------------------------------
# Library / mapping / inline-phrase loaders.
# ---------------------------------------------------------------------------


class TestLoadLibrary:
    def test_returns_flat_records_with_section_metadata(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        paths = _patch_paths(gdr, monkeypatch, tmp_path)
        _seed_library(
            paths["library"],
            records={
                "alpha": {"title": "A", "url": "https://a.example/"},
                "beta": {"title": "B"},
            },
        )
        flat, accessed = gdr.load_library()
        assert set(flat) == {"alpha", "beta"}
        # Section metadata is enriched onto every record.
        assert flat["alpha"]["_section"] == "splunk"
        assert flat["alpha"]["_id"] == "alpha"
        assert flat["alpha"]["url"] == "https://a.example/"
        assert accessed == "2026-05-11"

    def test_returns_none_accessed_when_meta_missing(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        paths = _patch_paths(gdr, monkeypatch, tmp_path)
        _seed_library(paths["library"], accessed=None)
        _, accessed = gdr.load_library()
        assert accessed is None

    def test_raises_on_duplicate_source_id_across_sections(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        paths = _patch_paths(gdr, monkeypatch, tmp_path)
        payload = {
            "_meta": {"accessedDate": "2026-05-11"},
            "splunk": {"shared-id": {"title": "X"}},
            "vendor": {"shared-id": {"title": "Y"}},
        }
        paths["library"].write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )
        with pytest.raises(ValueError, match="Duplicate source-reference id"):
            gdr.load_library()

    def test_skips_underscore_prefixed_top_level_sections(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Sections like ``_meta`` and ``_schema`` must NOT contribute
        records — they're metadata, not bibliographic entries.
        """
        paths = _patch_paths(gdr, monkeypatch, tmp_path)
        payload = {
            "_meta": {"accessedDate": "2026-05-11", "should-skip": {"title": "Z"}},
            "_schema": {"never": {"title": "N"}},
            "real": {"only-real": {"title": "R"}},
        }
        paths["library"].write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )
        flat, _ = gdr.load_library()
        assert set(flat) == {"only-real"}


class TestLoadMappings:
    def test_extracts_keywords_and_drops_meta(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        paths = _patch_paths(gdr, monkeypatch, tmp_path)
        _seed_mappings(
            paths["mappings"],
            docs={"docs/foo.md": {"primary": ["x"]}},
            keywords={"SPL": ["spl"]},
        )
        mappings, keywords = gdr.load_mappings()
        assert "docs/foo.md" in mappings
        assert mappings["docs/foo.md"]["primary"] == ["x"]
        # The ``_comment`` siphon at the keywords level is stripped.
        assert "_comment" not in keywords
        assert keywords["SPL"] == ["spl"]

    def test_keywords_default_to_empty_when_not_a_dict(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """If ``_topic_keywords`` is a non-dict (legacy / malformed),
        ``load_mappings`` falls back to ``{}`` rather than crashing.
        """
        paths = _patch_paths(gdr, monkeypatch, tmp_path)
        payload = {
            "_topic_keywords": "not-a-dict",
            "docs/foo.md": {"primary": ["x"]},
        }
        paths["mappings"].write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )
        mappings, keywords = gdr.load_mappings()
        assert keywords == {}
        assert "docs/foo.md" in mappings

    def test_strips_underscore_prefixed_keys_from_mappings(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        paths = _patch_paths(gdr, monkeypatch, tmp_path)
        payload = {
            "_meta": {"foo": "bar"},
            "_topic_keywords": {},
            "_section_a_comment": "drop me",
            "docs/real.md": {"primary": ["x"]},
        }
        paths["mappings"].write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )
        mappings, _ = gdr.load_mappings()
        assert list(mappings.keys()) == ["docs/real.md"]


class TestLoadInlinePhrases:
    def test_returns_empty_dict_when_file_missing(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        paths = _patch_paths(gdr, monkeypatch, tmp_path)
        # Explicitly do NOT seed the inline file.
        assert not paths["inline"].exists()
        assert gdr.load_inline_phrases() == {}

    def test_drops_meta_block_and_keeps_list_values_only(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        paths = _patch_paths(gdr, monkeypatch, tmp_path)
        paths["inline"].write_text(
            json.dumps(
                {
                    "_meta": {"description": "x"},
                    "valid-sid": ["phrase one", "phrase two"],
                    "invalid-sid": "not a list",  # should be dropped
                    "another-sid": ["only phrase"],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        out = gdr.load_inline_phrases()
        assert set(out) == {"valid-sid", "another-sid"}
        assert out["valid-sid"] == ["phrase one", "phrase two"]
        assert out["another-sid"] == ["only phrase"]


# ---------------------------------------------------------------------------
# collect_md_nodes
# ---------------------------------------------------------------------------


class TestCollectMdNodes:
    def test_scans_docs_subtree_and_extras(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        _patch_paths(gdr, monkeypatch, tmp_path)
        # docs/ subtree (nested)
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "alpha.md").write_text("# Alpha", encoding="utf-8")
        (tmp_path / "docs" / "nested").mkdir()
        (tmp_path / "docs" / "nested" / "beta.md").write_text(
            "# Beta", encoding="utf-8"
        )
        # An extra at the repo root.
        (tmp_path / "README.md").write_text("# Readme", encoding="utf-8")
        (tmp_path / "AGENTS.md").write_text("# Agents", encoding="utf-8")
        # Extra not present on disk — must NOT appear in the result.
        # (No file written for CONTRIBUTING.md.)
        out = gdr.collect_md_nodes()
        out_rel = sorted(str(p.relative_to(tmp_path)) for p in out)
        # We expect at least these three paths to be present.
        assert "docs/alpha.md" in out_rel
        assert "docs/nested/beta.md" in out_rel
        assert "README.md" in out_rel
        assert "AGENTS.md" in out_rel
        # And we MUST NOT see CONTRIBUTING.md because it's not on disk.
        assert "CONTRIBUTING.md" not in out_rel

    def test_deduplicates_with_resolved_paths(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """If an extra is also picked up by the ``docs/`` glob, the
        ``sorted({p.resolve() for p in nodes})`` step ensures we only
        emit one entry per real file.
        """
        _patch_paths(gdr, monkeypatch, tmp_path)
        (tmp_path / "docs").mkdir()
        # Same path that happens to also be listed in the explicit extras.
        # The dedup happens via resolved-path set comprehension.
        (tmp_path / "README.md").write_text("hello", encoding="utf-8")
        out = gdr.collect_md_nodes()
        # README.md should be present exactly once.
        readmes = [p for p in out if p.name == "README.md"]
        assert len(readmes) == 1


# ---------------------------------------------------------------------------
# strip_code_regions / strip_autogen_block
# ---------------------------------------------------------------------------


class TestStripCodeRegions:
    def test_removes_fenced_code_blocks(
        self, gdr: types.ModuleType
    ) -> None:
        body = (
            "before\n"
            "```python\n"
            "x = 1\n"
            "y = 2\n"
            "```\n"
            "after\n"
        )
        out = gdr.strip_code_regions(body)
        assert "x = 1" not in out
        assert "y = 2" not in out
        assert "before" in out
        assert "after" in out

    def test_removes_inline_code_spans(
        self, gdr: types.ModuleType
    ) -> None:
        body = "intro `rm -rf /` and trailing `secret` text"
        out = gdr.strip_code_regions(body)
        assert "rm -rf" not in out
        assert "secret" not in out
        assert "intro" in out and "trailing" in out

    def test_handles_indented_fenced_blocks(
        self, gdr: types.ModuleType
    ) -> None:
        body = "\n   ```\nfoo\n   ```\nbar\n"
        out = gdr.strip_code_regions(body)
        assert "foo" not in out
        assert "bar" in out

    def test_preserves_unfenced_content(
        self, gdr: types.ModuleType
    ) -> None:
        body = "this is regular prose with no fences"
        assert gdr.strip_code_regions(body) == body


class TestStripAutogenBlock:
    def test_removes_marked_section(
        self, gdr: types.ModuleType
    ) -> None:
        body = (
            "prefix\n"
            + gdr.BEGIN_MARKER
            + "\nold-content\n"
            + gdr.END_MARKER
            + "\nsuffix"
        )
        out = gdr.strip_autogen_block(body)
        assert "old-content" not in out
        assert "prefix" in out and "suffix" in out

    def test_passthrough_when_no_markers_present(
        self, gdr: types.ModuleType
    ) -> None:
        body = "no markers here"
        assert gdr.strip_autogen_block(body) == body


# ---------------------------------------------------------------------------
# URL hygiene helpers.
# ---------------------------------------------------------------------------


class TestUrlExcluded:
    @pytest.mark.parametrize(
        "url",
        [
            "https://img.shields.io/badge/version",
            "https://example.com/x",
            "https://localhost:8080",
            "https://127.0.0.1/test",
            "https://[2001:db8::1]/api",
            "https://yourdomain.tld/foo",
        ],
    )
    def test_known_noise_urls_excluded(
        self, gdr: types.ModuleType, url: str
    ) -> None:
        assert gdr.url_excluded(url) is True

    @pytest.mark.parametrize(
        "url",
        [
            "https://docs.splunk.com/Documentation/Splunk",
            "https://attack.mitre.org/techniques/T1059",
            "https://www.iso.org/standard/82875.html",
            "https://github.com/example/repo",
        ],
    )
    def test_real_urls_pass_through(
        self, gdr: types.ModuleType, url: str
    ) -> None:
        assert gdr.url_excluded(url) is False


class TestNormalizeUrl:
    @pytest.mark.parametrize(
        ("inp", "out"),
        [
            ("https://x.com/a.", "https://x.com/a"),
            ("https://x.com/a,", "https://x.com/a"),
            ("https://x.com/a;", "https://x.com/a"),
            ("https://x.com/a:", "https://x.com/a"),
            ("https://x.com/a!", "https://x.com/a"),
            ("https://x.com/a?", "https://x.com/a"),
            ('https://x.com/a"', "https://x.com/a"),
            ("https://x.com/a'", "https://x.com/a"),
            ("https://x.com/a>", "https://x.com/a"),
        ],
    )
    def test_strips_known_trailing_punctuation(
        self, gdr: types.ModuleType, inp: str, out: str
    ) -> None:
        assert gdr.normalize_url(inp) == out

    def test_strips_unbalanced_trailing_parens(
        self, gdr: types.ModuleType
    ) -> None:
        # One ``)`` without a matching ``(`` → strip it.
        assert (
            gdr.normalize_url("https://x.com/a)")
            == "https://x.com/a"
        )
        # Multiple unbalanced parens should still resolve to a clean URL.
        assert (
            gdr.normalize_url("https://x.com/a))")
            == "https://x.com/a"
        )

    def test_keeps_balanced_trailing_parens(
        self, gdr: types.ModuleType
    ) -> None:
        # Wikipedia-style: ``(disambiguation)`` is preserved when
        # balanced.
        assert (
            gdr.normalize_url("https://en.wikipedia.org/wiki/Foo_(bar)")
            == "https://en.wikipedia.org/wiki/Foo_(bar)"
        )

    def test_returns_unchanged_when_already_clean(
        self, gdr: types.ModuleType
    ) -> None:
        assert (
            gdr.normalize_url("https://x.com/a")
            == "https://x.com/a"
        )


class TestHumaniseUrl:
    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            (
                "https://attack.mitre.org/techniques/T1059",
                "MITRE ATT&CK Technique T1059",
            ),
            (
                "https://attack.mitre.org/techniques/T1059.001",
                "MITRE ATT&CK Technique T1059.001",
            ),
            (
                "https://attack.mitre.org/tactics/TA0001",
                "MITRE ATT&CK Tactic TA0001",
            ),
            (
                "https://attack.mitre.org/groups/G0007",
                "MITRE ATT&CK Group G0007",
            ),
            (
                "https://attack.mitre.org/",
                "MITRE ATT&CK Knowledge Base",
            ),
        ],
    )
    def test_mitre_attack_branches(
        self,
        gdr: types.ModuleType,
        url: str,
        expected: str,
    ) -> None:
        assert gdr.humanise_url(url) == expected

    def test_d3fend(self, gdr: types.ModuleType) -> None:
        out = gdr.humanise_url("https://d3fend.mitre.org/technique/example")
        assert "MITRE D3FEND" in out

    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            ("https://www.rfc-editor.org/rfc/rfc8259", "IETF RFC 8259"),
            ("https://datatracker.ietf.org/doc/html/rfc7159", "IETF RFC 7159"),
            ("https://tools.ietf.org/html/rfc1234", "IETF RFC 1234"),
        ],
    )
    def test_rfc_branches(
        self, gdr: types.ModuleType, url: str, expected: str
    ) -> None:
        assert gdr.humanise_url(url) == expected

    def test_splunkbase_app(self, gdr: types.ModuleType) -> None:
        out = gdr.humanise_url(
            "https://splunkbase.splunk.com/app/2734/"
        )
        assert "Splunkbase app #2734" == out

    def test_splunkbase_root(self, gdr: types.ModuleType) -> None:
        assert (
            gdr.humanise_url("https://splunkbase.splunk.com/")
            == "Splunkbase"
        )

    def test_splunk_docs_with_version(self, gdr: types.ModuleType) -> None:
        out = gdr.humanise_url(
            "https://docs.splunk.com/Documentation/Splunk/9.2/Search/About"
        )
        assert "Splunk" in out and "9.2" in out

    def test_splunk_docs_strips_latest_version(
        self, gdr: types.ModuleType
    ) -> None:
        out = gdr.humanise_url(
            "https://docs.splunk.com/Documentation/Splunk/latest/Search/About"
        )
        assert "latest" not in out

    def test_splunk_observability(self, gdr: types.ModuleType) -> None:
        out = gdr.humanise_url(
            "https://docs.splunk.com/observability/en/admin/admin.html"
        )
        assert out.startswith("Splunk Observability")

    def test_splunk_lantern(self, gdr: types.ModuleType) -> None:
        out = gdr.humanise_url(
            "https://lantern.splunk.com/Foo_Bar_Article"
        )
        assert out.startswith("Splunk Lantern")

    def test_nist_sp_in_path(self, gdr: types.ModuleType) -> None:
        # The SP-detection regex is ``SP\s*\d+-\d+[A-Z]?`` — it matches
        # both ``SP 800-53`` (space) and ``SP800-53`` (no space).
        out = gdr.humanise_url(
            "https://csrc.nist.gov/projects/risk-management/sp800-53"
        )
        assert "NIST sp800-53".upper() in out.upper()

    def test_nist_sp_with_revision_suffix(
        self, gdr: types.ModuleType
    ) -> None:
        # The fragment is included in the regex's search corpus, so the
        # ``#sp-800-53`` style anchor also matches.
        out = gdr.humanise_url(
            "https://csrc.nist.gov/publications#SP800-53A"
        )
        assert "NIST" in out and "800-53" in out.upper()

    def test_nist_sp_falls_to_default_when_not_matchable(
        self, gdr: types.ModuleType
    ) -> None:
        # The path uses ``/sp/`` as a directory token — the regex
        # requires ``SP`` immediately followed by ``\s*\d`` so this
        # does NOT match and the default branch fires.
        out = gdr.humanise_url(
            "https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final"
        )
        # Default branch produces ``NIST: <humanised-last-segment>``.
        assert out.startswith("NIST:")

    def test_nist_cyberframework(self, gdr: types.ModuleType) -> None:
        out = gdr.humanise_url(
            "https://www.nist.gov/cyberframework"
        )
        assert "NIST Cybersecurity Framework" in out

    def test_nist_default(self, gdr: types.ModuleType) -> None:
        out = gdr.humanise_url(
            "https://www.nist.gov/some/random/page"
        )
        assert out.startswith("NIST:")

    def test_iso_with_number(self, gdr: types.ModuleType) -> None:
        out = gdr.humanise_url("https://www.iso.org/standard/82875.html")
        assert "ISO/IEC 82875" == out

    def test_iso_root(self, gdr: types.ModuleType) -> None:
        out = gdr.humanise_url("https://www.iso.org/")
        assert out == "ISO/IEC standard"

    def test_eurlex_regulation(self, gdr: types.ModuleType) -> None:
        out = gdr.humanise_url(
            "https://eur-lex.europa.eu/eli/reg/2016/679/oj"
        )
        assert out == "EU Regulation 2016/679"

    def test_eurlex_directive(self, gdr: types.ModuleType) -> None:
        out = gdr.humanise_url(
            "https://eur-lex.europa.eu/eli/dir/2022/2555/oj"
        )
        assert out == "EU Directive 2022/2555"

    def test_eurlex_decision(self, gdr: types.ModuleType) -> None:
        out = gdr.humanise_url(
            "https://eur-lex.europa.eu/eli/dec/2010/87/oj"
        )
        assert out == "EU Decision 2010/87"

    def test_eurlex_default(self, gdr: types.ModuleType) -> None:
        out = gdr.humanise_url(
            "https://eur-lex.europa.eu/legal-content/EN/other-page"
        )
        assert out.startswith("EUR-Lex:")

    def test_legislation_gov_uk_act(self, gdr: types.ModuleType) -> None:
        out = gdr.humanise_url(
            "https://www.legislation.gov.uk/ukpga/2018/12/contents"
        )
        assert out == "UK Legislation 2018 c. 12"

    def test_legislation_gov_uk_default(
        self, gdr: types.ModuleType
    ) -> None:
        out = gdr.humanise_url(
            "https://www.legislation.gov.uk/landing-page"
        )
        assert out.startswith("UK Legislation:")

    def test_pcaob_as2201(self, gdr: types.ModuleType) -> None:
        out = gdr.humanise_url(
            "https://pcaobus.org/oversight/standards/auditing-standards/details/AS2201"
        )
        assert out == "PCAOB AS 2201"

    def test_pcaob_default(self, gdr: types.ModuleType) -> None:
        out = gdr.humanise_url("https://pcaobus.org/other-thing")
        assert out.startswith("PCAOB:")

    def test_sec(self, gdr: types.ModuleType) -> None:
        out = gdr.humanise_url("https://www.sec.gov/rules/final/2023/123.htm")
        assert out.startswith("U.S. SEC:")

    def test_hhs(self, gdr: types.ModuleType) -> None:
        out = gdr.humanise_url("https://www.hhs.gov/hipaa/guidance.html")
        assert out.startswith("U.S. HHS:")

    def test_ftc(self, gdr: types.ModuleType) -> None:
        out = gdr.humanise_url("https://www.ftc.gov/business-guidance/x")
        assert out.startswith("U.S. FTC:")

    def test_aicpa(self, gdr: types.ModuleType) -> None:
        out = gdr.humanise_url(
            "https://www.aicpa.org/topic/audit-and-attestation"
        )
        assert out.startswith("AICPA:")

    def test_pci_ssc(self, gdr: types.ModuleType) -> None:
        out = gdr.humanise_url(
            "https://www.pcisecuritystandards.org/document_library"
        )
        assert out.startswith("PCI SSC:")

    def test_owasp(self, gdr: types.ModuleType) -> None:
        out = gdr.humanise_url(
            "https://owasp.org/www-project-top-ten/"
        )
        assert out.startswith("OWASP:")

    def test_cisa(self, gdr: types.ModuleType) -> None:
        out = gdr.humanise_url(
            "https://www.cisa.gov/news-events/cybersecurity-advisories"
        )
        assert out.startswith("CISA:")

    def test_github_org_repo(self, gdr: types.ModuleType) -> None:
        out = gdr.humanise_url("https://github.com/splunk/splunk-sdk-python")
        assert out == "GitHub: splunk/splunk-sdk-python"

    def test_github_org_only(self, gdr: types.ModuleType) -> None:
        out = gdr.humanise_url("https://github.com/splunk")
        assert out == "GitHub: splunk"

    def test_github_root(self, gdr: types.ModuleType) -> None:
        out = gdr.humanise_url("https://github.com/")
        assert out == "GitHub"

    @pytest.mark.parametrize(
        ("url", "expected_prefix"),
        [
            (
                "https://learn.microsoft.com/en-us/azure/active-directory/x",
                "Microsoft Learn:",
            ),
            ("https://docs.aws.amazon.com/IAM/latest/UserGuide/x.html", "AWS Documentation:"),
            ("https://aws.amazon.com/some/page", "AWS:"),
            ("https://cloud.google.com/docs/some-page", "Google Cloud:"),
            ("https://kubernetes.io/docs/concepts/x/", "Kubernetes:"),
            ("https://www.cisco.com/c/en/us/products/x.html", "Cisco:"),
            ("https://www.crowdstrike.com/products/some-page", "CrowdStrike:"),
            ("https://www.okta.com/products/oie/page", "Okta:"),
            ("https://opentelemetry.io/docs/x", "OpenTelemetry:"),
            ("https://modelcontextprotocol.io/spec/x", "Model Context Protocol:"),
        ],
    )
    def test_vendor_branches(
        self,
        gdr: types.ModuleType,
        url: str,
        expected_prefix: str,
    ) -> None:
        out = gdr.humanise_url(url)
        assert out.startswith(expected_prefix), out

    def test_pure_host_fallback_with_tail(
        self, gdr: types.ModuleType
    ) -> None:
        out = gdr.humanise_url("https://random.example.org/some/page")
        # Should be "random.example.org: Some Page" or similar.
        assert "random.example.org" in out
        assert ":" in out

    def test_pure_host_fallback_root_only(
        self, gdr: types.ModuleType
    ) -> None:
        out = gdr.humanise_url("https://random.example.org/")
        assert "random.example.org" in out

    def test_strips_www_prefix(self, gdr: types.ModuleType) -> None:
        # www.foo.com → foo.com in the fallback label.
        out = gdr.humanise_url("https://www.unknown-site.com/")
        assert "unknown-site.com" in out
        assert "www." not in out


# ---------------------------------------------------------------------------
# get_doc_mapping / auto_resolve_keywords / extract_additional_urls
# ---------------------------------------------------------------------------


class TestGetDocMapping:
    def test_exact_path_match(self, gdr: types.ModuleType) -> None:
        mappings = {"docs/foo.md": {"primary": ["a"]}}
        assert gdr.get_doc_mapping("docs/foo.md", mappings) == {
            "primary": ["a"]
        }

    def test_short_key_match_for_docs_prefix(
        self, gdr: types.ModuleType
    ) -> None:
        mappings = {"foo.md": {"primary": ["a"]}}
        # docs/foo.md → also resolves via the short ``foo.md`` key.
        assert gdr.get_doc_mapping("docs/foo.md", mappings) == {
            "primary": ["a"]
        }

    def test_repo_root_files_do_not_use_short_key_fallback(
        self, gdr: types.ModuleType
    ) -> None:
        mappings = {"foo.md": {"primary": ["a"]}}
        assert gdr.get_doc_mapping("foo.md", mappings) == {"primary": ["a"]}
        # But README.md does NOT pick up mappings stored under "README.md"
        # via the docs/ short-key path (it just hits the exact match).
        # Equally, an unrelated repo-root key with a non-existent short
        # key returns {}.
        assert gdr.get_doc_mapping("other.md", mappings) == {}

    def test_returns_empty_dict_when_no_match(
        self, gdr: types.ModuleType
    ) -> None:
        assert gdr.get_doc_mapping("docs/missing.md", {}) == {}


class TestAutoResolveKeywords:
    def test_returns_source_ids_in_first_encountered_order(
        self, gdr: types.ModuleType
    ) -> None:
        body = "we use SPL and the CIM data model for normalisation."
        keywords = {"SPL": ["spl-ref"], "CIM": ["cim-ref"]}
        out = gdr.auto_resolve_keywords(body, keywords)
        # First-match-wins per term order (dict-insertion-order in
        # Python 3.7+).
        assert out == ["spl-ref", "cim-ref"]

    def test_case_insensitive_and_word_bounded(
        self, gdr: types.ModuleType
    ) -> None:
        # ``spl`` lowercase matches; ``cimpler`` does NOT match ``CIM``.
        body = "spl is everywhere; cimpler is unrelated."
        keywords = {"SPL": ["spl-ref"], "CIM": ["cim-ref"]}
        out = gdr.auto_resolve_keywords(body, keywords)
        assert out == ["spl-ref"]

    def test_returns_empty_when_no_terms_match(
        self, gdr: types.ModuleType
    ) -> None:
        body = "nothing relevant here."
        assert gdr.auto_resolve_keywords(body, {"X": ["x-ref"]}) == []

    def test_multiple_source_ids_per_term_emitted_once(
        self, gdr: types.ModuleType
    ) -> None:
        body = "MITRE ATT&CK is foundational."
        keywords = {"MITRE ATT&CK": ["mitre-ref", "mitre-att-ref"]}
        out = gdr.auto_resolve_keywords(body, keywords)
        assert out == ["mitre-ref", "mitre-att-ref"]

    def test_terms_with_punctuation_are_not_word_bounded(
        self, gdr: types.ModuleType
    ) -> None:
        # ``ISO/IEC 27001`` contains punctuation — the script uses a
        # specially-relaxed boundary to allow these.
        body = "see ISO/IEC 27001 for the framework."
        keywords = {"ISO/IEC 27001": ["iso-27001-ref"]}
        out = gdr.auto_resolve_keywords(body, keywords)
        assert out == ["iso-27001-ref"]


class TestExtractAdditionalUrls:
    def test_markdown_link_with_useful_label_kept(
        self, gdr: types.ModuleType
    ) -> None:
        body = "see [Splunk Documentation](https://docs.splunk.com/Documentation/Splunk)"
        out = gdr.extract_additional_urls(body, set())
        assert (
            "https://docs.splunk.com/Documentation/Splunk" in out
        )
        assert (
            out["https://docs.splunk.com/Documentation/Splunk"]
            == "Splunk Documentation"
        )

    def test_markdown_link_with_single_slug_label_falls_back_to_humanise(
        self, gdr: types.ModuleType
    ) -> None:
        body = "see [contents](https://notes.example.org/foo)"
        out = gdr.extract_additional_urls(body, set())
        # "contents" matches the single-slug junk pattern — humaniser
        # kicks in instead of taking "contents" as the label.
        assert (
            out["https://notes.example.org/foo"] != "contents"
        )

    def test_markdown_link_with_url_as_label(
        self, gdr: types.ModuleType
    ) -> None:
        body = (
            "see [https://notes.example.org/foo]"
            "(https://notes.example.org/foo)"
        )
        out = gdr.extract_additional_urls(body, set())
        assert "https://notes.example.org/foo" in out
        # URL-as-label → humaniser is used (output never starts with
        # "http").
        assert not out["https://notes.example.org/foo"].startswith("http")

    def test_excluded_urls_are_dropped(
        self, gdr: types.ModuleType
    ) -> None:
        body = "[badge](https://img.shields.io/badge/v/1.0)"
        out = gdr.extract_additional_urls(body, set())
        assert out == {}

    def test_covered_urls_are_dropped(
        self, gdr: types.ModuleType
    ) -> None:
        body = "[doc](https://notes.example.org/foo)"
        covered = {"https://notes.example.org/foo"}
        out = gdr.extract_additional_urls(body, covered)
        assert out == {}

    def test_bare_urls_picked_up(
        self, gdr: types.ModuleType
    ) -> None:
        body = "Reference: https://notes.example.org/bare-url in passing."
        out = gdr.extract_additional_urls(body, set())
        assert "https://notes.example.org/bare-url" in out

    def test_dedupes_same_url_seen_twice(
        self, gdr: types.ModuleType
    ) -> None:
        body = (
            "first [Good Label](https://notes.example.org/foo) "
            "second https://notes.example.org/foo"
        )
        out = gdr.extract_additional_urls(body, set())
        assert list(out.keys()).count("https://notes.example.org/foo") == 1
        assert out["https://notes.example.org/foo"] == "Good Label"

    def test_strips_bold_italic_noise_from_label(
        self, gdr: types.ModuleType
    ) -> None:
        body = "see [**Splunk Docs**](https://notes.example.org/clean-it)"
        out = gdr.extract_additional_urls(body, set())
        assert out["https://notes.example.org/clean-it"] == "Splunk Docs"

    def test_url_fragment_deduped_against_covered(
        self, gdr: types.ModuleType
    ) -> None:
        # Covered = no fragment; body link = with fragment. They should
        # collapse to one entry because urldefrag is applied.
        body = "[anchor](https://notes.example.org/foo#section)"
        covered = {"https://notes.example.org/foo"}
        out = gdr.extract_additional_urls(body, covered)
        assert out == {}


# ---------------------------------------------------------------------------
# build_repo_graph
# ---------------------------------------------------------------------------


class TestBuildRepoGraph:
    def test_builds_in_out_link_maps(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        _patch_paths(gdr, monkeypatch, tmp_path)
        a = tmp_path / "docs" / "a.md"
        b = tmp_path / "docs" / "b.md"
        a.parent.mkdir(parents=True, exist_ok=True)
        a.write_text("# A\nSee [B](b.md) for details.", encoding="utf-8")
        b.write_text("# B\nNothing here.", encoding="utf-8")
        outs, ins = gdr.build_repo_graph([a, b])
        assert "docs/b.md" in outs["docs/a.md"]
        assert "docs/a.md" in ins["docs/b.md"]

    def test_skips_self_links(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        _patch_paths(gdr, monkeypatch, tmp_path)
        a = tmp_path / "docs" / "a.md"
        a.parent.mkdir(parents=True, exist_ok=True)
        a.write_text("# A\nSee [A](a.md).", encoding="utf-8")
        outs, ins = gdr.build_repo_graph([a])
        assert outs == {} or "docs/a.md" not in outs.get("docs/a.md", set())
        assert ins == {} or "docs/a.md" not in ins.get("docs/a.md", set())

    def test_skips_external_and_non_md_targets(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        _patch_paths(gdr, monkeypatch, tmp_path)
        a = tmp_path / "docs" / "a.md"
        a.parent.mkdir(parents=True, exist_ok=True)
        a.write_text(
            "# A\n"
            "[ext](https://notes.example.org/x)\n"
            "[mailto](mailto:foo@notes.example.org)\n"
            "[file](file:///etc/passwd)\n"
            "[protocol-rel](//notes.example.org/x)\n"
            "[png](image.png)\n"
            "[missing](does-not-exist.md)\n",
            encoding="utf-8",
        )
        outs, ins = gdr.build_repo_graph([a])
        # No internal links should resolve.
        assert outs.get("docs/a.md", set()) == set()
        assert ins == {} or all(not s for s in ins.values())

    def test_skips_links_inside_autogen_block(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Body-strip should remove the auto-generated footer before
        scanning — so a link inside the footer should NOT count as an
        in/out edge.
        """
        _patch_paths(gdr, monkeypatch, tmp_path)
        a = tmp_path / "docs" / "a.md"
        b = tmp_path / "docs" / "b.md"
        a.parent.mkdir(parents=True, exist_ok=True)
        a.write_text(
            "# A\n"
            f"{gdr.BEGIN_MARKER}\n"
            "[footer-only](b.md)\n"
            f"{gdr.END_MARKER}\n",
            encoding="utf-8",
        )
        b.write_text("# B", encoding="utf-8")
        outs, ins = gdr.build_repo_graph([a, b])
        assert outs.get("docs/a.md", set()) == set()
        assert ins.get("docs/b.md", set()) == set()


# ---------------------------------------------------------------------------
# _resolve_accessed_date / format_accessed_date
# ---------------------------------------------------------------------------


class TestResolveAccessedDate:
    def test_returns_cached_value_when_already_resolved(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(gdr, "_ACCESSED_DATE_RESOLVED", "PRE-CACHED")
        assert gdr._resolve_accessed_date("2026-05-11") == "PRE-CACHED"

    def test_uses_env_var_when_present(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(gdr, "_ACCESSED_DATE_RESOLVED", None)
        monkeypatch.setattr(gdr, "ACCESSED_DATE_ENV", "2026-01-15")
        out = gdr._resolve_accessed_date("2026-05-11")
        assert "January" in out
        assert "2026" in out

    def test_falls_back_to_library_accessed_when_no_env(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(gdr, "_ACCESSED_DATE_RESOLVED", None)
        monkeypatch.setattr(gdr, "ACCESSED_DATE_ENV", None)
        out = gdr._resolve_accessed_date("2026-05-11")
        assert "May" in out and "2026" in out

    @pytest.mark.filterwarnings(
        "ignore:datetime.datetime.utcnow:DeprecationWarning"
    )
    def test_invalid_iso_falls_back_to_today(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Known script bug: ``datetime.utcnow()`` is deprecated. The
        warning is silenced for the duration of this test so the
        fall-back branch is still exercised. Replace with a real fix
        when scripts/generate_doc_references.py migrates to
        ``datetime.now(timezone.utc)``.
        """
        monkeypatch.setattr(gdr, "_ACCESSED_DATE_RESOLVED", None)
        monkeypatch.setattr(gdr, "ACCESSED_DATE_ENV", "not-a-date")
        out = gdr._resolve_accessed_date(None)
        # Should not raise; should return a non-empty long-form string.
        assert out
        assert "," in out  # "<Month> <Day>, <Year>"

    @pytest.mark.filterwarnings(
        "ignore:datetime.datetime.utcnow:DeprecationWarning"
    )
    def test_no_inputs_falls_back_to_today(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Known script bug: ``datetime.utcnow()`` is deprecated. See
        ``test_invalid_iso_falls_back_to_today``.
        """
        monkeypatch.setattr(gdr, "_ACCESSED_DATE_RESOLVED", None)
        monkeypatch.setattr(gdr, "ACCESSED_DATE_ENV", None)
        out = gdr._resolve_accessed_date(None)
        assert out
        assert "," in out


class TestFormatAccessedDate:
    def test_returns_resolved_value(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(gdr, "_ACCESSED_DATE_RESOLVED", "Cached Date")
        assert gdr.format_accessed_date() == "Cached Date"


# ---------------------------------------------------------------------------
# render_citation
# ---------------------------------------------------------------------------


class TestRenderCitation:
    def test_anchor_emitted_with_id_and_index(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            gdr, "_ACCESSED_DATE_RESOLVED", "May 11, 2026"
        )
        rec = {
            "authority": "Splunk Inc.",
            "year": 2026,
            "title": "Splunk Enterprise",
            "publisher": "Splunk LLC",
            "type": "documentation",
            "url": "https://docs.splunk.com/",
        }
        out = gdr.render_citation(7, rec)
        assert '<a id="ref-7">' in out
        assert "**[7]**" in out

    def test_includes_retrieved_for_documentation_type(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            gdr, "_ACCESSED_DATE_RESOLVED", "May 11, 2026"
        )
        rec = {
            "authority": "X",
            "year": 2026,
            "title": "T",
            "type": "documentation",
            "url": "https://x.example/",
        }
        out = gdr.render_citation(1, rec)
        assert "Retrieved May 11, 2026" in out
        assert "https://x.example/" in out

    def test_omits_retrieved_for_standard_type(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            gdr, "_ACCESSED_DATE_RESOLVED", "May 11, 2026"
        )
        rec = {
            "authority": "ISO",
            "year": 2022,
            "title": "ISO/IEC 27001",
            "type": "standard",
            "url": "https://www.iso.org/standard/82875.html",
        }
        out = gdr.render_citation(2, rec)
        assert "Retrieved" not in out
        assert "https://www.iso.org/" in out

    def test_emits_year_with_month_name_when_valid(
        self, gdr: types.ModuleType
    ) -> None:
        rec = {
            "authority": "A",
            "year": 2026,
            "month": 3,
            "title": "T",
        }
        out = gdr.render_citation(1, rec)
        assert "(2026, March)" in out

    def test_emits_year_only_when_month_is_invalid(
        self, gdr: types.ModuleType
    ) -> None:
        rec = {
            "authority": "A",
            "year": 2026,
            "month": "not-a-month",
            "title": "T",
        }
        out = gdr.render_citation(1, rec)
        assert "(2026)" in out
        assert "month" not in out.lower()

    def test_includes_edition_inside_title_parens(
        self, gdr: types.ModuleType
    ) -> None:
        rec = {
            "authority": "A",
            "year": 2024,
            "title": "Title.",  # trailing period is stripped
            "edition": "2nd ed.",
        }
        out = gdr.render_citation(1, rec)
        assert "*Title* (2nd ed.)" in out

    def test_omits_publisher_when_same_as_authority(
        self, gdr: types.ModuleType
    ) -> None:
        rec = {
            "authority": "OnlyOrg",
            "year": 2026,
            "title": "T",
            "publisher": "OnlyOrg",
        }
        out = gdr.render_citation(1, rec)
        # Authority appears at most once.
        assert out.count("OnlyOrg") == 1

    def test_emits_publisher_when_different(
        self, gdr: types.ModuleType
    ) -> None:
        rec = {
            "authority": "Splunk Inc.",
            "year": 2026,
            "title": "T",
            "publisher": "Cisco Systems Inc.",
        }
        out = gdr.render_citation(1, rec)
        assert "Splunk Inc." in out
        assert "Cisco Systems Inc." in out

    def test_emits_identifier(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # render_citation calls format_accessed_date() for URL records
        # of type ``specification``; pre-set the cache so the deprecated
        # ``datetime.utcnow()`` fallback never runs.
        monkeypatch.setattr(
            gdr, "_ACCESSED_DATE_RESOLVED", "May 11, 2026"
        )
        rec = {
            "authority": "IETF",
            "year": 2017,
            "title": "JSON",
            "identifier": "RFC 8259",
            "type": "specification",
            "url": "https://www.rfc-editor.org/rfc/rfc8259",
        }
        out = gdr.render_citation(1, rec)
        assert "RFC 8259" in out

    def test_handles_record_with_no_year(
        self, gdr: types.ModuleType
    ) -> None:
        rec = {"authority": "A", "title": "T"}
        out = gdr.render_citation(1, rec)
        assert "**[1]**" in out
        # No "()" with a date should appear.
        assert "(.)" not in out

    def test_handles_record_with_nothing_but_id(
        self, gdr: types.ModuleType
    ) -> None:
        rec = {}
        out = gdr.render_citation(99, rec)
        # Should not crash; should still produce the anchor and index.
        assert "**[99]**" in out

    def test_terminator_already_punctuated_passes_through(
        self, gdr: types.ModuleType
    ) -> None:
        rec = {"authority": "Foo?", "year": 2026, "title": "T"}
        out = gdr.render_citation(1, rec)
        # The authority's trailing ``?`` should be preserved (not
        # double-punctuated to ``?.``).
        assert "Foo?" in out
        assert "Foo?." not in out


# ---------------------------------------------------------------------------
# _scan_protected_spans / _in_protected / _inline_marker_html
# ---------------------------------------------------------------------------


class TestScanProtectedSpans:
    def test_detects_fenced_blocks_inline_code_headings_links(
        self, gdr: types.ModuleType
    ) -> None:
        body = (
            "# Heading\n"
            "Setext\n=====\n\n"
            "```\nfence body\n```\n"
            "and `inline code` plus [text](url) here.\n"
            "<a href='x'>html</a>\n"
            "[ref-id]: https://example.com\n"
            f"{gdr.BEGIN_MARKER}\n"
            "auto\n"
            f"{gdr.END_MARKER}\n"
        )
        spans = gdr._scan_protected_spans(body)
        # We expect at least one span per kind we know about. We don't
        # need to enumerate them, just that there are several.
        assert len(spans) >= 5

    def test_handles_yaml_frontmatter(
        self, gdr: types.ModuleType
    ) -> None:
        # Note: the ``---`` lines that bracket the frontmatter also
        # match the setext-underline regex, so multiple spans will fall
        # over the same byte range. We just want to confirm the entire
        # ``---\n...\n---\n`` block is covered.
        body = "---\ntitle: x\n---\nbody text\n"
        spans = gdr._scan_protected_spans(body)
        # Some span must end at the closing of the frontmatter block.
        end_of_frontmatter = len("---\ntitle: x\n---\n")
        assert any(
            e == end_of_frontmatter for _s, e in spans
        ), spans

    def test_returns_sorted_spans(
        self, gdr: types.ModuleType
    ) -> None:
        body = "[link](url) `code` ## heading"
        spans = gdr._scan_protected_spans(body)
        starts = [s for s, _ in spans]
        assert starts == sorted(starts)


class TestInProtected:
    def test_position_inside_span_is_protected(
        self, gdr: types.ModuleType
    ) -> None:
        spans = [(0, 5), (10, 20)]
        assert gdr._in_protected(2, spans) is True
        assert gdr._in_protected(15, spans) is True

    def test_position_before_or_after_all_spans_is_not_protected(
        self, gdr: types.ModuleType
    ) -> None:
        spans = [(10, 20)]
        assert gdr._in_protected(5, spans) is False
        assert gdr._in_protected(25, spans) is False

    def test_position_in_gap_between_spans_is_not_protected(
        self, gdr: types.ModuleType
    ) -> None:
        spans = [(0, 5), (10, 20)]
        assert gdr._in_protected(7, spans) is False

    def test_no_spans_returns_false(self, gdr: types.ModuleType) -> None:
        assert gdr._in_protected(0, []) is False
        assert gdr._in_protected(999, []) is False


class TestInlineMarkerHtml:
    def test_renders_sup_with_class_and_anchor(
        self, gdr: types.ModuleType
    ) -> None:
        out = gdr._inline_marker_html(3)
        assert out == '<sup class="ref">[<a href="#ref-3">3</a>]</sup>'


# ---------------------------------------------------------------------------
# inject_inline_citations
# ---------------------------------------------------------------------------


class TestInjectInlineCitations:
    def test_returns_body_unchanged_when_id_to_num_empty(
        self, gdr: types.ModuleType
    ) -> None:
        body = "no citations here"
        assert gdr.inject_inline_citations(body, {}, {}) == body

    def test_returns_body_unchanged_when_no_phrases_match(
        self, gdr: types.ModuleType
    ) -> None:
        body = "no relevant terms in this text"
        out = gdr.inject_inline_citations(
            body, {"sid-1": 1}, {"sid-1": ["Splunk"]}
        )
        assert out == body

    def test_injects_marker_at_first_non_protected_match(
        self, gdr: types.ModuleType
    ) -> None:
        body = "We use Splunk in production."
        out = gdr.inject_inline_citations(
            body, {"sid-1": 7}, {"sid-1": ["Splunk"]}
        )
        assert '<sup class="ref">[<a href="#ref-7">7</a>]</sup>' in out
        # The marker is AFTER "Splunk".
        assert "Splunk" + '<sup class="ref">' in out

    def test_skips_match_in_code_fence(
        self, gdr: types.ModuleType
    ) -> None:
        body = (
            "We use it.\n"
            "```\n"
            "Splunk\n"
            "```\n"
            "and Splunk again here.\n"
        )
        out = gdr.inject_inline_citations(
            body, {"sid-1": 1}, {"sid-1": ["Splunk"]}
        )
        # Marker present somewhere outside the fence.
        assert "<sup class=" in out
        # Only one marker — first non-protected match wins.
        assert out.count("<sup class=") == 1

    def test_each_source_id_annotated_at_most_once(
        self, gdr: types.ModuleType
    ) -> None:
        body = "Splunk and Splunk and Splunk."
        out = gdr.inject_inline_citations(
            body, {"sid-1": 1}, {"sid-1": ["Splunk"]}
        )
        # Exactly one inline marker, on the first match.
        assert out.count("<sup class=") == 1

    def test_longest_phrase_wins_when_overlapping(
        self, gdr: types.ModuleType
    ) -> None:
        # "ISO/IEC 27001:2022" should be tried before "ISO 27001".
        body = "see ISO/IEC 27001:2022 and other text."
        out = gdr.inject_inline_citations(
            body,
            {"long": 1, "short": 2},
            {
                "long": ["ISO/IEC 27001:2022"],
                "short": ["ISO 27001"],
            },
        )
        # The long phrase fires and "short" doesn't match the body.
        assert out.count("<sup class=") == 1
        assert "ref-1" in out

    def test_no_insertion_if_only_protected_matches(
        self, gdr: types.ModuleType
    ) -> None:
        body = "[Splunk](https://splunk.com/) is great."
        # The only "Splunk" mention is inside a markdown-link label,
        # which is protected — so no marker should fire.
        out = gdr.inject_inline_citations(
            body, {"sid-1": 1}, {"sid-1": ["Splunk"]}
        )
        assert "<sup class=" not in out


# ---------------------------------------------------------------------------
# render_section + apply_to_file end-to-end fixtures.
# ---------------------------------------------------------------------------


def _full_fixture(
    gdr: types.ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    doc_body: str = "# Foo\nSome content about Splunk and SPL.",
    mappings_payload: dict[str, Any] | None = None,
    inline_payload: dict[str, list[str]] | None = None,
    library_records: dict[str, dict] | None = None,
) -> dict[str, Any]:
    paths = _patch_paths(gdr, monkeypatch, tmp_path)
    _seed_library(paths["library"], records=library_records)
    _seed_mappings(
        paths["mappings"],
        docs=(mappings_payload or {}).get("docs", {}),
        keywords=(mappings_payload or {}).get("keywords", {}),
    )
    _seed_inline_phrases(paths["inline"], inline_payload)
    # Write one doc under docs/foo.md.
    doc = tmp_path / "docs" / "foo.md"
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text(doc_body, encoding="utf-8")
    return {"paths": paths, "doc": doc, "doc_rel": "docs/foo.md"}


class TestRenderSection:
    def test_emits_empty_doc_message_when_no_refs_or_repo_links(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        fix = _full_fixture(
            gdr, monkeypatch, tmp_path,
            doc_body="# Foo\nJust prose, nothing notable.",
        )
        library, accessed = gdr.load_library()
        monkeypatch.setattr(gdr, "_ACCESSED_DATE_RESOLVED", None)
        gdr._resolve_accessed_date(accessed)
        mappings, keywords = gdr.load_mappings()
        block, id_to_num = gdr.render_section(
            fix["doc_rel"], fix["doc"], library, mappings, keywords,
            set(), set(),
        )
        assert "_No external sources are cited inline" in block
        assert id_to_num == {}
        assert block.startswith(gdr.BEGIN_MARKER)
        assert block.rstrip().endswith(gdr.END_MARKER)

    def test_renders_primary_and_supporting_with_anchors(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        fix = _full_fixture(
            gdr, monkeypatch, tmp_path,
            doc_body="# Foo\nTalking about Splunk and SPL all day.",
            library_records={
                "alpha": {
                    "authority": "Alpha Org",
                    "year": 2026,
                    "title": "Alpha Title",
                    "type": "documentation",
                    "url": "https://alpha.example/",
                },
                "beta": {
                    "authority": "Beta Org",
                    "year": 2025,
                    "title": "Beta Title",
                    "type": "documentation",
                    "url": "https://beta.example/",
                },
            },
            mappings_payload={
                "docs": {
                    "docs/foo.md": {
                        "primary": ["alpha"],
                        "supporting": ["beta"],
                    },
                }
            },
        )
        library, accessed = gdr.load_library()
        monkeypatch.setattr(gdr, "_ACCESSED_DATE_RESOLVED", None)
        gdr._resolve_accessed_date(accessed)
        mappings, keywords = gdr.load_mappings()
        block, id_to_num = gdr.render_section(
            fix["doc_rel"], fix["doc"], library, mappings, keywords,
            set(), set(),
        )
        assert gdr.SUBSECTION_PRIMARY in block
        assert gdr.SUBSECTION_SUPPORTING in block
        assert id_to_num == {"alpha": 1, "beta": 2}
        assert "Alpha Title" in block
        assert "Beta Title" in block

    def test_drops_supporting_id_when_also_present_in_primary(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        fix = _full_fixture(
            gdr, monkeypatch, tmp_path,
            library_records={
                "alpha": {
                    "authority": "A",
                    "year": 2026,
                    "title": "Alpha",
                    "type": "documentation",
                    "url": "https://a.example/",
                },
            },
            mappings_payload={
                "docs": {
                    "docs/foo.md": {
                        "primary": ["alpha"],
                        "supporting": ["alpha"],  # de-duped
                    }
                }
            },
        )
        library, accessed = gdr.load_library()
        monkeypatch.setattr(gdr, "_ACCESSED_DATE_RESOLVED", None)
        gdr._resolve_accessed_date(accessed)
        mappings, keywords = gdr.load_mappings()
        block, id_to_num = gdr.render_section(
            fix["doc_rel"], fix["doc"], library, mappings, keywords,
            set(), set(),
        )
        # Only one numbered citation, even though "alpha" appears in
        # both buckets.
        assert id_to_num == {"alpha": 1}
        assert block.count("**[1]**") == 1

    def test_emits_repo_in_out_link_sections(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        fix = _full_fixture(gdr, monkeypatch, tmp_path)
        # Provide a sibling for the relative path computation.
        (tmp_path / "docs" / "bar.md").write_text("# Bar", encoding="utf-8")
        library, accessed = gdr.load_library()
        monkeypatch.setattr(gdr, "_ACCESSED_DATE_RESOLVED", None)
        gdr._resolve_accessed_date(accessed)
        mappings, keywords = gdr.load_mappings()
        out_set = {"docs/bar.md"}
        in_set = {"docs/bar.md"}
        block, _ = gdr.render_section(
            fix["doc_rel"], fix["doc"], library, mappings, keywords,
            out_set, in_set,
        )
        assert gdr.SUBSECTION_REPO_OUT in block
        assert gdr.SUBSECTION_REPO_IN in block
        assert "bar.md" in block

    def test_truncates_huge_repo_link_lists(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        fix = _full_fixture(gdr, monkeypatch, tmp_path)
        # Generate (MAX_REPO_LINKS_PER_DIRECTION + 5) sibling docs.
        n = gdr.MAX_REPO_LINKS_PER_DIRECTION + 5
        for i in range(n):
            (tmp_path / "docs" / f"sib{i:03d}.md").write_text(
                "# Sib", encoding="utf-8"
            )
        library, accessed = gdr.load_library()
        monkeypatch.setattr(gdr, "_ACCESSED_DATE_RESOLVED", None)
        gdr._resolve_accessed_date(accessed)
        mappings, keywords = gdr.load_mappings()
        out_set = {f"docs/sib{i:03d}.md" for i in range(n)}
        in_set: set[str] = set()
        block, _ = gdr.render_section(
            fix["doc_rel"], fix["doc"], library, mappings, keywords,
            out_set, in_set,
        )
        # We should see the truncation footer when exceeding the cap.
        assert "and 5 more" in block
        assert "docs/backlinks.md" in block

    def test_skips_additional_section_when_curated_count_high(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        # 12+ curated refs and ≤2 extra URLs in body → additional
        # section is intentionally skipped.
        records = {
            f"src-{i}": {
                "authority": f"Org {i}",
                "year": 2026,
                "title": f"Title {i}",
                "type": "documentation",
                "url": f"https://x{i}.example/",
            }
            for i in range(15)
        }
        fix = _full_fixture(
            gdr, monkeypatch, tmp_path,
            library_records=records,
            mappings_payload={
                "docs": {
                    "docs/foo.md": {
                        "primary": [f"src-{i}" for i in range(15)],
                    }
                }
            },
            doc_body="# Foo\nA single extra: https://other.example/x",
        )
        library, accessed = gdr.load_library()
        monkeypatch.setattr(gdr, "_ACCESSED_DATE_RESOLVED", None)
        gdr._resolve_accessed_date(accessed)
        mappings, keywords = gdr.load_mappings()
        block, _ = gdr.render_section(
            fix["doc_rel"], fix["doc"], library, mappings, keywords,
            set(), set(),
        )
        assert "Additional online sources" not in block
        assert "<details>" not in block

    def test_emits_additional_details_block(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        fix = _full_fixture(
            gdr, monkeypatch, tmp_path,
            doc_body=(
                "# Foo\n"
                "Body: https://body.example/one\n"
                "Body: https://body.example/two\n"
            ),
        )
        library, accessed = gdr.load_library()
        monkeypatch.setattr(gdr, "_ACCESSED_DATE_RESOLVED", None)
        gdr._resolve_accessed_date(accessed)
        mappings, keywords = gdr.load_mappings()
        block, _ = gdr.render_section(
            fix["doc_rel"], fix["doc"], library, mappings, keywords,
            set(), set(),
        )
        assert "<details>" in block
        assert "Additional online sources" in block
        assert "https://body.example/one" in block
        assert "https://body.example/two" in block

    def test_drops_records_with_unknown_ids_silently(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        fix = _full_fixture(
            gdr, monkeypatch, tmp_path,
            library_records={
                "real-id": {
                    "authority": "A",
                    "year": 2026,
                    "title": "T",
                    "type": "documentation",
                    "url": "https://a.example/",
                }
            },
            mappings_payload={
                "docs": {
                    "docs/foo.md": {
                        "primary": ["real-id", "ghost-id"],
                    }
                }
            },
        )
        library, accessed = gdr.load_library()
        monkeypatch.setattr(gdr, "_ACCESSED_DATE_RESOLVED", None)
        gdr._resolve_accessed_date(accessed)
        mappings, keywords = gdr.load_mappings()
        block, id_to_num = gdr.render_section(
            fix["doc_rel"], fix["doc"], library, mappings, keywords,
            set(), set(),
        )
        # The unknown ID is silently dropped.
        assert id_to_num == {"real-id": 1}
        assert "T" in block


# ---------------------------------------------------------------------------
# apply_to_file
# ---------------------------------------------------------------------------


class TestApplyToFile:
    def test_appends_new_block_when_marker_missing(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        fix = _full_fixture(gdr, monkeypatch, tmp_path)
        library, _ = gdr.load_library()
        mappings, keywords = gdr.load_mappings()
        original, new = gdr.apply_to_file(
            fix["doc"], fix["doc_rel"], library, mappings, keywords,
            {}, set(), set(),
        )
        assert gdr.BEGIN_MARKER not in original
        assert gdr.BEGIN_MARKER in new
        # The original content is preserved.
        assert original.splitlines()[0] in new

    def test_replaces_existing_block_idempotently(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        fix = _full_fixture(
            gdr, monkeypatch, tmp_path,
            doc_body=(
                "# Foo\nProse\n\n"
                f"{gdr.BEGIN_MARKER}\nold content\n{gdr.END_MARKER}\n"
            ),
        )
        library, accessed = gdr.load_library()
        monkeypatch.setattr(gdr, "_ACCESSED_DATE_RESOLVED", None)
        gdr._resolve_accessed_date(accessed)
        mappings, keywords = gdr.load_mappings()
        _, new = gdr.apply_to_file(
            fix["doc"], fix["doc_rel"], library, mappings, keywords,
            {}, set(), set(),
        )
        assert "old content" not in new
        # Exactly one marker pair survives.
        assert new.count(gdr.BEGIN_MARKER) == 1
        assert new.count(gdr.END_MARKER) == 1
        # Run a second pass — must be byte-identical (idempotent).
        fix["doc"].write_text(new, encoding="utf-8")
        _, third = gdr.apply_to_file(
            fix["doc"], fix["doc_rel"], library, mappings, keywords,
            {}, set(), set(),
        )
        assert third == new

    def test_strips_pre_existing_inline_markers(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        fix = _full_fixture(
            gdr, monkeypatch, tmp_path,
            doc_body=(
                "# Foo\n"
                'Splunk<sup class="ref">[<a href="#ref-9">9</a>]</sup> '
                "is good."
            ),
        )
        library, _ = gdr.load_library()
        mappings, keywords = gdr.load_mappings()
        _, new = gdr.apply_to_file(
            fix["doc"], fix["doc_rel"], library, mappings, keywords,
            {}, set(), set(),
        )
        # Stale marker is gone (no inline phrases supplied → no
        # replacement injected).
        assert 'href="#ref-9"' not in new

    def test_appends_separator_when_original_lacks_trailing_newline(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        fix = _full_fixture(
            gdr, monkeypatch, tmp_path,
            doc_body="# Foo\nNo trailing newline",
        )
        library, _ = gdr.load_library()
        mappings, keywords = gdr.load_mappings()
        original, new = gdr.apply_to_file(
            fix["doc"], fix["doc_rel"], library, mappings, keywords,
            {}, set(), set(),
        )
        assert not original.endswith("\n")
        # The script inserts a newline before the "---" separator.
        assert "\n\n---\n\n" in new


# ---------------------------------------------------------------------------
# main() CLI.
# ---------------------------------------------------------------------------


def _wire_full_repo(
    gdr: types.ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    library_records: dict[str, dict] | None = None,
    mappings_docs: dict[str, dict[str, list[str]]] | None = None,
    keywords: dict[str, list[str]] | None = None,
    inline_payload: dict[str, list[str]] | None = None,
    extra_docs: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Wire a complete pretend-repo under ``tmp_path``."""
    paths = _patch_paths(gdr, monkeypatch, tmp_path)
    _seed_library(paths["library"], records=library_records)
    _seed_mappings(
        paths["mappings"],
        docs=mappings_docs or {},
        keywords=keywords,
    )
    _seed_inline_phrases(paths["inline"], inline_payload)
    docs = {}
    for rel, body in (extra_docs or {"docs/foo.md": "# Foo"}).items():
        full = tmp_path / rel
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(body, encoding="utf-8")
        docs[rel] = full
    return {"paths": paths, "docs": docs}


class TestMainValidateLibrary:
    def test_validate_library_happy_path(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _wire_full_repo(
            gdr, monkeypatch, tmp_path,
            library_records={
                "alpha": {
                    "authority": "A",
                    "year": 2026,
                    "title": "T",
                    "type": "documentation",
                    "url": "https://a.example/",
                }
            },
            mappings_docs={
                "docs/foo.md": {"primary": ["alpha"]},
            },
            keywords={"Splunk": ["alpha"]},
            inline_payload={"alpha": ["Splunk"]},
        )
        rc = gdr.main(["--validate-library"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "OK:" in out
        assert "all mapping IDs resolve" in out

    def test_validate_library_reports_dangling_ids(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _wire_full_repo(
            gdr, monkeypatch, tmp_path,
            library_records={"only-real": {"title": "T"}},
            mappings_docs={
                "docs/foo.md": {
                    "primary": ["ghost-1"],
                    "supporting": ["ghost-2"],
                    "related": ["ghost-3"],
                },
            },
            keywords={"TermA": ["ghost-4"]},
            inline_payload={"ghost-5": ["phrase"]},
        )
        rc = gdr.main(["--validate-library"])
        out = capsys.readouterr().out
        assert rc == 1
        assert "dangling source IDs" in out
        # Each missing ID should appear in the output.
        for sid in ("ghost-1", "ghost-2", "ghost-3", "ghost-4", "ghost-5"):
            assert sid in out

    def test_validate_library_truncates_to_30_missing(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Build a mappings doc that references 50 ghost IDs.
        ghosts = {f"ghost-{i}": ["phrase"] for i in range(50)}
        _wire_full_repo(
            gdr, monkeypatch, tmp_path,
            library_records={"real": {"title": "R"}},
            inline_payload=ghosts,
        )
        rc = gdr.main(["--validate-library"])
        out = capsys.readouterr().out
        assert rc == 1
        # Only the first 30 are printed; the rest are dropped.
        printed_ghosts = sum(
            1 for line in out.splitlines() if "ghost-" in line
        )
        assert printed_ghosts == 30


class TestMainWriteMode:
    def test_writes_to_changed_files_by_default(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        wired = _wire_full_repo(
            gdr, monkeypatch, tmp_path,
            extra_docs={
                "docs/foo.md": "# Foo\nNo refs yet.",
            },
        )
        rc = gdr.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "Processed" in out
        assert "rewritten" in out
        content = wired["docs"]["docs/foo.md"].read_text(encoding="utf-8")
        assert gdr.BEGIN_MARKER in content
        assert gdr.END_MARKER in content

    def test_dry_run_does_not_write(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        wired = _wire_full_repo(
            gdr, monkeypatch, tmp_path,
            extra_docs={"docs/foo.md": "# Foo\nNo refs."},
        )
        original = wired["docs"]["docs/foo.md"].read_text(encoding="utf-8")
        rc = gdr.main(["--dry-run"])
        assert rc == 0
        assert (
            wired["docs"]["docs/foo.md"].read_text(encoding="utf-8")
            == original
        )

    def test_skip_set_suppresses_writes(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Add CHANGELOG.md which is in SKIP.
        wired = _wire_full_repo(
            gdr, monkeypatch, tmp_path,
            extra_docs={
                "CHANGELOG.md": "# Changelog",
                "docs/keep.md": "# Keep",
            },
        )
        # Make CHANGELOG.md a recognised "extra" by writing it to disk
        # — collect_md_nodes already references it as an extra.
        rc = gdr.main([])
        assert rc == 0
        out = capsys.readouterr().out
        # CHANGELOG.md must remain unchanged (no footer).
        changelog = wired["docs"]["CHANGELOG.md"].read_text(encoding="utf-8")
        assert gdr.BEGIN_MARKER not in changelog
        # But docs/keep.md should have a footer.
        keep = wired["docs"]["docs/keep.md"].read_text(encoding="utf-8")
        assert gdr.BEGIN_MARKER in keep
        # Summary reports a non-zero "skipped" count.
        assert "skipped" in out


class TestMainCheckMode:
    def test_check_returns_zero_when_clean(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _wire_full_repo(
            gdr, monkeypatch, tmp_path,
            extra_docs={"docs/foo.md": "# Foo"},
        )
        # First pass writes the footer.
        assert gdr.main([]) == 0
        # Reset accessed-date cache so the second main() doesn't rely
        # on a stale value (it actually re-resolves the same date so
        # output is identical, but be defensive).
        monkeypatch.setattr(gdr, "_ACCESSED_DATE_RESOLVED", None)
        # Second pass with --check sees no drift.
        rc = gdr.main(["--check"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "OK" in out

    def test_check_returns_one_on_drift(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        wired = _wire_full_repo(
            gdr, monkeypatch, tmp_path,
            extra_docs={"docs/foo.md": "# Foo\nNo refs."},
        )
        # Don't write the footer first — main(--check) sees the doc as
        # stale.
        rc = gdr.main(["--check"])
        out = capsys.readouterr().out
        assert rc == 1
        assert "stale auto-references" in out
        assert "docs/foo.md" in out

    def test_check_truncates_file_list_when_above_15(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Create 20 stale docs.
        extras = {f"docs/d{i:02d}.md": f"# Doc {i}" for i in range(20)}
        _wire_full_repo(
            gdr, monkeypatch, tmp_path,
            extra_docs=extras,
        )
        rc = gdr.main(["--check"])
        out = capsys.readouterr().out
        assert rc == 1
        # The "and N more" truncation footer should appear.
        assert "and 5 more" in out


class TestMainOnlyFilter:
    def test_only_glob_restricts_files_processed(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        wired = _wire_full_repo(
            gdr, monkeypatch, tmp_path,
            extra_docs={
                "docs/alpha.md": "# A",
                "docs/beta.md": "# B",
            },
        )
        rc = gdr.main(["--only", "docs/alpha.md"])
        assert rc == 0
        # Only alpha gets a footer; beta is untouched.
        assert gdr.BEGIN_MARKER in wired["docs"]["docs/alpha.md"].read_text(
            encoding="utf-8"
        )
        assert gdr.BEGIN_MARKER not in wired["docs"]["docs/beta.md"].read_text(
            encoding="utf-8"
        )

    def test_only_glob_with_wildcard(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        wired = _wire_full_repo(
            gdr, monkeypatch, tmp_path,
            extra_docs={
                "docs/alpha.md": "# A",
                "docs/beta.md": "# B",
                "AGENTS.md": "# Agents",
            },
        )
        rc = gdr.main(["--only", "docs/*.md"])
        assert rc == 0
        assert gdr.BEGIN_MARKER in wired["docs"]["docs/alpha.md"].read_text(
            encoding="utf-8"
        )
        assert gdr.BEGIN_MARKER in wired["docs"]["docs/beta.md"].read_text(
            encoding="utf-8"
        )
        # AGENTS.md is NOT under docs/ → no footer.
        assert gdr.BEGIN_MARKER not in wired["docs"]["AGENTS.md"].read_text(
            encoding="utf-8"
        )


class TestMainHelpAndErrors:
    def test_help_text_exits_zero(
        self, gdr: types.ModuleType
    ) -> None:
        with pytest.raises(SystemExit) as exc:
            gdr.main(["--help"])
        assert exc.value.code == 0


# ---------------------------------------------------------------------------
# Coverage closers — tests targeting specific branches/lines that the
# happy-path suite above leaves uncovered.
# ---------------------------------------------------------------------------


class TestCoverageClosers:
    def test_collect_md_nodes_skips_directories(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Line 187 branch (`if p.is_file()` false): a directory under
        ``docs/`` with an ``.md`` suffix must be skipped.
        """
        _patch_paths(gdr, monkeypatch, tmp_path)
        # A directory named ``something.md`` — the rglob hits it but
        # ``p.is_file()`` returns False.
        bogus_dir = tmp_path / "docs" / "weird.md"
        bogus_dir.mkdir(parents=True)
        real_md = tmp_path / "docs" / "real.md"
        real_md.write_text("# Real", encoding="utf-8")
        out = gdr.collect_md_nodes()
        out_names = [p.name for p in out]
        assert "real.md" in out_names
        # The directory was not added.
        assert bogus_dir.resolve() not in [p.resolve() for p in out]

    def test_extract_additional_urls_drops_repeat_markdown_link(
        self, gdr: types.ModuleType
    ) -> None:
        """Line 506 (`if url in found: continue` inside the markdown-
        link loop): the SAME URL appears in two markdown links — only
        the first should be kept.
        """
        body = (
            "[first label](https://notes.example.org/x) "
            "[second label](https://notes.example.org/x)"
        )
        out = gdr.extract_additional_urls(body, set())
        # Only one entry, and the label is the first one we saw.
        assert list(out.keys()) == ["https://notes.example.org/x"]
        assert out["https://notes.example.org/x"] == "first label"

    def test_build_repo_graph_skips_protocol_relative_targets(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Line 555 (the ``if target.startswith((...)) : continue``
        branch): hit on a protocol-relative ``.md`` target. Without
        this branch the script would happily resolve `//host/x.md`
        against the source's parent directory and emit a phantom edge.
        """
        _patch_paths(gdr, monkeypatch, tmp_path)
        a = tmp_path / "docs" / "a.md"
        a.parent.mkdir(parents=True, exist_ok=True)
        a.write_text(
            "# A\n"
            "[protocol-rel](//evil.example.org/x.md)\n"
            "[file](file:///etc/secret.md)\n"
            "[http](http://example.org/path.md)\n"
            "[https](https://example.org/path.md)\n"
            "[mailto](mailto:x@example.org)\n",  # mailto: doesn't end .md
            encoding="utf-8",
        )
        outs, _ins = gdr.build_repo_graph([a])
        assert outs.get("docs/a.md", set()) == set()

    def test_render_section_dedupes_duplicate_ids_in_resolve(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Line 697 (`if sid in seen: continue` inside resolve): a
        bucket that lists the same source ID twice should yield exactly
        one citation.
        """
        fix = _full_fixture(
            gdr, monkeypatch, tmp_path,
            library_records={
                "dup": {
                    "authority": "A",
                    "year": 2026,
                    "title": "T",
                    "type": "documentation",
                    "url": "https://a.example/",
                },
            },
            mappings_payload={
                "docs": {
                    "docs/foo.md": {
                        # Two references to the same ID in the same
                        # bucket — the inner ``seen`` set must filter
                        # the duplicate.
                        "primary": ["dup", "dup"],
                    }
                }
            },
        )
        library, accessed = gdr.load_library()
        monkeypatch.setattr(gdr, "_ACCESSED_DATE_RESOLVED", None)
        gdr._resolve_accessed_date(accessed)
        mappings, keywords = gdr.load_mappings()
        block, id_to_num = gdr.render_section(
            fix["doc_rel"], fix["doc"], library, mappings, keywords,
            set(), set(),
        )
        assert id_to_num == {"dup": 1}
        assert block.count("**[1]**") == 1

    def test_render_section_skips_url_collection_when_no_url(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Branch 736 (`if r.get('url'): covered.add(...)` false): the
        loop must NOT crash when a curated record has no URL.
        """
        fix = _full_fixture(
            gdr, monkeypatch, tmp_path,
            library_records={
                "no-url": {
                    "authority": "Author",
                    "year": 2020,
                    "title": "Book Without URL",
                    "type": "book",
                },
            },
            mappings_payload={
                "docs": {
                    "docs/foo.md": {"primary": ["no-url"]},
                }
            },
        )
        library, accessed = gdr.load_library()
        monkeypatch.setattr(gdr, "_ACCESSED_DATE_RESOLVED", None)
        gdr._resolve_accessed_date(accessed)
        mappings, keywords = gdr.load_mappings()
        block, id_to_num = gdr.render_section(
            fix["doc_rel"], fix["doc"], library, mappings, keywords,
            set(), set(),
        )
        assert id_to_num == {"no-url": 1}
        assert "Book Without URL" in block

    def test_render_section_truncates_in_sorted_list(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Line 829 (the in_sorted truncation footer): the previous
        truncation test only exercised out_sorted; this covers the
        symmetric branch for the "Cited by" section.
        """
        fix = _full_fixture(gdr, monkeypatch, tmp_path)
        # Generate (MAX_REPO_LINKS_PER_DIRECTION + 3) inbound sibling
        # docs, with no outbound links.
        n = gdr.MAX_REPO_LINKS_PER_DIRECTION + 3
        for i in range(n):
            (tmp_path / "docs" / f"in{i:03d}.md").write_text(
                "# In", encoding="utf-8"
            )
        library, accessed = gdr.load_library()
        monkeypatch.setattr(gdr, "_ACCESSED_DATE_RESOLVED", None)
        gdr._resolve_accessed_date(accessed)
        mappings, keywords = gdr.load_mappings()
        in_set = {f"docs/in{i:03d}.md" for i in range(n)}
        block, _ = gdr.render_section(
            fix["doc_rel"], fix["doc"], library, mappings, keywords,
            set(), in_set,
        )
        assert gdr.SUBSECTION_REPO_IN in block
        # The in_sorted truncation footer fires.
        assert "and 3 more" in block

    def test_humanise_url_splunk_docs_observability_branch(
        self, gdr: types.ModuleType
    ) -> None:
        """Branch 303->307: a Splunk Docs URL whose path doesn't match
        the ``/Documentation/<Product>/...`` regex should fall through
        to the observability matcher.
        """
        out = gdr.humanise_url(
            "https://docs.splunk.com/observability/en/admin/admin.html"
        )
        assert out.startswith("Splunk Observability")

    def test_main_skip_set_does_not_open_files(
        self,
        gdr: types.ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Lines 1067-1068: the ``if src_rel in SKIP: continue`` branch
        must short-circuit before apply_to_file is called.

        Only docs that are ALSO picked up by ``collect_md_nodes()``
        reach the SKIP filter. The script's extras list doesn't include
        SKIP entries like ``VERSION`` — but anything under ``docs/`` is
        scanned by ``rglob("*.md")``, so we use one of the ``docs/``-
        prefixed SKIP entries to exercise the branch.
        """
        wired = _wire_full_repo(
            gdr, monkeypatch, tmp_path,
            extra_docs={
                # In SKIP and picked up by the docs/ rglob:
                "docs/backlinks.md": "# Backlinks",
                # A regular doc that DOES get rewritten:
                "docs/normal.md": "# Normal",
            },
        )
        rc = gdr.main([])
        assert rc == 0
        # docs/backlinks.md's content is unchanged (no footer).
        assert (
            wired["docs"]["docs/backlinks.md"].read_text(encoding="utf-8")
            == "# Backlinks"
        )
        # docs/normal.md WAS rewritten.
        assert gdr.BEGIN_MARKER in wired["docs"]["docs/normal.md"].read_text(
            encoding="utf-8"
        )
        out = capsys.readouterr().out
        # Summary reports at least one skipped file.
        assert "skipped" in out
        # Specifically: " 1 skipped" or " 2 skipped" — the exact
        # count depends on whether collect_md_nodes() picked up other
        # SKIP-listed files in the test scaffold; either way it's >=1.
        match = re.search(r"(\d+)\s+skipped", out)
        assert match is not None
        assert int(match.group(1)) >= 1

    def test_inject_inline_citations_skips_already_annotated_sid(
        self, gdr: types.ModuleType
    ) -> None:
        """Line 945 (`if sid in annotated_ids: continue`): when one
        source has multiple phrases AND the longest phrase matches
        first, the script must not re-emit a second marker for the
        same source even if a shorter phrase also matches later.
        """
        # Source ``X`` has two phrases. Both occur in the body. After
        # the long phrase (``Splunk Enterprise Security``) inserts its
        # marker, the short one (``Splunk``) should be skipped on the
        # second pass through candidates.
        body = "Splunk Enterprise Security is great. Splunk Splunk."
        out = gdr.inject_inline_citations(
            body,
            {"X": 1},
            {"X": ["Splunk", "Splunk Enterprise Security"]},
        )
        # Exactly one marker — the long phrase wins, the short phrase
        # is skipped because the SID is now in annotated_ids.
        assert out.count("<sup class=") == 1
        # The marker is positioned after the long phrase, not after
        # the first short ``Splunk`` (which would be earlier).
        marker_pos = out.find("<sup class=")
        long_end = (
            out[:marker_pos].rfind("Splunk Enterprise Security")
            + len("Splunk Enterprise Security")
        )
        assert marker_pos == long_end

    def test_auto_resolve_keywords_keeps_first_sid_when_duplicated(
        self, gdr: types.ModuleType
    ) -> None:
        """Line 480 branch: the inner ``if sid not in seen`` guards
        against listing the same source ID twice when multiple keyword
        terms map to it.
        """
        body = "SPL is part of Splunk."
        keywords = {
            "SPL": ["shared-ref"],
            "Splunk": ["shared-ref"],
        }
        out = gdr.auto_resolve_keywords(body, keywords)
        # Even though both terms match, the shared ID appears once.
        assert out == ["shared-ref"]

    def test_humanise_url_splunk_docs_neither_branch_matches(
        self, gdr: types.ModuleType
    ) -> None:
        """Branch 303->307: a ``docs.splunk.com`` URL whose path is
        NEITHER ``/Documentation/...`` NOR ``/observability/...``
        should fall through to the pure-host fallback after the
        observability regex returns None.
        """
        out = gdr.humanise_url(
            "https://docs.splunk.com/some-other-page/about"
        )
        # No "Documentation" / "Observability" match → fallback path.
        assert out  # non-empty
        assert "docs.splunk.com" in out
        assert not out.startswith("Splunk ")

    def test_scan_protected_spans_unterminated_frontmatter(
        self, gdr: types.ModuleType
    ) -> None:
        """Branch 883->887: text starts with ``---\\n`` but the regex
        ``---\\n.*?\\n---\\n`` finds no closing fence — the YAML span
        is NOT appended and execution moves on to markdown links.
        """
        body = "---\nopen frontmatter never closes\n\nbody [link](url)\n"
        spans = gdr._scan_protected_spans(body)
        # Whatever spans are emitted, none of them is the full
        # frontmatter block (because there's no closing ``---``).
        # The first ``---`` is picked up by the setext-underline regex
        # as (0, 3), not by the YAML-frontmatter detector.
        # We assert that the inline link span IS present — proving
        # the function didn't crash and moved past the YAML branch.
        link_start = body.index("[link]")
        link_end = body.index("(url)") + len("(url)")
        assert (link_start, link_end) in spans
