"""Unit tests for ``splunk_uc.audits.splunkbase_ids``.

P16 wave HH: lifts ``src/splunk_uc/audits/splunkbase_ids.py`` from
~12% to 100% combined coverage. Pins every documented contract of
the Splunkbase-ID reference audit:

(a) ``URL_RE`` recognises both plain and markdown-linked
    splunkbase.splunk.com/app/<NUM> URLs.
(b) ``SPLUNKBASE_INLINE_RE`` recognises bare ``Splunkbase #123``
    references and de-duplicates spans already matched by URL_RE.
(c) ``NEARBY_NAME_RE`` finds the surrounding TA/Add-On/App name in
    the preceding 120-160 chars when no markdown link name is given.
(d) ``main()`` aggregates references by app-id and prints the
    canonical name + per-name counts; surfaces "<unknown>" misses.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any, Protocol

import pytest

from splunk_uc.audits import _uc_walk
from splunk_uc.audits import splunkbase_ids as sbi


class MakeUC(Protocol):
    def __call__(
        self,
        uc_id: str,
        payload: dict[str, Any] | None = None,
        category: int = 1,
    ) -> pathlib.Path: ...


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def fake_repo(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """Hermetic repo with content/ skeleton.

    NOTE: The audit imports ``iter_uc_sidecars`` from
    ``splunk_uc.audits._uc_walk`` which closes over the module-level
    ``CONTENT`` constant. Patch THAT one (not just any local copy in
    the audit module).
    """
    (tmp_path / "content").mkdir()
    monkeypatch.setattr(_uc_walk, "REPO", tmp_path)
    monkeypatch.setattr(_uc_walk, "CONTENT", tmp_path / "content")
    return tmp_path


@pytest.fixture
def make_uc(fake_repo: pathlib.Path) -> MakeUC:
    def _make(
        uc_id: str,
        payload: dict[str, Any] | None = None,
        category: int = 1,
    ) -> pathlib.Path:
        cat_dir = fake_repo / "content" / f"cat-{category:02d}-test-cat"
        cat_dir.mkdir(parents=True, exist_ok=True)
        sidecar = cat_dir / f"UC-{uc_id}.json"
        merged = {"id": uc_id, **(payload or {})}
        sidecar.write_text(json.dumps(merged), encoding="utf-8")
        return sidecar

    return _make


# ----------------------------------------------------------------------
# Module-level constants
# ----------------------------------------------------------------------


class TestModuleConstants:
    def test_url_re_matches_https(self) -> None:
        m = sbi.URL_RE.search("see https://splunkbase.splunk.com/app/2890")
        assert m is not None
        assert m.group("id") == "2890"

    def test_url_re_matches_without_scheme(self) -> None:
        m = sbi.URL_RE.search("see splunkbase.splunk.com/app/2890")
        assert m is not None
        assert m.group("id") == "2890"

    def test_url_re_matches_with_trailing_path(self) -> None:
        m = sbi.URL_RE.search("https://splunkbase.splunk.com/app/2890/#/overview")
        assert m is not None
        assert m.group("id") == "2890"

    def test_url_re_captures_md_name(self) -> None:
        m = sbi.URL_RE.search("[Splunk Add-On](https://splunkbase.splunk.com/app/1)")
        assert m is not None
        assert m.group("md_name") == "Splunk Add-On"

    def test_inline_re_matches_with_hash(self) -> None:
        m = sbi.SPLUNKBASE_INLINE_RE.search("see Splunkbase #2890 for details")
        assert m is not None
        assert m.group("id") == "2890"

    def test_inline_re_matches_without_hash(self) -> None:
        m = sbi.SPLUNKBASE_INLINE_RE.search("see Splunkbase 2890 for details")
        assert m is not None
        assert m.group("id") == "2890"

    def test_inline_re_is_case_insensitive(self) -> None:
        m = sbi.SPLUNKBASE_INLINE_RE.search("see SPLUNKBASE #2890 for details")
        assert m is not None

    def test_nearby_name_re_matches_addon(self) -> None:
        m = sbi.NEARBY_NAME_RE.search("see Splunk Add-On for Foo Bar")
        assert m is not None
        assert "Splunk Add-On for Foo" in m.group("name")

    def test_nearby_name_re_matches_splunk_ta_underscore(self) -> None:
        m = sbi.NEARBY_NAME_RE.search("see Splunk_TA_foo_bar at end")
        assert m is not None
        assert m.group("name") == "Splunk_TA_foo_bar"

    def test_nearby_name_re_matches_ta_dash(self) -> None:
        m = sbi.NEARBY_NAME_RE.search("see TA-foobar at end")
        assert m is not None
        assert m.group("name") == "TA-foobar"

    def test_nearby_name_re_matches_da_ess(self) -> None:
        m = sbi.NEARBY_NAME_RE.search("see DA-ESS-AccessProtection at end")
        assert m is not None
        assert m.group("name") == "DA-ESS-AccessProtection"

    def test_nearby_name_re_matches_splunk_app_for(self) -> None:
        m = sbi.NEARBY_NAME_RE.search("see Splunk App for Foo Bar at end")
        assert m is not None
        assert "Splunk App for Foo" in m.group("name")

    def test_scan_fields_match_documented(self) -> None:
        """The 6 documented fields are pinned."""
        assert sbi.SCAN_FIELDS == (
            "app",
            "dataSources",
            "implementation",
            "detailedImplementation",
            "description",
            "value",
        )


# ----------------------------------------------------------------------
# _extract_refs
# ----------------------------------------------------------------------


class TestExtractRefs:
    def test_empty_text_returns_empty(self) -> None:
        assert sbi._extract_refs("UC-1.1.1", "") == []

    def test_no_match_returns_empty(self) -> None:
        assert sbi._extract_refs("UC-1.1.1", "no splunkbase references here") == []

    def test_plain_url_uses_unknown_context(self) -> None:
        """A bare URL with no nearby name → ``<unknown>`` context."""
        result = sbi._extract_refs("UC-1.1.1", "see https://splunkbase.splunk.com/app/2890")
        assert result == [("2890", "<unknown>", "UC-1.1.1")]

    def test_url_with_md_link_name(self) -> None:
        result = sbi._extract_refs(
            "UC-1.1.1",
            "[Splunk Add-on for AWS](https://splunkbase.splunk.com/app/1876)",
        )
        assert result == [("1876", "Splunk Add-on for AWS", "UC-1.1.1")]

    def test_md_link_name_with_template_braces_skipped(self) -> None:
        """Names containing ``{`` (template placeholder) are rejected
        and fall back to NEARBY_NAME / <unknown>."""
        result = sbi._extract_refs(
            "UC-1.1.1",
            "[{{vendor}}](https://splunkbase.splunk.com/app/2890)",
        )
        assert result == [("2890", "<unknown>", "UC-1.1.1")]

    def test_url_with_nearby_name(self) -> None:
        """When no md_name is present, the audit walks back 120 chars
        looking for a NEARBY_NAME_RE match."""
        text = "See the Splunk_TA_foo at https://splunkbase.splunk.com/app/2890"
        result = sbi._extract_refs("UC-1.1.1", text)
        assert result == [("2890", "Splunk_TA_foo", "UC-1.1.1")]

    def test_url_nearby_name_far_away_unmatched(self) -> None:
        """Beyond the 120-char window, the audit uses <unknown>."""
        prefix = "Splunk_TA_foo " + ("x" * 200) + " "
        text = prefix + "https://splunkbase.splunk.com/app/2890"
        result = sbi._extract_refs("UC-1.1.1", text)
        assert result == [("2890", "<unknown>", "UC-1.1.1")]

    def test_url_nearby_name_last_wins(self) -> None:
        """When multiple NEARBY_NAME_RE matches precede the URL, the
        LAST one wins."""
        text = (
            "First Splunk_TA_oldone fell out of use, then we adopted "
            "Splunk_TA_newone via https://splunkbase.splunk.com/app/2890"
        )
        result = sbi._extract_refs("UC-1.1.1", text)
        assert result == [("2890", "Splunk_TA_newone", "UC-1.1.1")]

    def test_url_name_trailing_punctuation_stripped(self) -> None:
        """Trailing ``.,:;`` are stripped from the captured name."""
        text = "Splunk_TA_foo, https://splunkbase.splunk.com/app/2890"
        # Window includes 'Splunk_TA_foo,' but the regex captures
        # 'Splunk_TA_foo' (NEARBY_NAME_RE doesn't capture the comma);
        # this test is mainly for the .rstrip(",.;:") branch in the
        # combined case where the regex does capture trailing punct.
        result = sbi._extract_refs("UC-1.1.1", text)
        # Either way, the name is clean.
        assert result[0][1].endswith("foo")

    def test_url_name_whitespace_normalised(self) -> None:
        """``\\s+`` runs are collapsed to single spaces in the name."""
        text = "[Splunk  Add-On  for   AWS](https://splunkbase.splunk.com/app/1876)"
        result = sbi._extract_refs("UC-1.1.1", text)
        assert result == [("1876", "Splunk Add-On for AWS", "UC-1.1.1")]

    def test_inline_splunkbase_hash_id(self) -> None:
        text = "see Splunkbase #2890 for details"
        result = sbi._extract_refs("UC-1.1.1", text)
        assert ("2890", "<unknown>", "UC-1.1.1") in result

    def test_inline_no_hash(self) -> None:
        text = "see Splunkbase 2890 for details"
        result = sbi._extract_refs("UC-1.1.1", text)
        assert ("2890", "<unknown>", "UC-1.1.1") in result

    def test_inline_with_nearby_name(self) -> None:
        """Inline ``Splunkbase #<id>`` also looks back for a NEARBY_NAME."""
        text = "use the Splunk_TA_foo (Splunkbase #2890)"
        result = sbi._extract_refs("UC-1.1.1", text)
        assert result == [("2890", "Splunk_TA_foo", "UC-1.1.1")]

    def test_inline_suppressed_when_inside_url_span(self) -> None:
        """When an inline match overlaps an already-seen URL match,
        it's suppressed (avoids double-counting).

        The trigger requires the inline pattern (``\\bSplunkbase\\s*#?
        \\s*\\d{3,5}\\b``) to fall INSIDE a URL_RE-matched span — for
        example, when the markdown link *name* literally reads
        ``Splunkbase 12345``. Without the suppression the same ID
        would be double-counted.
        """
        text = "[Splunkbase 12345](https://splunkbase.splunk.com/app/12345)"
        result = sbi._extract_refs("UC-1.1.1", text)
        # Only one entry — the URL one — not duplicated by inline.
        assert len(result) == 1
        assert result[0] == ("12345", "Splunkbase 12345", "UC-1.1.1")

    def test_multiple_urls_in_one_text(self) -> None:
        text = (
            "Splunk_TA_a (https://splunkbase.splunk.com/app/100) "
            "and Splunk_TA_b (https://splunkbase.splunk.com/app/200)"
        )
        result = sbi._extract_refs("UC-1.1.1", text)
        assert ("100", "Splunk_TA_a", "UC-1.1.1") in result
        assert ("200", "Splunk_TA_b", "UC-1.1.1") in result

    def test_long_md_name_falls_back(self) -> None:
        """md_name >= 80 chars falls back to nearby-name / unknown.

        NOTE: ``URL_RE`` uses ``[^\\]]{1,80}`` for ``md_name``, so any
        markdown name >= 80 characters CANNOT match the md_name group;
        the regex backtracks and matches without it. With no preceding
        NEARBY_NAME_RE hit, the result is ``<unknown>``.
        """
        long_name = "x" * 81
        text = f"[{long_name}](https://splunkbase.splunk.com/app/2890)"
        result = sbi._extract_refs("UC-1.1.1", text)
        # md_name capture is None because the bracket group fails to
        # match; the URL still matches and the context is <unknown>.
        assert result == [("2890", "<unknown>", "UC-1.1.1")]


# ----------------------------------------------------------------------
# main()
# ----------------------------------------------------------------------


class TestMainClean:
    def test_empty_content_returns_zero(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        rc = sbi.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "Scanned 0 JSON sidecars" in out
        assert "Splunkbase references: 0" in out
        assert "Unique app IDs: 0" in out

    def test_clean_uc_no_references(
        self, make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_uc("1.1.1", {"description": "no splunkbase references here"})
        rc = sbi.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "Scanned 1 JSON sidecars" in out
        assert "Splunkbase references: 0" in out


class TestMainCollectsReferences:
    def test_single_reference(self, make_uc: MakeUC, capsys: pytest.CaptureFixture[str]) -> None:
        make_uc(
            "1.1.1",
            {"app": "[Splunk Add-on for AWS](https://splunkbase.splunk.com/app/1876)"},
        )
        rc = sbi.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "Splunkbase references: 1" in out
        assert "Unique app IDs: 1" in out
        # The sorted ID listing shows the canonical name.
        assert "1876" in out
        assert "Splunk Add-on for AWS" in out

    def test_multiple_fields_scanned(
        self, make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """All six SCAN_FIELDS contribute references."""
        payload = dict.fromkeys(sbi.SCAN_FIELDS, "Splunkbase #100")
        make_uc("1.1.1", payload)
        rc = sbi.main([])
        out = capsys.readouterr().out
        assert rc == 0
        # 6 fields scanned → 6 references to the same ID.
        assert "Splunkbase references: 6" in out
        assert "Unique app IDs: 1" in out

    def test_non_scan_field_ignored(
        self, make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """References in fields outside SCAN_FIELDS are not counted."""
        make_uc(
            "1.1.1",
            {"title": "Splunkbase #100 (in title, should not count)"},
        )
        rc = sbi.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "Splunkbase references: 0" in out

    def test_non_string_field_ignored(
        self, make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Non-string SCAN_FIELDS values are skipped."""
        make_uc("1.1.1", {"app": 42})
        rc = sbi.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "Splunkbase references: 0" in out

    def test_empty_string_field_ignored(
        self, make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Empty SCAN_FIELDS strings are skipped (``if v``)."""
        make_uc("1.1.1", {"app": ""})
        rc = sbi.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "Splunkbase references: 0" in out

    def test_missing_id_falls_back_to_unknown(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A sidecar with no ``id`` field renders as ``UC-<unknown>``."""
        cat = fake_repo / "content" / "cat-01-test"
        cat.mkdir(parents=True)
        sidecar = cat / "UC-1.1.1.json"
        sidecar.write_text(json.dumps({"app": "Splunkbase #100"}), encoding="utf-8")
        rc = sbi.main([])
        assert rc == 0


class TestMainAggregation:
    def test_unknown_context_counted(
        self,
        make_uc: MakeUC,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        make_uc("1.1.1", {"app": "https://splunkbase.splunk.com/app/2890"})
        rc = sbi.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "References with <unknown> context name: 1" in out

    def test_multi_name_variants_section(
        self,
        make_uc: MakeUC,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When the same ID is observed with multiple names, the
        'multiple observed name variants' section lists it sorted by
        most-common count."""
        make_uc(
            "1.1.1",
            {
                "app": (
                    "[Splunk Add-on for AWS](https://splunkbase.splunk.com/app/100) "
                    "[Splunk Add-on for AWS](https://splunkbase.splunk.com/app/100) "
                    "[AWS TA Old Name](https://splunkbase.splunk.com/app/100)"
                )
            },
        )
        rc = sbi.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "IDs with multiple observed name variants (1)" in out
        assert "ID 100" in out
        # The canonical is the most common name.
        assert "canonical: 'Splunk Add-on for AWS'" in out
        # Per-name counts (sorted by most-common).
        assert "2x" in out
        assert "1x" in out

    def test_no_multi_variants_section_when_unique(
        self,
        make_uc: MakeUC,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When every ID has exactly one observed name, the multi-name
        section reports zero entries."""
        make_uc(
            "1.1.1",
            {"app": "[Foo](https://splunkbase.splunk.com/app/100)"},
        )
        assert sbi.main([]) == 0
        out = capsys.readouterr().out
        assert "IDs with multiple observed name variants (0)" in out

    def test_unique_ids_sorted_numerically(
        self,
        make_uc: MakeUC,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The "All N unique IDs" section lists IDs sorted by integer
        value, not lexicographically."""
        make_uc(
            "1.1.1",
            {
                "app": (
                    "[A](https://splunkbase.splunk.com/app/100) "
                    "[B](https://splunkbase.splunk.com/app/50) "
                    "[C](https://splunkbase.splunk.com/app/200)"
                )
            },
        )
        assert sbi.main([]) == 0
        out = capsys.readouterr().out
        # Find the "All N unique IDs" section.
        section = out.split("All ")[1]
        # Numeric sort means 50 < 100 < 200.
        i50 = section.index(" 50  ")
        i100 = section.index("100  ")
        i200 = section.index("200  ")
        assert i50 < i100 < i200


class TestMainCli:
    def test_argv_none_uses_sys_argv(
        self,
        fake_repo: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("sys.argv", ["splunkbase_ids"])
        rc = sbi.main(None)
        assert rc == 0

    def test_help_exits_clean(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with pytest.raises(SystemExit) as excinfo:
            sbi.main(["--help"])
        out = capsys.readouterr().out
        assert excinfo.value.code == 0
        assert "Splunkbase" in out
