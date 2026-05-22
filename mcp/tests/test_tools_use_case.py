"""Tests for ``splunk_uc_mcp.tools.use_case`` (get_use_case, list_categories)."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
import respx
from splunk_uc_mcp.catalog import Catalog, CatalogNotFoundError
from splunk_uc_mcp.tools.use_case import (
    GET_USE_CASE_MARKDOWN_OUTPUT_SCHEMA,
    GET_USE_CASE_MARKDOWN_SCHEMA,
    GET_USE_CASE_OUTPUT_SCHEMA,
    GET_USE_CASE_SCHEMA,
    LIST_CATEGORIES_OUTPUT_SCHEMA,
    LIST_CATEGORIES_SCHEMA,
    _coerce_splunkbase_apps,
    get_use_case,
    get_use_case_markdown,
    list_categories,
)


@pytest.fixture
def isolated_synthetic_catalog(
    synthetic_catalog: Catalog,
) -> Iterator[Catalog]:
    """Synthetic catalogue with remote fetches blocked (404 on every path).

    Without this isolation, ``Catalog.load_json`` falls through to the
    live GitHub Pages mirror when a requested file is missing from the
    local tree — which silently leaks real UCs into tests that expected
    the synthetic shape. The respx mock returns 404 for every request
    under the catalogue's ``base_url``, so a local miss surfaces as
    :class:`CatalogNotFoundError` (the contract ``get_use_case`` depends
    on when it falls back to ``uc-thin.json``).
    """

    respx_mock = respx.mock(assert_all_called=False)
    respx_mock.get(url__startswith=synthetic_catalog.base_url).respond(404)
    respx_mock.start()
    try:
        yield synthetic_catalog
    finally:
        respx_mock.stop()
        respx_mock.reset()


class TestGetUseCaseSchemas:
    def test_input_schema_shape(self) -> None:
        s = GET_USE_CASE_SCHEMA
        assert s["properties"]["uc_id"]["type"] == "string"
        assert "uc_id" in s["required"]
        assert s["additionalProperties"] is False

    def test_output_schema_shape(self) -> None:
        s = GET_USE_CASE_OUTPUT_SCHEMA
        for key in ("id", "title", "equipment", "mitreAttack", "compliance"):
            assert key in s["properties"]

    def test_output_schema_advertises_implementation_ordering(self) -> None:
        """``wave`` + ``prerequisiteUseCases`` must be declared so agents
        know they can rely on the fields (even if empty) for planning."""

        props = GET_USE_CASE_OUTPUT_SCHEMA["properties"]
        assert props["wave"]["type"] == "string"
        assert (
            props["prerequisiteUseCases"]["items"]["pattern"].startswith("^UC-")
        )

    def test_output_schema_advertises_splunkbase_apps(self) -> None:
        """v1.7.0 catalogue: every UC carries (possibly empty)
        ``splunkbaseApps`` so agents can render install guidance.

        The role enum must match ``schemas/uc.schema.json``; if the
        enum drifts, hand-rolled MCP consumers will silently accept
        invalid roles. Pin both the enum order and the required keys.
        """

        props = GET_USE_CASE_OUTPUT_SCHEMA["properties"]
        assert "splunkbaseApps" in props
        sb = props["splunkbaseApps"]
        assert sb["type"] == "array"
        item = sb["items"]
        assert item["required"] == ["id", "name", "role"]
        assert item["properties"]["id"]["type"] == "integer"
        assert item["properties"]["role"]["enum"] == [
            "primary",
            "data-source",
            "premium",
            "optional",
        ]


class TestCoerceSplunkbaseApps:
    def test_handles_missing_or_wrong_type(self) -> None:
        assert _coerce_splunkbase_apps(None) == []
        assert _coerce_splunkbase_apps("nope") == []
        assert _coerce_splunkbase_apps({}) == []

    def test_promotes_compact_to_full_shape(self) -> None:
        out = _coerce_splunkbase_apps([
            {
                "id": 5631,
                "role": "data-source",
                "name": "Splunk_TA_cisco_meraki",
                "minVersion": "2.7.1",
            },
            {
                "id": 263,
                "role": "premium",
                "name": "ES",
                "setupSkill": "splunk-es-setup",
                "requiresSmeReview": True,
            },
        ])
        assert out[0]["id"] == 5631
        assert out[0]["minVersion"] == "2.7.1"
        assert out[1]["setupSkill"] == "splunk-es-setup"
        assert out[1]["requiresSmeReview"] is True

    def test_drops_entries_missing_required_keys(self) -> None:
        out = _coerce_splunkbase_apps([
            {"id": None, "role": "primary"},
            {"id": 5631, "role": "data-source"},
            {"id": 5631, "name": "x"},
            {"role": "data-source", "name": "y"},
            "not-a-dict",
        ])
        assert out == []

    def test_input_schema_pattern_is_valid(self) -> None:
        import re

        pattern = GET_USE_CASE_SCHEMA["properties"]["uc_id"]["pattern"]
        compiled = re.compile(pattern)
        assert compiled.fullmatch("22.1.1") is not None
        assert compiled.fullmatch("1.1.1") is not None
        assert compiled.fullmatch("22.01.1") is None  # no leading zero
        assert compiled.fullmatch("22.1") is None
        assert compiled.fullmatch("22.1.1.1") is None


class TestGetUseCaseLive:
    def test_fetch_compliance_uc(self, live_catalog: Catalog) -> None:
        """cat-22 UCs return the compliance sidecar with full detail."""

        r = get_use_case(catalog=live_catalog, uc_id="22.1.1")
        assert r["id"] == "22.1.1"
        assert r["title"]
        assert isinstance(r.get("compliance"), list)
        assert len(r["compliance"]) >= 1
        entry = r["compliance"][0]
        assert "regulation" in entry
        assert "clause" in entry

    def test_fetch_non_compliance_uc(self, live_catalog: Catalog) -> None:
        """Non-cat-22 UCs fall back to uc-thin; get empty compliance[]."""

        r = get_use_case(catalog=live_catalog, uc_id="1.1.1")
        assert r["id"] == "1.1.1"
        assert r["title"]
        assert r.get("compliance") == []

    def test_unknown_uc_raises_not_found(self, live_catalog: Catalog) -> None:
        with pytest.raises(CatalogNotFoundError):
            get_use_case(catalog=live_catalog, uc_id="999.999.999")

    def test_compliance_sidecar_strips_apiVersion(
        self, live_catalog: Catalog
    ) -> None:
        """Sidecars carry apiVersion/_meta; those must not leak to agents."""

        r = get_use_case(catalog=live_catalog, uc_id="22.1.1")
        assert "apiVersion" not in r
        assert "_meta" not in r
        for k in r:
            assert not k.startswith("$")


class TestGetUseCaseValidation:
    @pytest.mark.parametrize(
        "bad_id",
        [
            "22.1",
            "abc",
            "22.1.1.1",
            "../etc/passwd",
            "22.01.1",
            "",
            "22.1.1 ",
            "22.1.a",
            "-1.1.1",
        ],
    )
    def test_rejects_invalid_uc_id(
        self, live_catalog: Catalog, bad_id: str
    ) -> None:
        with pytest.raises(ValueError, match="uc_id"):
            get_use_case(catalog=live_catalog, uc_id=bad_id)

    def test_accepts_zero_segments(self, live_catalog: Catalog) -> None:
        """``0.0.0`` is a valid shape even if the UC itself doesn't exist."""

        with pytest.raises(CatalogNotFoundError):
            get_use_case(catalog=live_catalog, uc_id="0.0.0")


class TestGetUseCaseSynthetic:
    def test_compliance_sidecar_preferred(
        self, synthetic_catalog: Catalog
    ) -> None:
        r = get_use_case(catalog=synthetic_catalog, uc_id="22.1.1")
        assert r["id"] == "22.1.1"
        assert r["compliance"][0]["regulation"] == "GDPR"
        # Sidecar-only field (SPL) must flow through.
        assert "spl" in r
        # Bookkeeping must not leak.
        assert "apiVersion" not in r

    def test_thin_fallback(
        self, isolated_synthetic_catalog: Catalog
    ) -> None:
        r = get_use_case(catalog=isolated_synthetic_catalog, uc_id="1.1.1")
        assert r["id"] == "1.1.1"
        assert r["title"] == "Test UC One"
        assert r["compliance"] == []

    def test_unknown_uc_raises(
        self, isolated_synthetic_catalog: Catalog
    ) -> None:
        with pytest.raises(CatalogNotFoundError):
            get_use_case(catalog=isolated_synthetic_catalog, uc_id="99.99.99")

    def test_thin_fallback_surfaces_wave_and_prereq(
        self, isolated_synthetic_catalog: Catalog
    ) -> None:
        """A crawl UC loaded via the uc-thin fallback still exposes wave
        + prereq, even when the UC has no compliance sidecar."""

        r = get_use_case(catalog=isolated_synthetic_catalog, uc_id="1.1.1")
        assert r.get("wave") == "crawl"
        assert r.get("prerequisiteUseCases") == []

    def test_compliance_sidecar_surfaces_wave_and_prereq(
        self, synthetic_catalog: Catalog
    ) -> None:
        """A walk UC loaded from the compliance sidecar carries the same
        ordering metadata plus the upstream UC edge."""

        r = get_use_case(catalog=synthetic_catalog, uc_id="22.1.1")
        assert r.get("wave") == "walk"
        assert r.get("prerequisiteUseCases") == ["UC-1.1.1"]


class TestListCategoriesSchemas:
    def test_input_schema_is_empty(self) -> None:
        s = LIST_CATEGORIES_SCHEMA
        assert s["type"] == "object"
        assert s.get("properties") in (None, {})
        assert s["additionalProperties"] is False

    def test_output_schema_shape(self) -> None:
        s = LIST_CATEGORIES_OUTPUT_SCHEMA
        assert "categories" in s["properties"]
        assert "count" in s["properties"]
        sub_schema = s["properties"]["categories"]["items"]["properties"]
        assert "id" in sub_schema
        assert "useCaseCount" in sub_schema
        assert "subcategories" in sub_schema


class TestListCategoriesLive:
    def test_categories_present(self, live_catalog: Catalog) -> None:
        r = list_categories(catalog=live_catalog)
        assert r["count"] >= 20
        ids = {c["id"] for c in r["categories"]}
        assert "22" in ids

    def test_category_structure(self, live_catalog: Catalog) -> None:
        r = list_categories(catalog=live_catalog)
        for c in r["categories"]:
            assert "id" in c
            assert "useCaseCount" in c
            assert "subcategories" in c
            assert c["useCaseCount"] >= 1
            for sub in c["subcategories"]:
                assert sub["id"].startswith(f"{c['id']}.")
                assert sub["useCaseCount"] >= 1

    def test_subcategory_counts_sum_to_category(
        self, live_catalog: Catalog
    ) -> None:
        r = list_categories(catalog=live_catalog)
        for c in r["categories"]:
            total = sum(s["useCaseCount"] for s in c["subcategories"])
            assert total == c["useCaseCount"]

    def test_categories_sorted_numerically(
        self, live_catalog: Catalog
    ) -> None:
        r = list_categories(catalog=live_catalog)
        ids = [int(c["id"]) for c in r["categories"]]
        assert ids == sorted(ids)


class TestListCategoriesSynthetic:
    def test_synthetic_tree(self, synthetic_catalog: Catalog) -> None:
        r = list_categories(catalog=synthetic_catalog)
        assert r["count"] == 2
        ids = [c["id"] for c in r["categories"]]
        assert ids == ["1", "22"]

        cat_1 = r["categories"][0]
        assert cat_1["useCaseCount"] == 1
        assert cat_1["subcategories"] == [{"id": "1.1", "useCaseCount": 1}]

        cat_22 = r["categories"][1]
        assert cat_22["useCaseCount"] == 1
        assert cat_22["subcategories"] == [{"id": "22.1", "useCaseCount": 1}]


class TestGetUseCaseMarkdownSchemas:
    def test_input_schema_shape(self) -> None:
        s = GET_USE_CASE_MARKDOWN_SCHEMA
        assert "uc_id" in s["required"]
        assert s["additionalProperties"] is False
        assert s["properties"]["uc_id"]["type"] == "string"

    def test_output_schema_shape(self) -> None:
        s = GET_USE_CASE_MARKDOWN_OUTPUT_SCHEMA
        for key in ("id", "url", "markdown"):
            assert key in s["required"]
        assert s["properties"]["markdown"]["type"] == "string"


class TestGetUseCaseMarkdownSynthetic:
    def test_compliance_uc_renders_full_doc(
        self, synthetic_catalog: Catalog
    ) -> None:
        r = get_use_case_markdown(catalog=synthetic_catalog, uc_id="22.1.1")
        assert r["id"] == "UC-22.1.1"
        assert r["url"].endswith("/uc/UC-22.1.1/uc.md")
        md = r["markdown"]
        # Title and source line frame the document.
        assert md.startswith("# UC-22.1.1 — GDPR PII access detection")
        assert "Source: [Splunk Monitoring Use Cases]" in md
        # SPL must be in a fenced code block.
        assert "```spl" in md
        assert "index=azure | stats count by user" in md
        # Quick facts table includes structured metadata.
        assert "| Field | Value |" in md
        assert "| Wave | walk |" in md
        # Compliance mapping rendered.
        assert "## Compliance mappings" in md
        assert "GDPR — Art.5" in md
        # Prerequisite UC link uses the canonical site URL.
        assert "[UC-1.1.1](https://fenre.github.io/splunk-monitoring-use-cases/uc/UC-1.1.1/)" in md

    def test_thin_uc_renders_minimal_doc(
        self, isolated_synthetic_catalog: Catalog
    ) -> None:
        r = get_use_case_markdown(
            catalog=isolated_synthetic_catalog, uc_id="1.1.1"
        )
        assert r["id"] == "UC-1.1.1"
        md = r["markdown"]
        assert md.startswith("# UC-1.1.1 — Test UC One")
        # Non-compliance UCs have no compliance section.
        assert "## Compliance mappings" not in md
        # Quick facts still render the basics.
        assert "| Wave | crawl |" in md

    def test_unknown_uc_raises(
        self, isolated_synthetic_catalog: Catalog
    ) -> None:
        with pytest.raises(CatalogNotFoundError):
            get_use_case_markdown(
                catalog=isolated_synthetic_catalog, uc_id="99.99.99"
            )

    def test_invalid_uc_id_rejected(
        self, synthetic_catalog: Catalog
    ) -> None:
        with pytest.raises(ValueError, match="uc_id"):
            get_use_case_markdown(catalog=synthetic_catalog, uc_id="../etc")


class TestGetUseCaseMarkdownAllSections:
    """Drives ``get_use_case_markdown`` against a single UC dict that
    has every optional section populated, so every render branch in
    the renderer (last-modified header, plain-language, knownFalse
    positives both shapes, references in four shapes, compliance with
    mode + assurance, compliance with no clause) is exercised by one
    parametrised UC dict.

    The renderer calls ``get_use_case`` internally, so we monkeypatch
    that symbol on the module to return our crafted dict instead of
    reading from disk. This keeps the test hermetic and lets us prove
    every branch fires from a single, readable fixture.
    """

    @pytest.fixture
    def rich_uc(self) -> dict[str, object]:
        return {
            "id": "22.1.1",
            "title": "Rich UC",
            "reviewed": "2026-01-15",  # last-modified header
            "grandmaExplanation": "We watch the data.",  # ge block
            "criticality": "high",
            "difficulty": "medium",
            "wave": "walk",
            "splunkPillar": "compliance",
            "monitoringType": ["detection"],
            "app": ["splunk_ta_linux"],
            "dataSources": ["wineventlog"],
            "cimModels": ["Authentication"],
            "equipment": ["linux"],
            "equipmentModels": ["azure:vm"],
            "mitreAttack": ["T1078"],
            "prerequisiteUseCases": [
                "UC-1.1.1",
                "   ",  # whitespace-only -> hits the "continue" branch
            ],
            "value": "Detect anomalous access patterns",
            "spl": "index=foo | stats count",
            "detailedImplementation": "Install the TA, enable the search.",
            "visualization": "single-value panel",
            "knownFalsePositives": [
                "Batch jobs at 2 AM",
                "   ",  # whitespace-only -> skipped
                "Quarterly audits",
            ],
            "references": [
                {"title": "Splunk Docs", "url": "https://docs.splunk.com"},  # both
                {"url": "https://nourl-title.example/spec"},  # url only
                {"title": "Title only, no URL"},  # title only
                "https://plain-string.example",  # bare string
                "   ",  # whitespace -> skipped
            ],
            "compliance": [
                {
                    "regulation": "GDPR",
                    "clause": "Art.5",
                    "mode": "detect",
                    "assurance": "primary",
                },
                {"regulation": "PCI", "clause": ""},  # reg-only -> 483-484
                "not a dict, skipped",  # non-dict -> 470 (continue)
            ],
        }

    def test_renders_all_optional_sections(
        self,
        monkeypatch: pytest.MonkeyPatch,
        synthetic_catalog: Catalog,
        rich_uc: dict[str, object],
    ) -> None:
        from splunk_uc_mcp.tools import use_case as use_case_mod

        monkeypatch.setattr(
            use_case_mod,
            "get_use_case",
            lambda *, catalog, uc_id: dict(rich_uc),
        )

        result = use_case_mod.get_use_case_markdown(
            catalog=synthetic_catalog, uc_id="22.1.1"
        )
        md = result["markdown"]
        # Header carries the canonical id and a last-modified line.
        assert md.startswith("# UC-22.1.1 — Rich UC")
        assert "> Last-modified: 2026-01-15" in md
        # Plain-language block is rendered as a blockquote.
        assert "## In plain language" in md
        assert "> We watch the data." in md
        # Quick-facts table has the standard rows.
        assert "| Wave | walk |" in md
        assert "| Criticality | high |" in md
        # Prereq list keeps the UC-1.1.1 link and drops the whitespace.
        assert "[UC-1.1.1](" in md
        # Value, SPL fence, implementation, visualization all present.
        assert "## Value" in md
        assert "```spl" in md
        assert "## Implementation" in md
        assert "Install the TA" in md
        assert "## Visualization" in md
        # Known false positives renders both list items, skipping whitespace.
        assert "## Known false positives" in md
        assert "- Batch jobs at 2 AM" in md
        assert "- Quarterly audits" in md
        # References render in all four shapes.
        assert "## References" in md
        assert "[Splunk Docs](https://docs.splunk.com)" in md
        assert "- https://nourl-title.example/spec" in md
        assert "- Title only, no URL" in md
        assert "- https://plain-string.example" in md
        # Compliance section: GDPR with mode + assurance tail, PCI w/o clause,
        # the bare string is silently skipped (non-dict branch).
        assert "## Compliance mappings" in md
        assert "GDPR — Art.5 (mode: detect; assurance: primary)" in md
        assert "- PCI" in md
        # The non-dict entry must NOT have created an output line.
        assert "not a dict, skipped" not in md

    def test_string_known_false_positive_renders_inline(
        self,
        monkeypatch: pytest.MonkeyPatch,
        synthetic_catalog: Catalog,
    ) -> None:
        """The ``knownFalsePositives`` field may be a bare string,
        in which case the renderer emits it as a single paragraph
        instead of a bullet list (server.py renderer lines 440-441
        — the ``else`` branch of ``isinstance(kfp, (list, tuple))``)."""

        from splunk_uc_mcp.tools import use_case as use_case_mod

        monkeypatch.setattr(
            use_case_mod,
            "get_use_case",
            lambda *, catalog, uc_id: {
                "id": "22.1.1",
                "title": "Bare-string KFP",
                "spl": "index=foo | head 1",
                "knownFalsePositives": "Just a single paragraph here.",
            },
        )

        result = use_case_mod.get_use_case_markdown(
            catalog=synthetic_catalog, uc_id="22.1.1"
        )
        md = result["markdown"]
        assert "## Known false positives" in md
        # The bare string is dropped under the heading; the list bullet
        # ``-`` MUST be absent because we hit the non-list branch.
        assert "Just a single paragraph here." in md
        # The list path would have prefixed each line with `- ` — assert
        # the renderer DID NOT use bullets for the string body.
        kfp_section = md.split("## Known false positives", 1)[1]
        first_para = kfp_section.strip().split("\n\n", 1)[0]
        assert not first_para.lstrip().startswith("- ")

    def test_empty_fact_value_after_filter_is_dropped(
        self,
        monkeypatch: pytest.MonkeyPatch,
        synthetic_catalog: Catalog,
    ) -> None:
        """Hit the ``_add_fact`` early-return branch on use_case.py
        line 363: when a fact's stringified value collapses to the
        empty string after filtering, the renderer must drop it
        from the Quick facts table rather than emit a blank row.

        Reproducing this requires a list whose entries are all
        ``None`` or the empty string — those entries pass the
        first ``raw == []`` guard (the list itself is non-empty),
        then ``", ".join(... if v not in (None, ""))`` filters
        them all out, leaving ``value == ""`` which trips line 363.

        Equivalently a non-list raw of ``"   "`` would also hit
        line 363 via the ``str(raw).strip()`` path. We use both in
        the same test (one per fact label) so a future refactor
        that fixes just one path can't silently regress the other.
        """

        from splunk_uc_mcp.tools import use_case as use_case_mod

        monkeypatch.setattr(
            use_case_mod,
            "get_use_case",
            lambda *, catalog, uc_id: {
                "id": "22.1.1",
                "title": "Empty-fact UC",
                "spl": "index=foo | head 1",
                # List of all-empty entries -> hits the list filter
                # path; the only element gets dropped by the join
                # filter and value collapses to "".
                "monitoringType": [None, ""],
                # Bare whitespace string -> hits the str(raw).strip()
                # path; value collapses to "" after strip.
                "wave": "   ",
            },
        )

        result = use_case_mod.get_use_case_markdown(
            catalog=synthetic_catalog, uc_id="22.1.1"
        )
        md = result["markdown"]
        # Neither row should appear in the Quick facts table.
        assert "| Monitoring type |" not in md
        assert "| Wave |" not in md

    def test_dict_reference_with_no_title_or_url_is_skipped(
        self,
        monkeypatch: pytest.MonkeyPatch,
        synthetic_catalog: Catalog,
    ) -> None:
        """Pin the 456->448 partial branch: when a reference dict
        carries neither ``title`` nor ``url``, the renderer must fall
        through every emission arm and continue to the next entry
        without appending a malformed bullet (e.g. ``- `` with no
        text). Without this test the False arm of ``elif t:`` on
        line 456 was uncovered — only the True arms of the if/elif
        cascade were exercised by the rich-UC fixture.
        """
        from splunk_uc_mcp.tools import use_case as use_case_mod

        monkeypatch.setattr(
            use_case_mod,
            "get_use_case",
            lambda *, catalog, uc_id: {
                "id": "22.1.1",
                "title": "Empty-refs UC",
                "spl": "index=foo | head 1",
                "references": [
                    # Both fields are missing — the helper must skip.
                    {},
                    # Both fields are empty strings — same skip path.
                    {"title": "", "url": ""},
                    # Sanity bullet so the section still renders and we
                    # can assert nothing leaked from the empty entries.
                    {"title": "Anchor", "url": "https://example.invalid/"},
                ],
            },
        )

        result = use_case_mod.get_use_case_markdown(
            catalog=synthetic_catalog, uc_id="22.1.1"
        )
        md = result["markdown"]
        assert "## References" in md
        # The valid entry renders as a markdown link.
        assert "[Anchor](https://example.invalid/)" in md
        # The two empty entries must NOT have produced any bullet —
        # specifically there must be no bare ``- `` line with no
        # following text inside the References section.
        refs_section = md.split("## References", 1)[1].split("\n\n", 1)[0]
        for line in refs_section.splitlines():
            assert line.strip() != "-", (
                "empty reference dict leaked an empty bullet"
            )

    def test_compliance_entry_with_no_regulation_is_skipped(
        self,
        monkeypatch: pytest.MonkeyPatch,
        synthetic_catalog: Catalog,
    ) -> None:
        """Pin the 483->468 partial branch: when a compliance entry
        carries no ``regulation`` field, neither ``if reg and clause``
        nor ``elif reg`` fires. The loop continues to the next entry
        without appending anything. Without this test the False arm
        of ``elif reg`` on line 483 was uncovered — the rich-UC
        fixture covers the reg+clause and reg-only paths but not the
        no-reg path.
        """
        from splunk_uc_mcp.tools import use_case as use_case_mod

        monkeypatch.setattr(
            use_case_mod,
            "get_use_case",
            lambda *, catalog, uc_id: {
                "id": "22.1.1",
                "title": "No-regulation compliance UC",
                "spl": "index=foo | head 1",
                "compliance": [
                    # No regulation field at all — must be silently dropped.
                    {"clause": "Art.5", "mode": "detect"},
                    # Empty regulation string — same skip path.
                    {"regulation": "", "clause": "Art.7"},
                    # Sanity entry so the section still renders.
                    {"regulation": "GDPR", "clause": "Art.32"},
                ],
            },
        )

        result = use_case_mod.get_use_case_markdown(
            catalog=synthetic_catalog, uc_id="22.1.1"
        )
        md = result["markdown"]
        assert "## Compliance mappings" in md
        assert "GDPR — Art.32" in md
        # The two reg-less entries MUST NOT have leaked their clause
        # text into the rendered mappings (which would be the case if
        # the helper accidentally rendered the clause alone).
        compl_section = md.split("## Compliance mappings", 1)[1].split(
            "\n\n", 1
        )[0]
        assert "Art.5" not in compl_section
        assert "Art.7" not in compl_section


class TestListCategoriesMalformedIds:
    """Pin the line-523 guard in ``list_categories``: UC IDs that
    don't have at least three dotted parts must be silently dropped
    from the category tree rather than crashing on the index unpack."""

    def test_skips_uc_ids_with_fewer_than_three_parts(
        self,
        monkeypatch: pytest.MonkeyPatch,
        synthetic_catalog: Catalog,
    ) -> None:
        from splunk_uc_mcp.tools import use_case as use_case_mod

        def _load_json(*segments: str) -> dict[str, object]:
            assert segments == ("recommender", "uc-thin.json")
            return {
                "useCases": [
                    {"id": "22.1.1", "title": "Valid"},
                    # Missing dotted parts — must be skipped, not crash.
                    {"id": "bogus"},
                    {"id": "22"},
                    {"id": "22.1"},
                    {"id": ""},
                ]
            }

        monkeypatch.setattr(
            synthetic_catalog, "load_json", _load_json
        )
        result = use_case_mod.list_categories(catalog=synthetic_catalog)
        # Only the well-formed UC produces a category entry.
        category_ids = [c["id"] for c in result["categories"]]
        assert category_ids == ["22"]
        # And exactly one UC was counted in that category's subcategory.
        cat22 = next(c for c in result["categories"] if c["id"] == "22")
        assert cat22["useCaseCount"] == 1
        # Subcategory tree mirrors the same count for "22.1".
        assert cat22["subcategories"] == [
            {"id": "22.1", "useCaseCount": 1},
        ]
