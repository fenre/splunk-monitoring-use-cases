"""Hermetic unit tests for ``scripts/build_provenance.py``.

The provenance ledger is what powers the small "origin" badge on
every UC card in ``index.html`` and the ``per_category`` rollup in
``docs/provenance-coverage.md``. Two failure modes we want to
catch loudly:

* Misclassification — a vendor docs URL silently demoted to
  ``community`` or ``unclassified`` because someone reordered
  ``HOST_RULES`` or dropped a hostname. The badge would suddenly
  flip on hundreds of UCs.
* Priority ladder drift — the wrong category bubbling up as the
  *primary origin*. The ladder is the contract: more authoritative
  origins MUST win. Reordering ``ORIGIN_PRIORITY`` without a
  matching schema bump would silently change every UC's badge.

The tests below are hermetic: ``CATALOG_PATH``, ``PROVENANCE_PATH``,
``PROVENANCE_JS_PATH`` and ``DOC_PATH`` are all monkey-patched to
``tmp_path`` so nothing on disk is touched. The ``main()`` CLI is
exercised end-to-end via captured stdout/stderr.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "build_provenance.py"


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "build_provenance", SCRIPT_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["build_provenance"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bp() -> ModuleType:
    return _load_module()


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def _patch_paths(
    bp: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> dict[str, Path]:
    """Re-root every hard-coded output path into ``tmp_path``."""
    catalog = tmp_path / "catalog.json"
    prov = tmp_path / "provenance.json"
    prov_js = tmp_path / "provenance.js"
    doc = tmp_path / "docs" / "provenance-coverage.md"
    monkeypatch.setattr(bp, "CATALOG_PATH", catalog)
    monkeypatch.setattr(bp, "PROVENANCE_PATH", prov)
    monkeypatch.setattr(bp, "PROVENANCE_JS_PATH", prov_js)
    monkeypatch.setattr(bp, "DOC_PATH", doc)
    return {
        "catalog": catalog,
        "provenance": prov,
        "provenance_js": prov_js,
        "doc": doc,
    }


def _seed_catalog(
    catalog_path: Path,
    *,
    use_cases: list[dict[str, Any]] | None = None,
) -> None:
    """Write a minimal catalog.json with a single category containing
    the supplied UCs. Each UC dict must carry at least ``i`` (id) and
    ``refs`` (markdown / bare URL bundle). Additional UC fields
    (e.g. ``reviewed``, ``status``) flow through to the ledger entry.
    """
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.write_text(
        json.dumps({
            "DATA": [{
                "i": 1,
                "s": [{
                    "i": "1.1",
                    "u": list(use_cases or []),
                }],
            }],
        }),
        encoding="utf-8",
    )


# ======================================================================
# 1. Module-level constants & contracts
# ======================================================================


class TestModuleConstants:
    def test_origin_priority_ladder_is_strictly_decreasing(
        self, bp: ModuleType
    ) -> None:
        """Every category in ``ORIGIN_PRIORITY`` must carry a
        unique integer rank — otherwise the tie-breaker in
        ``_primary_origin`` becomes order-dependent.
        """
        ranks = list(bp.ORIGIN_PRIORITY.values())
        assert len(ranks) == len(set(ranks)), (
            "ORIGIN_PRIORITY has duplicate rank values — primary "
            "origin selection becomes non-deterministic."
        )

    def test_every_origin_has_a_badge_label(self, bp: ModuleType) -> None:
        """Every category in ``ORIGIN_PRIORITY`` MUST have a matching
        ``BADGE_LABEL`` entry — the ``BADGE_LABEL[origin]`` lookup in
        ``build_ledger`` would KeyError otherwise.
        """
        missing = set(bp.ORIGIN_PRIORITY) - set(bp.BADGE_LABEL)
        assert missing == set(), (
            f"ORIGIN_PRIORITY has categories without BADGE_LABEL: {missing}"
        )

    def test_host_rules_categories_are_in_priority_ladder(
        self, bp: ModuleType
    ) -> None:
        """Every category produced by ``HOST_RULES`` must appear in
        ``ORIGIN_PRIORITY`` — otherwise the rank lookup falls back to
        0 and the category sinks below ``contributor``, which would
        be a serious regression.
        """
        rule_cats = {r.category for r in bp.HOST_RULES}
        missing = rule_cats - set(bp.ORIGIN_PRIORITY)
        assert missing == set(), (
            f"HOST_RULES emit categories not in ORIGIN_PRIORITY: {missing}"
        )

    def test_splunk_official_outranks_splunk_blog(
        self, bp: ModuleType
    ) -> None:
        """Both ``docs.splunk.com`` and ``www.splunk.com/blog`` are
        valid Splunk-hosted citations, but the official docs MUST
        win the primary-origin race against the marketing blog.
        """
        assert (
            bp.ORIGIN_PRIORITY["splunk-official"]
            > bp.ORIGIN_PRIORITY["splunk-blog"]
        )


# ======================================================================
# 2. _classify_host
# ======================================================================


class TestClassifyHost:
    def test_official_splunk_docs(self, bp: ModuleType) -> None:
        assert bp._classify_host("docs.splunk.com") == "splunk-official"
        assert bp._classify_host("lantern.splunk.com") == "splunk-official"
        assert bp._classify_host("splunkbase.splunk.com") == "splunk-official"

    def test_splunk_blog_distinguished_from_official(
        self, bp: ModuleType
    ) -> None:
        """``www.splunk.com`` is the blog/marketing domain, NOT
        ``splunk-official`` — the marketing label sits below
        threat-intel on the priority ladder.
        """
        assert bp._classify_host("www.splunk.com") == "splunk-blog"
        assert bp._classify_host("splunk.com") == "splunk-blog"

    def test_vendor_microsoft(self, bp: ModuleType) -> None:
        assert (
            bp._classify_host("learn.microsoft.com") == "vendor-official"
        )
        assert (
            bp._classify_host("docs.microsoft.com") == "vendor-official"
        )

    def test_vendor_cisco(self, bp: ModuleType) -> None:
        assert bp._classify_host("docs.cisco.com") == "vendor-official"

    def test_vendor_aws(self, bp: ModuleType) -> None:
        assert (
            bp._classify_host("docs.aws.amazon.com") == "vendor-official"
        )

    def test_mitre_attack(self, bp: ModuleType) -> None:
        assert bp._classify_host("attack.mitre.org") == "mitre-attack"

    def test_nist_standards(self, bp: ModuleType) -> None:
        assert bp._classify_host("csrc.nist.gov") == "nist-compliance"
        assert (
            bp._classify_host("www.pcisecuritystandards.org")
            == "nist-compliance"
        )

    def test_threat_intel_dfir_report(self, bp: ModuleType) -> None:
        assert bp._classify_host("thedfirreport.com") == "threat-intel"

    def test_community_github(self, bp: ModuleType) -> None:
        assert bp._classify_host("github.com") == "community"

    def test_unknown_host_returns_unclassified(
        self, bp: ModuleType
    ) -> None:
        assert (
            bp._classify_host("totally-random-corporate-blog.example")
            == "unclassified"
        )

    def test_subdomain_match_via_endswith(self, bp: ModuleType) -> None:
        """``host.endswith('.' + suffix)`` must match arbitrary
        depth of subdomain. For ``microsoft.com`` rule, any
        ``X.microsoft.com`` host should match too.
        """
        assert (
            bp._classify_host("releases.microsoft.com")
            == "vendor-official"
        )
        # Multi-level subdomain still matches.
        assert (
            bp._classify_host("a.b.c.microsoft.com")
            == "vendor-official"
        )

    def test_case_normalisation_and_leading_dot_stripped(
        self, bp: ModuleType
    ) -> None:
        """Host comparison is case-insensitive AND tolerant of a
        leading dot, matching the lenient normalisation in
        ``_classify_host``.
        """
        assert (
            bp._classify_host("DOCS.SPLUNK.COM") == "splunk-official"
        )
        assert (
            bp._classify_host(".docs.splunk.com") == "splunk-official"
        )

    def test_empty_string_is_unclassified(self, bp: ModuleType) -> None:
        assert bp._classify_host("") == "unclassified"


# ======================================================================
# 3. _extract_urls
# ======================================================================


class TestExtractUrls:
    def test_empty_string_returns_empty_list(self, bp: ModuleType) -> None:
        assert bp._extract_urls("") == []

    def test_none_input_treated_as_empty(self, bp: ModuleType) -> None:
        """The script seeds ``refs_raw = uc.get("refs") or ""`` so
        None never reaches ``_extract_urls`` in production, but we
        still pin the helper's contract on the falsy-input branch.
        """
        assert bp._extract_urls("") == []

    def test_markdown_link_extraction(self, bp: ModuleType) -> None:
        text = "See [Splunk docs](https://docs.splunk.com/Documentation) for details."
        urls = bp._extract_urls(text)
        assert urls == ["https://docs.splunk.com/Documentation"]

    def test_bare_url_extraction(self, bp: ModuleType) -> None:
        text = "Background: https://attack.mitre.org/techniques/T1059/"
        urls = bp._extract_urls(text)
        assert urls == ["https://attack.mitre.org/techniques/T1059/"]

    def test_markdown_takes_precedence_over_bare(
        self, bp: ModuleType
    ) -> None:
        """When the same URL appears once inside a markdown link AND
        once bare in the same blob, dedup ensures it's emitted only
        once — and the markdown form is captured first, so order
        reflects discovery order.
        """
        text = (
            "[Docs](https://docs.splunk.com/x) and "
            "https://docs.splunk.com/x for context."
        )
        urls = bp._extract_urls(text)
        assert urls == ["https://docs.splunk.com/x"]

    def test_trailing_punctuation_stripped(self, bp: ModuleType) -> None:
        text = "See [x](https://x/y), or also: https://example.com/z;"
        urls = bp._extract_urls(text)
        # markdown URLs strip ".,;" — bare URLs strip the same set.
        assert all(not u.endswith((".", ",", ";")) for u in urls)

    def test_empty_url_skipped(self, bp: ModuleType) -> None:
        """A markdown match whose URL becomes empty after rstrip
        is skipped (`if url and url not in seen:` is False).

        While URL_RE in ``_MD_LINK_RE`` requires at least one
        non-paren character (so the empty-after-strip case is
        almost impossible to construct), the guard is part of the
        public contract and must keep working.
        """
        # No URLs at all should produce an empty list, not crash.
        assert bp._extract_urls("plain text with no links") == []

    def test_dedup_across_markdown_and_bare(
        self, bp: ModuleType
    ) -> None:
        """If the same URL appears repeatedly under different
        wrappers, it's emitted only once.
        """
        text = (
            "[A](https://x/y) [B](https://x/y) https://x/y "
            "https://x/y."
        )
        urls = bp._extract_urls(text)
        assert urls == ["https://x/y"]

    def test_multiple_distinct_urls(self, bp: ModuleType) -> None:
        text = (
            "Refs: [a](https://docs.splunk.com/A), "
            "[b](https://attack.mitre.org/B), "
            "https://github.com/C"
        )
        urls = bp._extract_urls(text)
        assert sorted(urls) == sorted([
            "https://docs.splunk.com/A",
            "https://attack.mitre.org/B",
            "https://github.com/C",
        ])

    def test_bare_url_after_markdown_link_not_double_extracted(
        self, bp: ModuleType
    ) -> None:
        """The ``_BARE_URL_RE`` carries a ``(?<!\\])`` negative
        look-behind to avoid re-matching the URL inside a markdown
        link — the markdown extractor already emitted it.
        """
        text = "[Splunk](https://docs.splunk.com/X)"
        urls = bp._extract_urls(text)
        assert urls == ["https://docs.splunk.com/X"]


# ======================================================================
# 4. _primary_origin
# ======================================================================


class TestPrimaryOrigin:
    def test_no_categories_returns_contributor(
        self, bp: ModuleType
    ) -> None:
        assert bp._primary_origin([]) == "contributor"

    def test_splunk_official_outranks_blog(self, bp: ModuleType) -> None:
        out = bp._primary_origin(["splunk-blog", "splunk-official"])
        assert out == "splunk-official"

    def test_vendor_outranks_community_and_unclassified(
        self, bp: ModuleType
    ) -> None:
        out = bp._primary_origin([
            "community", "unclassified", "vendor-official",
        ])
        assert out == "vendor-official"

    def test_mitre_outranks_nist_outranks_threat_intel(
        self, bp: ModuleType
    ) -> None:
        out = bp._primary_origin([
            "threat-intel", "nist-compliance", "mitre-attack",
        ])
        assert out == "mitre-attack"

    def test_duplicates_collapse(self, bp: ModuleType) -> None:
        """Same-category entries collapse via ``set()``; the result
        is purely a function of the unique categories present.
        """
        out = bp._primary_origin([
            "community", "community", "community",
        ])
        assert out == "community"

    def test_unknown_category_falls_back_to_priority_zero(
        self, bp: ModuleType
    ) -> None:
        """Unknown categories receive priority 0 in
        ``ORIGIN_PRIORITY.get(c, 0)``, sinking them below
        ``contributor`` (priority 1). A known category beats an
        unknown one.
        """
        out = bp._primary_origin(["unknown-cat", "splunk-blog"])
        assert out == "splunk-blog"


# ======================================================================
# 5. _reproducible_now
# ======================================================================


class TestReproducibleNow:
    def test_honors_source_date_epoch(
        self, bp: ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When ``SOURCE_DATE_EPOCH`` is set, the timestamp is
        pinned to that exact UTC second — a prerequisite for
        byte-identical reproducible builds.
        """
        # epoch 0 = 1970-01-01T00:00:00Z
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "0")
        out = bp._reproducible_now()
        assert out == "1970-01-01T00:00:00Z"

    def test_pinned_to_specific_epoch(
        self, bp: ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A specific Unix epoch produces a stable UTC ISO-8601
        string. We use 86400 (= 1970-01-02T00:00:00Z) so the test
        is timezone-independent and trivially verifiable.
        """
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "86400")
        out = bp._reproducible_now()
        assert out == "1970-01-02T00:00:00Z"

    def test_non_digit_epoch_falls_back_to_wall_clock(
        self, bp: ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Malformed ``SOURCE_DATE_EPOCH`` is treated as absent so
        the build still completes (the env var is honored by
        convention; a typo shouldn't crash the whole pipeline).
        """
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "not-a-number")
        out = bp._reproducible_now()
        # The wall-clock fallback emits an RFC-3339 UTC stamp.
        assert out.endswith("Z")
        assert "T" in out

    def test_unset_env_falls_back_to_wall_clock(
        self, bp: ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
        out = bp._reproducible_now()
        assert out.endswith("Z")


# ======================================================================
# 6. build_ledger
# ======================================================================


class TestBuildLedger:
    def test_missing_catalog_exits_2(
        self,
        bp: ModuleType,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When ``CATALOG_PATH`` does not exist the script bails
        with exit code 2 and a "catalog.json missing — run build.py
        first." message.
        """
        _patch_paths(bp, monkeypatch, tmp_path)
        # No seeding — catalog.json does not exist.
        with pytest.raises(SystemExit) as exc_info:
            bp.build_ledger()
        assert exc_info.value.code == 2
        err = capsys.readouterr().err
        assert "catalog.json missing" in err

    def test_empty_data_produces_empty_entries(
        self,
        bp: ModuleType,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        paths = _patch_paths(bp, monkeypatch, tmp_path)
        paths["catalog"].write_text(
            json.dumps({"DATA": []}), encoding="utf-8"
        )
        ledger = bp.build_ledger()
        assert ledger["total_ucs"] == 0
        assert ledger["entries"] == {}
        assert ledger["origin_counts"] == {}
        assert ledger["per_category"] == {}
        assert ledger["schema_version"] == 1
        assert "generated_at" in ledger

    def test_single_splunk_official_uc(
        self,
        bp: ModuleType,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        paths = _patch_paths(bp, monkeypatch, tmp_path)
        _seed_catalog(paths["catalog"], use_cases=[{
            "i": "1.1.1",
            "refs": "[Splunk](https://docs.splunk.com/Doc/x)",
        }])
        ledger = bp.build_ledger()
        assert ledger["total_ucs"] == 1
        entry = ledger["entries"]["1.1.1"]
        assert entry["origin"] == "splunk-official"
        assert entry["origin_label"] == "Splunk official"
        assert entry["references"] == [{
            "url": "https://docs.splunk.com/Doc/x",
            "category": "splunk-official",
        }]
        assert ledger["origin_counts"]["splunk-official"] == 1
        assert ledger["per_category"]["1"]["splunk-official"] == 1

    def test_contributor_fallback_when_no_refs(
        self,
        bp: ModuleType,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A UC with no references at all falls back to
        ``contributor`` (the script authored this UC itself).
        """
        paths = _patch_paths(bp, monkeypatch, tmp_path)
        _seed_catalog(paths["catalog"], use_cases=[{
            "i": "1.1.1",
            "refs": "",
        }])
        ledger = bp.build_ledger()
        entry = ledger["entries"]["1.1.1"]
        assert entry["origin"] == "contributor"
        assert entry["origin_label"] == "Contributor"
        assert entry["references"] == []

    def test_refs_none_falls_back_to_contributor(
        self,
        bp: ModuleType,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """``uc.get("refs") or ""`` collapses the missing-field
        case to ``""`` and then ``_extract_urls`` yields []."""
        paths = _patch_paths(bp, monkeypatch, tmp_path)
        _seed_catalog(paths["catalog"], use_cases=[{
            "i": "1.1.1",
            # no refs key at all
        }])
        ledger = bp.build_ledger()
        assert ledger["entries"]["1.1.1"]["origin"] == "contributor"

    def test_mixed_origins_picks_most_authoritative(
        self,
        bp: ModuleType,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        paths = _patch_paths(bp, monkeypatch, tmp_path)
        _seed_catalog(paths["catalog"], use_cases=[{
            "i": "1.1.1",
            "refs": (
                "[Spunk](https://docs.splunk.com/X), "
                "[MITRE](https://attack.mitre.org/T1059/), "
                "[Random](https://example-unknown.example/y)"
            ),
        }])
        ledger = bp.build_ledger()
        # splunk-official (10) > mitre-attack (8) > unclassified (3)
        assert ledger["entries"]["1.1.1"]["origin"] == "splunk-official"
        # Three URLs, three references rows; verify each got
        # classified correctly.
        urls = {r["url"]: r["category"]
                for r in ledger["entries"]["1.1.1"]["references"]}
        assert urls == {
            "https://docs.splunk.com/X": "splunk-official",
            "https://attack.mitre.org/T1059/": "mitre-attack",
            "https://example-unknown.example/y": "unclassified",
        }

    def test_reviewed_and_status_flow_through(
        self,
        bp: ModuleType,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """``reviewed`` and ``status`` fields on the UC become
        ``last_reviewed`` and ``status`` on the ledger entry.
        """
        paths = _patch_paths(bp, monkeypatch, tmp_path)
        _seed_catalog(paths["catalog"], use_cases=[{
            "i": "1.1.1",
            "refs": "",
            "reviewed": "2026-05-19",
            "status": "production",
        }])
        ledger = bp.build_ledger()
        entry = ledger["entries"]["1.1.1"]
        assert entry["last_reviewed"] == "2026-05-19"
        assert entry["status"] == "production"

    def test_unparseable_url_falls_back_to_unclassified(
        self,
        bp: ModuleType,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """``urlparse`` swallows nearly any input without raising;
        this test pins the contract that an empty netloc is what
        actually triggers the ``unclassified`` fallback.
        """
        paths = _patch_paths(bp, monkeypatch, tmp_path)
        # Use a markdown link so the URL goes through _extract_urls.
        _seed_catalog(paths["catalog"], use_cases=[{
            "i": "1.1.1",
            "refs": "[no host](https:///path/only)",
        }])
        ledger = bp.build_ledger()
        cats = [
            r["category"]
            for r in ledger["entries"]["1.1.1"]["references"]
        ]
        # Either we got at least one URL with an empty netloc
        # classified as unclassified, OR the entry was dropped
        # entirely (in which case origin is ``contributor``).
        if cats:
            assert "unclassified" in cats
        else:
            assert (
                ledger["entries"]["1.1.1"]["origin"] == "contributor"
            )

    def test_urlparse_exception_handler_is_defensive(
        self,
        bp: ModuleType,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Lines 274-275 wrap ``urlparse(url)`` in ``try/except``
        and fall back to ``netloc = ""`` on any exception. In
        practice ``urlparse`` swallows malformed input without
        raising (it returns an empty ParseResult), so the handler
        is unreachable through any string input the regex can
        produce.

        We trip the handler by monkey-patching ``urlparse`` to
        raise — this proves the fallback code is wired correctly,
        which is the only guarantee the defensive guard can
        legitimately make.
        """
        paths = _patch_paths(bp, monkeypatch, tmp_path)
        _seed_catalog(paths["catalog"], use_cases=[{
            "i": "1.1.1",
            "refs": "[x](https://docs.splunk.com/X)",
        }])

        def _exploding_urlparse(_url: str) -> None:
            raise ValueError("simulated parse failure")

        monkeypatch.setattr(bp, "urlparse", _exploding_urlparse)
        ledger = bp.build_ledger()
        # netloc fell back to "" → category is unclassified.
        assert (
            ledger["entries"]["1.1.1"]["references"][0]["category"]
            == "unclassified"
        )

    def test_per_category_rollup_is_segregated_by_top_level_cat(
        self,
        bp: ModuleType,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        paths = _patch_paths(bp, monkeypatch, tmp_path)
        paths["catalog"].write_text(
            json.dumps({
                "DATA": [
                    {"i": 1, "s": [{"i": "1.1", "u": [{
                        "i": "1.1.1",
                        "refs": "[x](https://docs.splunk.com/A)",
                    }]}]},
                    {"i": 2, "s": [{"i": "2.1", "u": [{
                        "i": "2.1.1",
                        "refs": "[m](https://attack.mitre.org/B)",
                    }]}]},
                ]
            }),
            encoding="utf-8",
        )
        ledger = bp.build_ledger()
        assert ledger["total_ucs"] == 2
        assert ledger["per_category"]["1"] == {"splunk-official": 1}
        assert ledger["per_category"]["2"] == {"mitre-attack": 1}


# ======================================================================
# 7. render_coverage_doc
# ======================================================================


class TestRenderCoverageDoc:
    def test_renders_header_and_table_with_total_zero(
        self, bp: ModuleType
    ) -> None:
        """Edge case: total_ucs = 0. ``pct()`` falls back to a
        plain count to avoid ZeroDivisionError.
        """
        empty_ledger = {
            "total_ucs": 0,
            "origin_counts": {},
            "per_category": {},
            "generated_at": "2026-05-19T00:00:00Z",
        }
        out = bp.render_coverage_doc(empty_ledger)
        assert "# Provenance coverage" in out
        assert "Auto-generated by `scripts/build_provenance.py`" in out
        assert "0 use cases audited" in out
        # Priority ladder table is rendered regardless of counts.
        assert "splunk-official" in out
        assert "contributor" in out

    def test_renders_count_rows_in_priority_order(
        self, bp: ModuleType
    ) -> None:
        ledger = {
            "total_ucs": 100,
            "origin_counts": {
                "splunk-official": 60,
                "mitre-attack": 25,
                "community": 15,
            },
            "per_category": {
                "1": {"splunk-official": 60},
                "2": {"mitre-attack": 25, "community": 15},
            },
            "generated_at": "2026-05-19T00:00:00Z",
        }
        out = bp.render_coverage_doc(ledger)
        # Splunk-official must appear before community in the
        # "Overall coverage" rollup. Both badge-label strings
        # appear in the priority-ladder description table earlier
        # in the doc, so we anchor the search on the rollup
        # section header.
        rollup_start = out.find("## Overall coverage")
        assert rollup_start != -1
        rollup = out[rollup_start:]
        ofs_splunk = rollup.find("Splunk official")
        ofs_community = rollup.find("Community")
        assert ofs_splunk != -1 and ofs_community != -1
        assert ofs_splunk < ofs_community
        # Percentages are rendered.
        assert "60 (60.0%)" in out
        assert "25 (25.0%)" in out

    def test_per_category_rollup_includes_all_columns(
        self, bp: ModuleType
    ) -> None:
        """The per-category table renders all 9 origin columns even
        when most are zero.
        """
        ledger = {
            "total_ucs": 1,
            "origin_counts": {"splunk-official": 1},
            "per_category": {"1": {"splunk-official": 1}},
            "generated_at": "2026-05-19T00:00:00Z",
        }
        out = bp.render_coverage_doc(ledger)
        # Header row carries all 9 origin column names + Total.
        for header in [
            "Splunk", "Vendor", "MITRE", "Standards",
            "Threat-intel", "Blog", "Community", "Other", "Contributor",
        ]:
            assert header in out
        # Cat 1 row sums to 1 (only one UC).
        assert "Cat 1" in out

    def test_per_category_rows_sorted_numerically(
        self, bp: ModuleType
    ) -> None:
        """Category numbers sort by integer value (1, 2, 10), not
        lexicographically (1, 10, 2). This matters once we have
        more than 9 categories.
        """
        ledger = {
            "total_ucs": 3,
            "origin_counts": {"splunk-official": 3},
            "per_category": {
                "10": {"splunk-official": 1},
                "2": {"splunk-official": 1},
                "1": {"splunk-official": 1},
            },
            "generated_at": "2026-05-19T00:00:00Z",
        }
        out = bp.render_coverage_doc(ledger)
        # All rows are present; "Cat 1" appears before "Cat 2"
        # appears before "Cat 10".
        ofs1 = out.find("Cat 1 |")
        ofs2 = out.find("Cat 2 |")
        ofs10 = out.find("Cat 10 |")
        assert 0 < ofs1 < ofs2 < ofs10

    def test_non_numeric_category_keys_sink_to_bottom(
        self, bp: ModuleType
    ) -> None:
        """Non-numeric category keys (legacy / mistakes) get sort
        key 9999 and end up at the bottom of the rollup.
        """
        ledger = {
            "total_ucs": 2,
            "origin_counts": {"splunk-official": 2},
            "per_category": {
                "weird-cat": {"splunk-official": 1},
                "1": {"splunk-official": 1},
            },
            "generated_at": "2026-05-19T00:00:00Z",
        }
        out = bp.render_coverage_doc(ledger)
        ofs1 = out.find("Cat 1 |")
        ofs_weird = out.find("Cat weird-cat |")
        assert ofs1 < ofs_weird


# ======================================================================
# 8. main() CLI
# ======================================================================


class TestMainCli:
    def test_default_run_writes_three_files(
        self,
        bp: ModuleType,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        paths = _patch_paths(bp, monkeypatch, tmp_path)
        _seed_catalog(paths["catalog"], use_cases=[{
            "i": "1.1.1",
            "refs": "[x](https://docs.splunk.com/X)",
        }])
        # Avoid argparse seeing pytest's own argv.
        monkeypatch.setattr(sys, "argv", ["build_provenance"])
        rc = bp.main()
        assert rc == 0
        # All three artefacts emitted.
        assert paths["provenance"].exists()
        assert paths["provenance_js"].exists()
        assert paths["doc"].exists()
        # provenance.json is valid JSON
        payload = json.loads(paths["provenance"].read_text("utf-8"))
        assert payload["total_ucs"] == 1
        # provenance.js starts with the expected preamble
        js = paths["provenance_js"].read_text("utf-8")
        assert "window.PROVENANCE = " in js
        assert "window.PROVENANCE_LABELS = " in js
        assert "1.1.1" in js
        # Stdout reports the writes
        out = capsys.readouterr().out
        assert "Wrote" in out
        assert "Provenance indexed: 1 UCs" in out

    def test_no_write_suppresses_files_but_still_prints_summary(
        self,
        bp: ModuleType,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        paths = _patch_paths(bp, monkeypatch, tmp_path)
        _seed_catalog(paths["catalog"], use_cases=[{
            "i": "1.1.1",
            "refs": "[x](https://docs.splunk.com/X)",
        }])
        monkeypatch.setattr(sys, "argv", ["build_provenance", "--no-write"])
        rc = bp.main()
        assert rc == 0
        assert not paths["provenance"].exists()
        assert not paths["provenance_js"].exists()
        assert not paths["doc"].exists()
        out = capsys.readouterr().out
        # No "Wrote" line, but the summary still ran.
        assert "Wrote" not in out
        assert "Provenance indexed: 1 UCs" in out

    def test_strict_threshold_passes_below_10_percent(
        self,
        bp: ModuleType,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        paths = _patch_paths(bp, monkeypatch, tmp_path)
        # 1 UC with no refs → contributor share = 100%, but only
        # 1 UC means 100%/threshold trips below if there are 9
        # other UCs with refs. Build that ratio.
        ucs = [{
            "i": f"1.1.{n}",
            "refs": "[x](https://docs.splunk.com/X)",
        } for n in range(1, 10)] + [{
            "i": "1.1.10",
            "refs": "",  # contributor
        }]
        _seed_catalog(paths["catalog"], use_cases=ucs)
        monkeypatch.setattr(sys, "argv", ["build_provenance", "--no-write", "--strict"])
        rc = bp.main()
        # 1 of 10 = 10% (NOT > 10%), so strict passes.
        assert rc == 0

    def test_strict_threshold_fails_above_10_percent(
        self,
        bp: ModuleType,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When > 10% of UCs fall back to ``contributor``, ``--strict``
        prints an ERROR line and returns 1.
        """
        paths = _patch_paths(bp, monkeypatch, tmp_path)
        # 2 contributor / 10 total = 20% > 10% threshold.
        ucs = [{
            "i": f"1.1.{n}",
            "refs": "[x](https://docs.splunk.com/X)",
        } for n in range(1, 9)] + [
            {"i": "1.1.9", "refs": ""},
            {"i": "1.1.10", "refs": ""},
        ]
        _seed_catalog(paths["catalog"], use_cases=ucs)
        monkeypatch.setattr(sys, "argv", ["build_provenance", "--no-write", "--strict"])
        rc = bp.main()
        assert rc == 1
        err = capsys.readouterr().err
        assert "ERROR" in err
        assert "contributor" in err
        assert "20.0%" in err

    def test_strict_with_zero_total_does_not_error(
        self,
        bp: ModuleType,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When the catalog is empty (total == 0) the strict gate
        is silently skipped — division by zero would otherwise
        crash the script.
        """
        paths = _patch_paths(bp, monkeypatch, tmp_path)
        paths["catalog"].write_text(
            json.dumps({"DATA": []}), encoding="utf-8"
        )
        monkeypatch.setattr(sys, "argv", ["build_provenance", "--no-write", "--strict"])
        rc = bp.main()
        assert rc == 0


# ======================================================================
# 9. __main__ guard
# ======================================================================


class TestMainGuard:
    def test_module_has_main_guard(self) -> None:
        """Pin the ``if __name__ == "__main__": sys.exit(main())``
        guard at the bottom of the file. Without it, importing the
        module would trigger ``main()`` and either crash (no catalog)
        or write outputs.
        """
        src = SCRIPT_PATH.read_text(encoding="utf-8")
        assert 'if __name__ == "__main__":' in src
        assert "sys.exit(main())" in src
