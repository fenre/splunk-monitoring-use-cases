"""Hermetic unit tests for ``scripts/audit_doc_vendor_products.py``.

The script extracts "Vendor + 1-4 capitalised tokens" phrases from
every prose document under ``docs/`` (plus a small extras list),
matches Cisco / Splunk hits against a curated allowlist enriched
from ``api/v1/equipment/index.json`` and
``data/splunkbase-catalog.json``, and writes
``data/doc-vendor-mentions.json``. It's the second-line hallucination
defence after the URL audit: a 200-OK URL can still sit next to a
fabricated product name.

We care about three failure surfaces:

* **Extractor false-positives** — the tail walker has 7 distinct
  stop conditions (lowercase, English stopword, prose-verb blacklist,
  slash, UC-ID, second anchor, terminating punct, capitalisation
  rule, tail-length cap). Any silent regression there blows the
  ``suspicious`` queue up by hundreds of phrases overnight.
* **Allowlist drift** — equipment + Splunkbase JSON live in
  separate files; misparsing them silently shrinks the allowlist
  and pumps the suspicious queue (false positives). Pin the
  three legal Splunkbase shapes and the equipment label/model
  flattening.
* **--strict exit semantics** — gate must exit 1 on suspicious
  results and 0 on a clean run; confusing those two states would
  let CI silently bless hallucinations.

Hermetic: every filesystem read/write is monkey-patched into
``tmp_path``. The real ``data/doc-vendor-mentions.json`` is never
touched.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "audit_doc_vendor_products.py"


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "audit_doc_vendor_products", SCRIPT_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["audit_doc_vendor_products"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def avp() -> ModuleType:
    """Fresh import of the audit module per test."""
    return _load_module()


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def _patch_paths(
    avp: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> dict[str, Path]:
    """Re-root every hard-coded input/output path into ``tmp_path``."""
    docs_dir = tmp_path / "docs"
    status_path = tmp_path / "data" / "doc-vendor-mentions.json"
    equipment_index = tmp_path / "api" / "v1" / "equipment" / "index.json"
    splunkbase_catalog = tmp_path / "data" / "splunkbase-catalog.json"

    monkeypatch.setattr(avp, "REPO", tmp_path)
    monkeypatch.setattr(avp, "DOCS_DIR", docs_dir)
    monkeypatch.setattr(avp, "STATUS_PATH", status_path)
    monkeypatch.setattr(avp, "EQUIPMENT_INDEX", equipment_index)
    monkeypatch.setattr(avp, "SPLUNKBASE_CATALOG", splunkbase_catalog)

    return {
        "repo": tmp_path,
        "docs_dir": docs_dir,
        "status_path": status_path,
        "equipment_index": equipment_index,
        "splunkbase_catalog": splunkbase_catalog,
    }


def _write_doc(docs_dir: Path, rel: str, body: str) -> Path:
    out = docs_dir / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(body, encoding="utf-8")
    return out


# ======================================================================
# 1. Module-level constants & contracts
# ======================================================================


class TestModuleConstants:
    def test_vendor_surfaces_anchors_have_explicit_tail_caps(
        self, avp: ModuleType
    ) -> None:
        # Every anchor must declare an integer tail cap; missing caps
        # would crash extract_phrases with a KeyError. Pin a few
        # representative anchors so an accidental rename surfaces here.
        for anchor in ("Cisco", "Splunk", "Microsoft", "AWS", "Red Hat",
                       "Palo Alto", "Check Point"):
            assert anchor in avp.VENDOR_SURFACES
            assert isinstance(avp.VENDOR_SURFACES[anchor], int)
            assert avp.VENDOR_SURFACES[anchor] >= 3

    def test_anchors_sorted_orders_longest_first(self, avp: ModuleType) -> None:
        # Multi-word anchors MUST be matched before their first-token
        # prefix, otherwise "Red Hat" would mis-bind to "Red".
        lens = [len(a) for a in avp.ANCHORS_SORTED]
        assert lens == sorted(lens, reverse=True), \
            "ANCHORS_SORTED must be longest-first"

    def test_english_stopwords_lowercase(self, avp: ModuleType) -> None:
        for w in avp.ENGLISH_STOPWORDS:
            assert w == w.lower()

    def test_prose_verb_blacklist_lowercase(self, avp: ModuleType) -> None:
        for w in avp.PROSE_VERB_BLACKLIST:
            assert w == w.lower()

    def test_known_prose_noise_lowercase(self, avp: ModuleType) -> None:
        for w in avp.KNOWN_PROSE_NOISE:
            assert w == w.lower()

    def test_curated_cisco_lowercase_and_prefixed(
        self, avp: ModuleType
    ) -> None:
        # Allowlist matching is case-insensitive but build_allowlist
        # expects lower-case entries. Pin that.
        for w in avp.CURATED_CISCO:
            assert w == w.lower()
            assert w.startswith("cisco"), \
                f"non-cisco entry in CURATED_CISCO: {w!r}"

    def test_curated_splunk_lowercase_and_prefixed(
        self, avp: ModuleType
    ) -> None:
        for w in avp.CURATED_SPLUNK:
            assert w == w.lower()
            assert w.startswith("splunk"), \
                f"non-splunk entry in CURATED_SPLUNK: {w!r}"

    def test_default_extra_uses_repo_relative_paths(
        self, avp: ModuleType
    ) -> None:
        # The walker derives absolute paths from REPO / rel; absolute
        # paths in DEFAULT_EXTRA would silently bypass the
        # monkey-patched REPO root.
        for rel in avp.DEFAULT_EXTRA:
            assert not rel.startswith("/")

    def test_capitalised_token_re_accepts_acronyms(self, avp: ModuleType) -> None:
        # Two-char-or-longer alphanumeric tokens with a leading capital.
        assert avp.CAPITALISED_TOKEN_RE.fullmatch("ASA")
        assert avp.CAPITALISED_TOKEN_RE.fullmatch("Catalyst")
        assert avp.CAPITALISED_TOKEN_RE.fullmatch("IOS-XE")
        # Mixed alnum-and-punct tokens are accepted as long as the
        # first two chars are [A-Z][A-Za-z0-9].
        assert avp.CAPITALISED_TOKEN_RE.fullmatch("X9")
        assert avp.CAPITALISED_TOKEN_RE.fullmatch("X9.5")

    def test_capitalised_token_re_rejects_purely_numeric(
        self, avp: ModuleType
    ) -> None:
        assert not avp.CAPITALISED_TOKEN_RE.fullmatch("9")
        assert not avp.CAPITALISED_TOKEN_RE.fullmatch("9.4")
        assert not avp.CAPITALISED_TOKEN_RE.fullmatch("134")

    def test_capitalised_token_re_rejects_single_capital_letter(
        self, avp: ModuleType
    ) -> None:
        # The pattern requires AT LEAST two characters, so single
        # capital letters do NOT match. This is intentional - it
        # prevents the walker from absorbing trailing initials like
        # "Cisco A B C" as a tail. Pin the contract.
        assert not avp.CAPITALISED_TOKEN_RE.fullmatch("A")
        assert not avp.CAPITALISED_TOKEN_RE.fullmatch("Z")

    def test_trailing_punct_contains_curly_quotes_and_dashes(
        self, avp: ModuleType
    ) -> None:
        # Curly quotes and em/en dashes show up in prose; the walker
        # MUST treat them as terminating.
        for ch in (".", ",", ";", ":", "!", "?", "\u201d", "\u2014"):
            assert ch in avp.TRAILING_PUNCT


# ======================================================================
# 2. collect_docs
# ======================================================================


class TestCollectDocs:
    def test_returns_empty_when_docs_dir_missing(
        self, avp: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _patch_paths(avp, monkeypatch, tmp_path)
        assert avp.collect_docs() == []

    def test_finds_markdown_under_docs_recursively(
        self, avp: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        paths = _patch_paths(avp, monkeypatch, tmp_path)
        _write_doc(paths["docs_dir"], "guides/x.md", "x")
        _write_doc(paths["docs_dir"], "y.md", "y")
        out = avp.collect_docs()
        assert len(out) == 2
        names = {p.name for p in out}
        assert names == {"x.md", "y.md"}

    def test_includes_default_extras_when_present(
        self, avp: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        paths = _patch_paths(avp, monkeypatch, tmp_path)
        (tmp_path / "AGENTS.md").write_text("hello", encoding="utf-8")
        (tmp_path / "README.md").write_text("hello", encoding="utf-8")
        out = avp.collect_docs()
        names = {p.name for p in out}
        assert "AGENTS.md" in names
        assert "README.md" in names

    def test_skips_missing_default_extras_silently(
        self, avp: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        paths = _patch_paths(avp, monkeypatch, tmp_path)
        # No DEFAULT_EXTRA file present — the walker must not raise.
        (tmp_path / "AGENTS.md").write_text("x", encoding="utf-8")
        # No docs/ dir either; only one extra exists.
        out = avp.collect_docs()
        assert [p.name for p in out] == ["AGENTS.md"]

    def test_deduplicates_paths(
        self, avp: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        paths = _patch_paths(avp, monkeypatch, tmp_path)
        # The same file under docs/ and again as an extra MUST be
        # returned only once. Realistically this happens when a doc
        # lives under docs/ but is also listed in DEFAULT_EXTRA.
        target = paths["docs_dir"] / "README.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("dup", encoding="utf-8")
        # Spoof DEFAULT_EXTRA to point at the same realpath.
        monkeypatch.setattr(
            avp, "DEFAULT_EXTRA", [str(target.relative_to(tmp_path))],
        )
        out = avp.collect_docs()
        assert len(out) == 1

    def test_skips_directories_that_match_md_glob(
        self, avp: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # ``rglob('*.md')`` matches *any* path ending in ``.md`` -
        # including directories named ``foo.md``. The walker MUST
        # filter those out via ``p.is_file()``; a regression here
        # would crash when read_text() is later called on a directory.
        paths = _patch_paths(avp, monkeypatch, tmp_path)
        paths["docs_dir"].mkdir(parents=True, exist_ok=True)
        # Directory whose name ends in ``.md`` - covered by glob but
        # is NOT a file.
        (paths["docs_dir"] / "weirdly-named.md").mkdir()
        _write_doc(paths["docs_dir"], "real.md", "real")
        out = avp.collect_docs()
        names = {p.name for p in out}
        assert names == {"real.md"}


# ======================================================================
# 3. clean_prose
# ======================================================================


class TestCleanProse:
    def test_strips_yaml_frontmatter(self, avp: ModuleType) -> None:
        text = "---\ntitle: X\n---\nBody text.\n"
        out = avp.clean_prose(text)
        assert "title: X" not in out
        assert "Body text." in out

    def test_strips_fenced_code_blocks(self, avp: ModuleType) -> None:
        text = "Prose.\n```python\nimport os\n```\nMore prose."
        out = avp.clean_prose(text)
        assert "import os" not in out
        assert "Prose." in out
        assert "More prose." in out

    def test_strips_inline_code(self, avp: ModuleType) -> None:
        text = "Use the `splunk btool` command for Splunk."
        out = avp.clean_prose(text)
        assert "splunk btool" not in out
        assert "Splunk" in out

    def test_strips_autogenerated_sources_block(self, avp: ModuleType) -> None:
        text = (
            "Top.\n"
            "<!-- BEGIN-AUTOGENERATED-SOURCES -->\n"
            "[1] Cisco IOS\n"
            "<!-- END-AUTOGENERATED-SOURCES -->\n"
            "Bottom."
        )
        out = avp.clean_prose(text)
        assert "Cisco IOS" not in out
        assert "Top." in out
        assert "Bottom." in out

    def test_unwraps_markdown_links_keeping_label(
        self, avp: ModuleType
    ) -> None:
        text = "See [Cisco Catalyst](https://example.org/c) docs."
        out = avp.clean_prose(text)
        assert "Cisco Catalyst" in out
        assert "https://example.org/c" not in out

    def test_strips_html_tags(self, avp: ModuleType) -> None:
        text = 'Refs: <sup>[1]</sup> <a id="x">label</a>.'
        out = avp.clean_prose(text)
        assert "<sup>" not in out
        assert "<a" not in out

    def test_preserves_plain_prose(self, avp: ModuleType) -> None:
        text = "Cisco Catalyst 9300 Series ships with IOS-XE."
        out = avp.clean_prose(text)
        assert out == text


# ======================================================================
# 4. tokenise + helpers
# ======================================================================


class TestTokenise:
    def test_splits_on_whitespace_and_records_offset(
        self, avp: ModuleType
    ) -> None:
        toks = avp.tokenise("Cisco  Catalyst\t9300")
        assert [t for t, _ in toks] == ["Cisco", "Catalyst", "9300"]
        # Offsets must be ascending and within the string.
        offsets = [o for _, o in toks]
        assert offsets == sorted(offsets)
        assert all(0 <= o < len("Cisco  Catalyst\t9300") for o in offsets)

    def test_empty_string_returns_empty(self, avp: ModuleType) -> None:
        assert avp.tokenise("") == []

    def test_whitespace_only_returns_empty(self, avp: ModuleType) -> None:
        assert avp.tokenise("   \n\t") == []


class TestIsCapitalised:
    @pytest.mark.parametrize("tok", [
        "Cisco", "Catalyst", "ASA", "ESA", "IOS-XE",
        "Catalyst,", "ASA.",
    ])
    def test_accepts_product_name_tokens(
        self, avp: ModuleType, tok: str
    ) -> None:
        assert avp.is_capitalised(tok)

    @pytest.mark.parametrize("tok", [
        "the", "and", "for", "9300", "134",
        "cisco",  # lower-case = not a fresh capitalised token
    ])
    def test_rejects_lowercase_and_numeric(
        self, avp: ModuleType, tok: str
    ) -> None:
        assert not avp.is_capitalised(tok)

    def test_empty_after_strip_returns_false(self, avp: ModuleType) -> None:
        # A token that's pure trailing punctuation strips to "".
        assert not avp.is_capitalised(".")


class TestIsTerminatingPunct:
    @pytest.mark.parametrize("tok,expected", [
        ("X.", True), ("X,", True), ("X;", True), ("X:", True),
        ("X!", True), ("X?", True), ("X)", True), ("X]", True),
        ("X", False), ("X-", False),
    ])
    def test_recognises_terminators(
        self, avp: ModuleType, tok: str, expected: bool
    ) -> None:
        assert avp.is_terminating_punct(tok) is expected

    def test_empty_token_is_falsy(self, avp: ModuleType) -> None:
        # `is_terminating_punct("")` short-circuits via ``tok and ...``
        # and returns the empty string itself. Pin the falsy-but-not-
        # exactly-False contract so downstream callers can rely on
        # ``if is_terminating_punct(t)``.
        assert not avp.is_terminating_punct("")


class TestNormalisePhrase:
    def test_empty_words_returns_empty_string(self, avp: ModuleType) -> None:
        assert avp.normalise_phrase([]) == ""

    def test_strips_trailing_punctuation_from_last_word(
        self, avp: ModuleType
    ) -> None:
        assert avp.normalise_phrase(["Cisco", "Catalyst", "9300."]) == \
            "Cisco Catalyst 9300"

    def test_collapses_with_single_space(self, avp: ModuleType) -> None:
        assert avp.normalise_phrase(["A", "B", "C"]) == "A B C"


# ======================================================================
# 5. extract_phrases — the heart
# ======================================================================


class TestExtractPhrases:
    def test_emits_anchor_phrase_offset_triples(
        self, avp: ModuleType
    ) -> None:
        out = avp.extract_phrases("Cisco Catalyst Center is good.")
        assert len(out) == 1
        anchor, phrase, offset = out[0]
        assert anchor == "Cisco"
        assert phrase == "Cisco Catalyst Center"
        assert offset >= 0

    def test_no_anchor_returns_empty(self, avp: ModuleType) -> None:
        assert avp.extract_phrases("Hello world how are you.") == []

    def test_anchor_with_no_tail_returns_empty(self, avp: ModuleType) -> None:
        # Anchor followed immediately by a lowercase word means there
        # is no product tail; walker must skip and emit nothing.
        assert avp.extract_phrases("Cisco is great.") == []

    def test_stops_at_lowercase_token(self, avp: ModuleType) -> None:
        out = avp.extract_phrases("Cisco Catalyst is great.")
        assert [p for _, p, _ in out] == ["Cisco Catalyst"]

    def test_stops_at_english_stopword(self, avp: ModuleType) -> None:
        out = avp.extract_phrases("Cisco Catalyst and Meraki ship.")
        assert [p for _, p, _ in out] == ["Cisco Catalyst"]

    def test_stops_at_prose_verb_blacklist(self, avp: ModuleType) -> None:
        out = avp.extract_phrases("Splunk provides everything.")
        # `provides` is blacklisted -> Splunk has no tail
        assert out == []

    def test_stops_at_slash_token(self, avp: ModuleType) -> None:
        out = avp.extract_phrases("Cisco IOS/NX-OS is a list.")
        # IOS/NX-OS contains slash -> walker stops without emitting it.
        assert out == []

    def test_stops_at_uc_id_token(self, avp: ModuleType) -> None:
        out = avp.extract_phrases("Cisco UC-1.2.3 reference.")
        assert out == []

    def test_stops_at_second_anchor(self, avp: ModuleType) -> None:
        # Cisco's tail starts at "Catalyst", then hits "Splunk" - which
        # is itself an anchor - so the walker stops. The phrase emitted
        # MUST NOT contain "Splunk". Then the walker advances and
        # extracts a Splunk phrase independently.
        out = avp.extract_phrases("Cisco Catalyst Splunk Cloud.")
        cisco_phrases = [p for a, p, _ in out if a == "Cisco"]
        splunk_phrases = [p for a, p, _ in out if a == "Splunk"]
        assert cisco_phrases == ["Cisco Catalyst"]
        # Splunk's extraction begins fresh and captures "Cloud".
        assert "Splunk Cloud" in splunk_phrases

    def test_stops_at_terminating_punctuation_in_tail(
        self, avp: ModuleType
    ) -> None:
        out = avp.extract_phrases("Cisco Catalyst, ISE and Meraki ship.")
        # Comma terminator means the tail keeps "Catalyst" but does not
        # extend to ISE.
        assert [p for _, p, _ in out] == ["Cisco Catalyst"]

    def test_respects_max_tail_cap(self, avp: ModuleType) -> None:
        # VENDOR_SURFACES["AWS"] == 3, so the tail must cap there.
        # Use multi-character capitalised tokens (single capital letters
        # fail is_capitalised by design - see TestModuleConstants).
        out = avp.extract_phrases("AWS Probe Alpha Beta Gamma Delta Epsilon.")
        aws_phrases = [p for a, p, _ in out if a == "AWS"]
        # The walker MUST cap the tail at 3 tokens.
        assert aws_phrases
        for p in aws_phrases:
            assert len(p.split()) - 1 <= 3, f"tail too long: {p!r}"
        # And exactly 3 product tokens must follow, not fewer.
        assert "AWS Probe Alpha Beta" in aws_phrases

    def test_matches_multi_word_anchor_red_hat(
        self, avp: ModuleType
    ) -> None:
        out = avp.extract_phrases("Red Hat Enterprise Linux ships.")
        anchors = {a for a, _, _ in out}
        phrases = {p for _, p, _ in out}
        assert "Red Hat" in anchors
        assert "Red Hat Enterprise Linux" in phrases

    def test_matches_multi_word_anchor_palo_alto(
        self, avp: ModuleType
    ) -> None:
        out = avp.extract_phrases("Palo Alto Networks Strata is a firewall.")
        phrases = {p for _, p, _ in out}
        assert "Palo Alto Networks Strata" in phrases

    def test_skips_anchor_after_consuming_phrase(
        self, avp: ModuleType
    ) -> None:
        # After consuming Cisco Catalyst Center, the walker must
        # advance i to j so we don't re-match Center as a new anchor.
        out = avp.extract_phrases("Cisco Catalyst Center is ready.")
        anchors = [a for a, _, _ in out]
        assert anchors.count("Cisco") == 1

    def test_empty_after_punct_breaks_tail(self, avp: ModuleType) -> None:
        # Token whose bare-strip is empty (e.g. "..") terminates the
        # tail with no further extension.
        out = avp.extract_phrases("Cisco .. unrelated.")
        # ".." strips to empty -> bare="" -> break -> tail empty.
        assert out == []

    def test_emits_two_extractions_in_one_doc(
        self, avp: ModuleType
    ) -> None:
        out = avp.extract_phrases(
            "Cisco Catalyst rocks. Splunk Cloud is great."
        )
        assert {a for a, _, _ in out} == {"Cisco", "Splunk"}


# ======================================================================
# 6. load_equipment_allowlist
# ======================================================================


class TestLoadEquipmentAllowlist:
    def test_returns_empty_when_file_missing(
        self, avp: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _patch_paths(avp, monkeypatch, tmp_path)
        assert avp.load_equipment_allowlist() == set()

    def test_flattens_labels_and_model_labels(
        self, avp: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        paths = _patch_paths(avp, monkeypatch, tmp_path)
        payload = {
            "equipment": [
                {
                    "label": "Cisco Catalyst 9300",
                    "models": [
                        {"label": "Cisco Catalyst 9300-48P"},
                        {"label": "Cisco Catalyst 9300-24T"},
                    ],
                },
                {
                    "label": "Splunk Universal Forwarder",
                    "models": [],
                },
            ],
        }
        paths["equipment_index"].parent.mkdir(parents=True, exist_ok=True)
        paths["equipment_index"].write_text(json.dumps(payload), encoding="utf-8")
        out = avp.load_equipment_allowlist()
        assert "cisco catalyst 9300" in out
        assert "cisco catalyst 9300-48p" in out
        assert "splunk universal forwarder" in out

    def test_skips_missing_or_whitespace_labels(
        self, avp: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        paths = _patch_paths(avp, monkeypatch, tmp_path)
        paths["equipment_index"].parent.mkdir(parents=True, exist_ok=True)
        paths["equipment_index"].write_text(json.dumps({
            "equipment": [
                {"label": "   ", "models": [{"label": ""}]},
                {"label": None, "models": [{"label": None}]},
                {"models": [{}]},
            ],
        }), encoding="utf-8")
        assert avp.load_equipment_allowlist() == set()


# ======================================================================
# 7. load_splunkbase_allowlist
# ======================================================================


class TestLoadSplunkbaseAllowlist:
    def test_returns_empty_when_file_missing(
        self, avp: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _patch_paths(avp, monkeypatch, tmp_path)
        assert avp.load_splunkbase_allowlist() == set()

    def test_returns_empty_when_file_is_garbage_json(
        self, avp: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        paths = _patch_paths(avp, monkeypatch, tmp_path)
        paths["splunkbase_catalog"].parent.mkdir(parents=True, exist_ok=True)
        paths["splunkbase_catalog"].write_text("{ broken json", encoding="utf-8")
        assert avp.load_splunkbase_allowlist() == set()

    def test_reads_apps_shape(
        self, avp: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        paths = _patch_paths(avp, monkeypatch, tmp_path)
        paths["splunkbase_catalog"].parent.mkdir(parents=True, exist_ok=True)
        paths["splunkbase_catalog"].write_text(json.dumps({
            "apps": [
                {"id": "1", "title": "Splunk Add-on for Cisco"},
                {"id": "2", "name": "Splunk DB Connect"},
                {"id": "3", "label": "Splunk SOAR App for ServiceNow"},
                {"id": "4"},  # No title/name/label -> skipped
                "not-a-dict",   # Non-dict entry -> skipped
            ],
        }), encoding="utf-8")
        out = avp.load_splunkbase_allowlist()
        assert "splunk add-on for cisco" in out
        assert "splunk db connect" in out
        assert "splunk soar app for servicenow" in out
        assert len(out) == 3  # the broken entries are dropped

    def test_reads_entries_shape(
        self, avp: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        paths = _patch_paths(avp, monkeypatch, tmp_path)
        paths["splunkbase_catalog"].parent.mkdir(parents=True, exist_ok=True)
        paths["splunkbase_catalog"].write_text(json.dumps({
            "entries": [{"title": "Splunk Stream"}],
        }), encoding="utf-8")
        assert avp.load_splunkbase_allowlist() == {"splunk stream"}

    def test_reads_dict_apps_shape(
        self, avp: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # Some Splunkbase mirrors emit {"apps": {"id1": {...}, ...}}
        paths = _patch_paths(avp, monkeypatch, tmp_path)
        paths["splunkbase_catalog"].parent.mkdir(parents=True, exist_ok=True)
        paths["splunkbase_catalog"].write_text(json.dumps({
            "apps": {
                "1": {"title": "Splunk Add-on for AWS"},
                "2": {"title": "Splunk Add-on for Azure"},
            },
        }), encoding="utf-8")
        out = avp.load_splunkbase_allowlist()
        assert out == {
            "splunk add-on for aws",
            "splunk add-on for azure",
        }

    def test_skips_whitespace_titles(
        self, avp: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        paths = _patch_paths(avp, monkeypatch, tmp_path)
        paths["splunkbase_catalog"].parent.mkdir(parents=True, exist_ok=True)
        paths["splunkbase_catalog"].write_text(json.dumps({
            "apps": [{"id": "1", "title": "   "}],
        }), encoding="utf-8")
        assert avp.load_splunkbase_allowlist() == set()


# ======================================================================
# 8. build_allowlist
# ======================================================================


class TestBuildAllowlist:
    def test_returns_one_set_per_known_vendor(
        self, avp: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _patch_paths(avp, monkeypatch, tmp_path)
        out = avp.build_allowlist()
        assert set(out.keys()) == {"Cisco", "Splunk"}

    def test_seeds_curated_baselines(
        self, avp: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _patch_paths(avp, monkeypatch, tmp_path)
        out = avp.build_allowlist()
        # Curated baselines must always be present.
        for entry in avp.CURATED_CISCO:
            assert entry in out["Cisco"]
        for entry in avp.CURATED_SPLUNK:
            assert entry in out["Splunk"]

    def test_enriches_with_equipment_labels(
        self, avp: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        paths = _patch_paths(avp, monkeypatch, tmp_path)
        paths["equipment_index"].parent.mkdir(parents=True, exist_ok=True)
        paths["equipment_index"].write_text(json.dumps({
            "equipment": [
                {"label": "Cisco Made-Up Probe 999", "models": []},
                {"label": "Splunk Made-Up Forwarder X", "models": []},
                # Non-vendor-prefixed labels MUST NOT pollute either set.
                {"label": "Aruba CX 6300", "models": []},
            ],
        }), encoding="utf-8")
        out = avp.build_allowlist()
        assert "cisco made-up probe 999" in out["Cisco"]
        assert "splunk made-up forwarder x" in out["Splunk"]
        # The aruba label MUST NOT show up in either Cisco or Splunk.
        assert "aruba cx 6300" not in out["Cisco"]
        assert "aruba cx 6300" not in out["Splunk"]

    def test_enriches_splunk_with_splunkbase_titles_only(
        self, avp: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        paths = _patch_paths(avp, monkeypatch, tmp_path)
        paths["splunkbase_catalog"].parent.mkdir(parents=True, exist_ok=True)
        paths["splunkbase_catalog"].write_text(json.dumps({
            "apps": [
                {"id": "1", "title": "Splunk Custom Probe"},
                # Splunkbase apps that do NOT start with "Splunk" must
                # NOT pollute the Splunk allowlist.
                {"id": "2", "title": "Cisco-only App"},
            ],
        }), encoding="utf-8")
        out = avp.build_allowlist()
        assert "splunk custom probe" in out["Splunk"]
        assert "cisco-only app" not in out["Splunk"]
        assert "cisco-only app" not in out["Cisco"]


# ======================================================================
# 9. audit — end-to-end
# ======================================================================


class TestAudit:
    def test_full_pipeline_emits_meta_anchor_counts_mentions_suspicious(
        self, avp: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        paths = _patch_paths(avp, monkeypatch, tmp_path)
        doc = _write_doc(
            paths["docs_dir"], "guide.md",
            "Cisco Catalyst Center is fine. Cisco Madeup-Probe Z is not.\n"
            "Splunk Cloud is recognised. Splunk Madeup-Thing Q is not.\n",
        )
        out = avp.audit([doc])
        # Top-level keys frozen.
        assert set(out.keys()) == {
            "_meta", "anchor_counts", "mentions", "suspicious",
        }
        # _meta schema pinned.
        assert out["_meta"]["schemaVersion"] == "1.0"
        # anchor_counts is sorted desc; spot-check Cisco/Splunk present.
        assert out["anchor_counts"]["Cisco"] >= 1
        assert out["anchor_counts"]["Splunk"] >= 1
        # Mentions list is sorted by descending count then by phrase.
        counts = [m["count"] for m in out["mentions"]]
        assert counts == sorted(counts, reverse=True)

    def test_suspicious_only_contains_cisco_or_splunk(
        self, avp: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # Other vendors have no allowlist; their phrases MUST never
        # show up in suspicious.
        paths = _patch_paths(avp, monkeypatch, tmp_path)
        doc = _write_doc(
            paths["docs_dir"], "x.md",
            "Microsoft Made-Up Probe. Datadog Made-Up Probe. AWS Made-Up Probe.\n",
        )
        out = avp.audit([doc])
        assert all(
            s["anchor"] in {"Cisco", "Splunk"} for s in out["suspicious"]
        )

    def test_suspicious_skips_known_prose_noise(
        self, avp: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        paths = _patch_paths(avp, monkeypatch, tmp_path)
        # "Cisco Solution Briefs" extracts cleanly (both tail tokens
        # are capitalised) and the lower-case form is in
        # KNOWN_PROSE_NOISE, so the audit MUST drop it from
        # suspicious - this exercises the "continue" branch in audit().
        doc = _write_doc(
            paths["docs_dir"], "x.md",
            "We publish Cisco Solution Briefs every quarter.\n",
        )
        out = avp.audit([doc])
        # The phrase shows up in mentions (full corpus catalog) but
        # MUST NOT appear in suspicious.
        ment_phrases = {m["phrase"].lower() for m in out["mentions"]}
        susp_phrases = {s["phrase"].lower() for s in out["suspicious"]}
        assert "cisco solution briefs" in ment_phrases
        assert "cisco solution briefs" not in susp_phrases

    def test_suspicious_accepts_multi_token_allowlist_prefix(
        self, avp: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # "Cisco Catalyst Center" extracted from a doc that says
        # "Cisco Catalyst Center Strikeforce" should be accepted
        # because the curated entry "cisco catalyst center" is a
        # multi-token prefix.
        paths = _patch_paths(avp, monkeypatch, tmp_path)
        doc = _write_doc(
            paths["docs_dir"], "x.md",
            "Cisco Catalyst Center Workflow is a real thing.\n",
        )
        out = avp.audit([doc])
        # The phrase emitted is "Cisco Catalyst Center Workflow"; the
        # 3-token curated entry "cisco catalyst center" gates it as
        # NOT suspicious.
        assert all(
            "cisco catalyst center workflow" != s["phrase"].lower()
            for s in out["suspicious"]
        )

    def test_suspicious_rejects_single_token_allowlist_prefix(
        self, avp: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # If the allowlist only held the bare anchor (e.g. "cisco")
        # we MUST NOT silently absolve every "Cisco Foo Bar"
        # extraction. Pin that defence by injecting a single-token
        # allow entry and checking it does NOT clear an unknown phrase.
        paths = _patch_paths(avp, monkeypatch, tmp_path)
        # Add only the bare "cisco" token to the curated baseline.
        monkeypatch.setattr(avp, "CURATED_CISCO", {"cisco"})
        # And empty Splunk so we focus on the Cisco branch.
        monkeypatch.setattr(avp, "CURATED_SPLUNK", set())
        doc = _write_doc(
            paths["docs_dir"], "x.md",
            "Cisco Made-Up Probe ZZ is a fake.\n",
        )
        out = avp.audit([doc])
        # The Cisco extraction MUST still appear as suspicious because
        # the single-token allowlist entry does not gate it.
        assert any(
            s["phrase"].lower() == "cisco made-up probe zz"
            for s in out["suspicious"]
        )

    def test_unreadable_doc_is_skipped(
        self, avp: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        paths = _patch_paths(avp, monkeypatch, tmp_path)
        ok_doc = _write_doc(paths["docs_dir"], "ok.md", "Cisco Catalyst.")
        bogus = paths["docs_dir"] / "missing.md"
        out = avp.audit([ok_doc, bogus])
        # The audit must succeed and process the ok doc.
        assert out["anchor_counts"].get("Cisco", 0) >= 1

    def test_mentions_aggregates_count_and_files(
        self, avp: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        paths = _patch_paths(avp, monkeypatch, tmp_path)
        d1 = _write_doc(
            paths["docs_dir"], "a.md",
            "Cisco Catalyst. Cisco Catalyst again.\n",
        )
        d2 = _write_doc(paths["docs_dir"], "b.md", "Cisco Catalyst.\n")
        out = avp.audit([d1, d2])
        catalyst = [m for m in out["mentions"] if m["phrase"] == "Cisco Catalyst"]
        assert len(catalyst) == 1
        assert catalyst[0]["count"] == 3
        # Files dict is sorted by descending in-file count.
        files = catalyst[0]["files"]
        assert set(files.keys()) == {"docs/a.md", "docs/b.md"}
        assert files["docs/a.md"] == 2  # first file had two mentions
        assert files["docs/b.md"] == 1


# ======================================================================
# 10. _print_summary
# ======================================================================


class TestPrintSummary:
    def test_prints_vendor_anchor_section(
        self, avp: ModuleType, capsys: pytest.CaptureFixture
    ) -> None:
        payload = {
            "anchor_counts": {"Cisco": 5, "Splunk": 3},
            "suspicious": [],
        }
        avp._print_summary(payload, top=10)
        out = capsys.readouterr().out
        assert "Vendor anchors:" in out
        assert "Cisco" in out
        assert "Splunk" in out
        assert "5 mentions" in out
        assert "3 mentions" in out

    def test_prints_suspicious_count(
        self, avp: ModuleType, capsys: pytest.CaptureFixture
    ) -> None:
        payload = {
            "anchor_counts": {},
            "suspicious": [
                {"count": 2, "phrase": "Cisco Made-Up", "files": {}},
            ],
        }
        avp._print_summary(payload, top=10)
        out = capsys.readouterr().out
        assert "1 suspicious phrases" in out
        assert "Cisco Made-Up" in out

    def test_truncates_suspicious_to_top(
        self, avp: ModuleType, capsys: pytest.CaptureFixture
    ) -> None:
        payload = {
            "anchor_counts": {},
            "suspicious": [
                {"count": i, "phrase": f"Cisco P{i}", "files": {}}
                for i in range(50)
            ],
        }
        avp._print_summary(payload, top=3)
        out = capsys.readouterr().out
        # Only the first 3 phrases should be printed in detail.
        assert "Cisco P0" in out
        assert "Cisco P2" in out
        assert "Cisco P40" not in out

    def test_prints_top_three_files_per_phrase(
        self, avp: ModuleType, capsys: pytest.CaptureFixture
    ) -> None:
        payload = {
            "anchor_counts": {},
            "suspicious": [{
                "count": 9,
                "phrase": "Cisco Bogus",
                "files": {
                    "docs/a.md": 5,
                    "docs/b.md": 3,
                    "docs/c.md": 1,
                    "docs/d.md": 1,  # should NOT appear (cap at 3)
                },
            }],
        }
        avp._print_summary(payload, top=10)
        out = capsys.readouterr().out
        assert "docs/a.md" in out
        assert "docs/b.md" in out
        assert "docs/c.md" in out
        assert "docs/d.md" not in out


# ======================================================================
# 11. main() CLI
# ======================================================================


class TestMainWriteMode:
    def test_writes_status_file_and_returns_zero(
        self,
        avp: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
    ) -> None:
        paths = _patch_paths(avp, monkeypatch, tmp_path)
        _write_doc(paths["docs_dir"], "x.md", "Cisco Catalyst.")
        rc = avp.main(argv=[])
        assert rc == 0
        assert paths["status_path"].is_file()
        payload = json.loads(paths["status_path"].read_text(encoding="utf-8"))
        assert payload["_meta"]["schemaVersion"] == "1.0"
        out = capsys.readouterr().out
        assert "Scanning " in out
        assert "Vendor anchors:" in out

    def test_returns_two_when_no_docs(
        self,
        avp: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
    ) -> None:
        _patch_paths(avp, monkeypatch, tmp_path)
        # No docs/ dir, no extras present -> exit code 2.
        rc = avp.main(argv=[])
        assert rc == 2
        out = capsys.readouterr().out
        assert "No prose docs" in out

    def test_strict_exits_one_on_suspicious(
        self,
        avp: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        paths = _patch_paths(avp, monkeypatch, tmp_path)
        _write_doc(
            paths["docs_dir"], "x.md", "Cisco Made-Up Probe ZZ.\n",
        )
        # Lock the allowlist to a single bare-anchor entry so the
        # suspicious queue is guaranteed to contain at least one item.
        monkeypatch.setattr(avp, "CURATED_CISCO", {"cisco"})
        monkeypatch.setattr(avp, "CURATED_SPLUNK", set())
        rc = avp.main(argv=["--strict"])
        assert rc == 1

    def test_strict_exits_zero_on_clean_run(
        self,
        avp: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        paths = _patch_paths(avp, monkeypatch, tmp_path)
        # A doc that contains only allowlisted phrases.
        _write_doc(
            paths["docs_dir"], "x.md",
            "Cisco Catalyst Center is fine.\n",
        )
        rc = avp.main(argv=["--strict"])
        assert rc == 0

    def test_top_flag_shrinks_printed_suspicious_block(
        self,
        avp: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
    ) -> None:
        paths = _patch_paths(avp, monkeypatch, tmp_path)
        # Multiple unique unknown Cisco phrases.
        body = "\n".join(
            f"Cisco Madeup Probe Q{i}.\n" for i in range(10)
        )
        _write_doc(paths["docs_dir"], "x.md", body)
        monkeypatch.setattr(avp, "CURATED_CISCO", {"cisco"})
        monkeypatch.setattr(avp, "CURATED_SPLUNK", set())
        rc = avp.main(argv=["--top", "2"])
        assert rc == 0
        out = capsys.readouterr().out
        # Only the first two phrases should appear in the body.
        assert out.count("Cisco Madeup Probe Q") <= 2


class TestMainReportMode:
    def test_report_uses_existing_status_file(
        self,
        avp: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
    ) -> None:
        paths = _patch_paths(avp, monkeypatch, tmp_path)
        paths["status_path"].parent.mkdir(parents=True, exist_ok=True)
        paths["status_path"].write_text(json.dumps({
            "_meta": {"schemaVersion": "1.0"},
            "anchor_counts": {"Cisco": 99},
            "mentions": [],
            "suspicious": [
                {"count": 1, "phrase": "Cisco Made-Up", "files": {}},
            ],
        }), encoding="utf-8")
        rc = avp.main(argv=["--report"])
        assert rc == 0
        out = capsys.readouterr().out
        # The report mode must NOT re-scan; we should NOT see the
        # "Scanning ..." progress line.
        assert "Scanning " not in out
        # But we must see the summary.
        assert "Cisco" in out
        assert "99 mentions" in out

    def test_report_returns_two_when_status_missing(
        self,
        avp: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
    ) -> None:
        _patch_paths(avp, monkeypatch, tmp_path)
        rc = avp.main(argv=["--report"])
        assert rc == 2
        out = capsys.readouterr().out
        assert "No status file" in out

    def test_report_with_strict_exits_one_on_suspicious(
        self,
        avp: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        paths = _patch_paths(avp, monkeypatch, tmp_path)
        paths["status_path"].parent.mkdir(parents=True, exist_ok=True)
        paths["status_path"].write_text(json.dumps({
            "_meta": {"schemaVersion": "1.0"},
            "anchor_counts": {},
            "mentions": [],
            "suspicious": [
                {"count": 1, "phrase": "Cisco Made-Up", "files": {}},
            ],
        }), encoding="utf-8")
        rc = avp.main(argv=["--report", "--strict"])
        assert rc == 1
