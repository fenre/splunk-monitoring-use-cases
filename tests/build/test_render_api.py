"""Tests for tools/build/render_api.py — API JSON artefacts."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TOOLS_DIR = str(REPO_ROOT / "tools")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from build import parse_content  # noqa: E402
from build import render_api  # noqa: E402


def _minimal_catalog(project_root: Path) -> parse_content.Catalog:
    return parse_content.Catalog(
        project_root=project_root,
        categories=[
            {
                "i": 3,
                "n": "Network & Flow  !",
                "s": [
                    {
                        "i": "3.2",
                        "n": "Kubernetes",
                        # numeric sort: 3.2.10 after 3.2.5
                        "u": [
                            {
                                "i": "3.2.10",
                                "n": "Later UC",
                                "md": "huge markdown",
                                "q": "index=* | noop",
                                "prio": 2,
                            },
                            {
                                "i": "3.2.5",
                                "n": "Earlier UC",
                                "sapp": [
                                    {
                                        "id": "app1",
                                        "name": "App",
                                        "url": "https://x",
                                        "predecessor": [{"id": "old", "name": "Old", "desc": "x"}],
                                    }
                                ],
                            },
                        ],
                    }
                ],
            }
        ],
        cat_meta={"3": {"icon": "net", "desc": "meta desc"}},
        cat_groups={"g": [3]},
        equipment=[{"k": "v"}],
        regulations={},
        recently_added=["3.2.10"],
        facets={"foo": ["bar"]},
    )


class TestPureHelpers:
    def test_slug(self):
        assert render_api._slug("Hello World") == "hello-world"
        assert render_api._slug("!!!") == "category"

    def test_sort_key_numeric_segments(self):
        assert render_api._sort_key("3.2.10") > render_api._sort_key("3.2.5")

    def test_ts_reproducible(self):
        assert render_api._ts(True) == "1970-01-01T00:00:00Z"

    def test_normalise_cat_groups(self):
        assert render_api._normalise_cat_groups(None) == {}
        assert render_api._normalise_cat_groups({"a": [1, "2", "x"]}) == {"a": [1, 2]}

    def test_normalise_cat_groups_skips_non_list_values(self):
        """Dict values that aren't lists/tuples are silently dropped from
        the output ENTIRELY — the key never makes it into the result
        (covers line 254)."""
        out = render_api._normalise_cat_groups(
            {"good": [1, 2], "bad": "not a list", "also-bad": 42}
        )
        assert out == {"good": [1, 2]}

    def test_normalise_cat_meta_strips_empty(self):
        assert render_api._normalise_cat_meta({"1": {"a": 1, "b": "", "c": None}}) == {
            "1": {"a": 1}
        }

    def test_normalise_cat_meta_returns_empty_for_non_dict_input(self):
        """Non-dict inputs (None, list, str) yield ``{}`` (covers line 262)."""
        assert render_api._normalise_cat_meta(None) == {}
        assert render_api._normalise_cat_meta([("1", {"a": 1})]) == {}
        assert render_api._normalise_cat_meta("not-a-dict") == {}

    def test_normalise_cat_meta_skips_non_dict_values(self):
        """Per-key values that aren't dicts are dropped (covers line 266)."""
        out = render_api._normalise_cat_meta(
            {"1": {"icon": "x"}, "2": "not-a-dict", "3": None}
        )
        assert out == {"1": {"icon": "x"}}

    def test_sorted_unique_skips_none_entries(self):
        """``None`` items in the input are filtered before dedup (covers
        line 278)."""
        out = render_api._sorted_unique([None, "1.1.1", None, "1.1.2", "1.1.1"])
        assert out == ["1.1.1", "1.1.2"]


class TestCatalogIndexMalformedInputs:
    """``_write_catalog_index`` MUST skip categories/UCs whose identifying
    fields are missing rather than crash. These tests pin the defensive
    early-continue paths inside the main builder loop."""

    def test_category_missing_i_is_dropped(self, tmp_path: Path):
        """A category dict without the ``i`` field is silently skipped
        and never appears in the catalog index (covers line 148 in
        ``_write_category_shards`` and line 176 in
        ``_write_catalog_index``)."""
        catalog = parse_content.Catalog(
            project_root=tmp_path,
            categories=[
                {"i": 1, "n": "Real", "s": [{"i": "1.1", "u": [{"i": "1.1.1", "n": "x"}]}]},
                {"n": "Headless"},  # No `i` → must be skipped.
            ],
            cat_meta={},
            cat_groups={},
            equipment=[],
            regulations={},
            recently_added=[],
            facets={},
        )
        api_dir = tmp_path / "api"
        api_dir.mkdir()

        render_api._write_category_shards(catalog, api_dir, reproducible=True)
        # Only one cat-N.json is emitted — the headless one is dropped.
        emitted = sorted(p.name for p in api_dir.glob("cat-*.json"))
        assert emitted == ["cat-1.json"]

        render_api._write_catalog_index(catalog, api_dir, reproducible=True)
        index = json.loads((api_dir / "catalog-index.json").read_text(encoding="utf-8"))
        assert [c["i"] for c in index["categories"]] == [1]

    def test_uc_without_i_is_skipped_from_index(self, tmp_path: Path):
        """A UC dict without the ``i`` field is silently dropped during
        index emission so the lazy-bootstrap payload doesn't crash on
        a malformed entry (covers line 192)."""
        catalog = parse_content.Catalog(
            project_root=tmp_path,
            categories=[
                {
                    "i": 1,
                    "n": "Real",
                    "s": [
                        {
                            "i": "1.1",
                            "u": [
                                {"i": "1.1.1", "n": "Real UC"},
                                {"n": "Headless UC"},  # No `i` → must be skipped.
                            ],
                        }
                    ],
                }
            ],
            cat_meta={},
            cat_groups={},
            equipment=[],
            regulations={},
            recently_added=[],
            facets={},
        )
        api_dir = tmp_path / "api"
        api_dir.mkdir()
        render_api._write_catalog_index(catalog, api_dir, reproducible=True)
        index = json.loads((api_dir / "catalog-index.json").read_text(encoding="utf-8"))
        # Only the real UC made it into the lazy-bootstrap payload.
        assert [u["i"] for u in index["ucs"]] == ["1.1.1"]
        assert index["counts"]["useCases"] == 1

    def test_cat_meta_quick_field_is_propagated(self, tmp_path: Path):
        """A category whose ``cat_meta`` carries a ``quick`` value
        surfaces it on the index entry alongside ``icon`` and ``desc``
        (covers line 215)."""
        catalog = parse_content.Catalog(
            project_root=tmp_path,
            categories=[{"i": 1, "n": "X", "s": []}],
            cat_meta={"1": {"icon": "fa-foo", "desc": "Foo", "quick": "all-foo"}},
            cat_groups={},
            equipment=[],
            regulations={},
            recently_added=[],
            facets={},
        )
        api_dir = tmp_path / "api"
        api_dir.mkdir()
        render_api._write_catalog_index(catalog, api_dir, reproducible=True)
        index = json.loads((api_dir / "catalog-index.json").read_text(encoding="utf-8"))
        cat0 = index["categories"][0]
        assert cat0["quick"] == "all-foo"
        assert cat0["icon"] == "fa-foo"
        assert cat0["desc"] == "Foo"


class TestRegulationsIndex:
    """``_build_regulations_index`` and ``_count_ucs_per_regulation``
    optional-field branches and matching logic."""

    def _catalog(self, tmp_path: Path, *, regulations: dict, categories: list = None):
        return parse_content.Catalog(
            project_root=tmp_path,
            categories=categories or [],
            cat_meta={},
            cat_groups={},
            equipment=[],
            regulations=regulations,
            recently_added=[],
            facets={},
        )

    def test_optional_short_name_tier_and_jurisdiction_are_propagated(self, tmp_path: Path):
        """Regulations with ``shortName`` (line 304), integer ``tier``
        (line 307) and list ``jurisdiction`` (line 309) surface those
        fields on the index entry; missing fields are omitted."""
        catalog = self._catalog(
            tmp_path,
            regulations={
                "gdpr": {
                    "name": "General Data Protection Regulation",
                    "shortName": "GDPR",
                    "tier": 1,
                    "jurisdiction": ["EU", "UK"],
                },
                "skinny": {"name": "Skinny Reg"},
            },
        )
        entries = render_api._build_regulations_index(catalog)
        gdpr = next(e for e in entries if e["id"] == "gdpr")
        skinny = next(e for e in entries if e["id"] == "skinny")
        assert gdpr["shortName"] == "GDPR"
        assert gdpr["tier"] == 1
        assert gdpr["jurisdiction"] == ["EU", "UK"]
        assert "shortName" not in skinny
        assert "tier" not in skinny
        assert "jurisdiction" not in skinny

    def test_tier_non_int_and_jurisdiction_non_list_are_skipped(self, tmp_path: Path):
        """When ``tier`` is a string and ``jurisdiction`` is a scalar,
        both fields are omitted from the index entry (covers the false
        arms of the isinstance() guards on lines 306 and 308)."""
        catalog = self._catalog(
            tmp_path,
            regulations={
                "weird": {"name": "Weird", "tier": "one", "jurisdiction": "EU"},
            },
        )
        entries = render_api._build_regulations_index(catalog)
        assert "tier" not in entries[0]
        assert "jurisdiction" not in entries[0]

    def test_count_ucs_returns_empty_when_no_regulations(self, tmp_path: Path):
        """Catalogs without any regulation metadata short-circuit to an
        empty dict (covers line 328)."""
        catalog = self._catalog(tmp_path, regulations={}, categories=[
            {"i": 1, "n": "X", "s": [{"i": "1.1", "u": [{"i": "1.1.1", "regs": ["GDPR"]}]}]},
        ])
        assert render_api._count_ucs_per_regulation(catalog) == {}

    def test_count_ucs_matches_aliases_rewrites_and_prefix(self, tmp_path: Path):
        """Counts every UC once per matched framework: exact alias
        match, rewrite ("EU NIS2" → "NIS2"), and prefix match
        ("GDPR Art.32" → "gdpr"). Aliases list with multiple entries
        exercises line 350; the prefix-match branch covers line 381."""
        catalog = self._catalog(
            tmp_path,
            regulations={
                "gdpr": {
                    "name": "GDPR",
                    "shortName": "GDPR",
                    "aliases": ["EU GDPR", "Reg 2016/679"],
                },
                "nis2": {"name": "NIS2 Directive", "shortName": "NIS2"},
            },
            categories=[
                {
                    "i": 1, "n": "X",
                    "s": [
                        {
                            "i": "1.1",
                            "u": [
                                {"i": "1.1.1", "regs": ["GDPR"]},  # exact alias
                                {"i": "1.1.2", "regs": ["EU NIS2"]},  # rewrite
                                {"i": "1.1.3", "regs": ["GDPR Art.32"]},  # prefix
                                {"i": "1.1.4", "regs": ["Reg 2016/679"]},  # alias
                            ],
                        }
                    ],
                }
            ],
        )
        counts = render_api._count_ucs_per_regulation(catalog)
        assert counts["gdpr"] == 3  # 1.1.1, 1.1.3, 1.1.4
        assert counts["nis2"] == 1  # 1.1.2

    def test_count_ucs_skips_uc_without_id_and_with_non_list_regs(
        self, tmp_path: Path
    ):
        """``regs`` that isn't a list (line 359) and a UC without ``i``
        (line 362) are both silently skipped."""
        catalog = self._catalog(
            tmp_path,
            regulations={"gdpr": {"name": "GDPR", "shortName": "GDPR"}},
            categories=[
                {
                    "i": 1, "n": "X",
                    "s": [
                        {
                            "i": "1.1",
                            "u": [
                                {"i": "1.1.1", "regs": "GDPR"},  # non-list → skip
                                {"regs": ["GDPR"]},               # no id   → skip
                                {"i": "1.1.3", "regs": ["GDPR"]}, # valid
                            ],
                        }
                    ],
                }
            ],
        )
        counts = render_api._count_ucs_per_regulation(catalog)
        assert counts["gdpr"] == 1


class TestPathManifest:
    """``_write_path_manifest`` UC-missing-id branch and non-dict
    regulation handling."""

    def test_uc_without_id_is_skipped_from_manifest(self, tmp_path: Path):
        """A UC dict without ``i`` is skipped during manifest emission
        (covers line 425)."""
        catalog = parse_content.Catalog(
            project_root=tmp_path,
            categories=[
                {
                    "i": 1, "n": "X",
                    "s": [
                        {"i": "1.1", "u": [
                            {"i": "1.1.1", "n": "Real"},
                            {"n": "Headless"},  # no id → skipped
                        ]}
                    ],
                }
            ],
            cat_meta={}, cat_groups={}, equipment=[], regulations={},
            recently_added=[], facets={},
        )
        api_dir = tmp_path / "api"
        api_dir.mkdir()
        render_api._write_path_manifest(catalog, api_dir, reproducible=True)
        manifest = json.loads((api_dir / "manifest.json").read_text(encoding="utf-8"))
        assert [u["id"] for u in manifest["paths"]["ucs"]] == ["UC-1.1.1"]

    def test_non_dict_regulation_falls_back_to_reg_id_as_name(self, tmp_path: Path):
        """When ``catalog.regulations[id]`` is not a dict (defensive
        path), the manifest emits ``name`` as the bare reg_id rather
        than calling ``reg.get('name', ...)`` (covers the false arm of
        the isinstance() inline on line 441)."""
        catalog = parse_content.Catalog(
            project_root=tmp_path,
            categories=[],
            cat_meta={}, cat_groups={}, equipment=[],
            regulations={"gdpr": "this should be a dict"},  # malformed
            recently_added=[], facets={},
        )
        api_dir = tmp_path / "api"
        api_dir.mkdir()
        render_api._write_path_manifest(catalog, api_dir, reproducible=True)
        manifest = json.loads((api_dir / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["paths"]["regulations"][0]["name"] == "gdpr"


class TestShortlinksPlaceholder:
    """``_write_shortlinks_placeholder`` preserves an existing file
    instead of overwriting (covers line 455 — early return)."""

    def test_existing_shortlinks_is_not_overwritten(self, tmp_path: Path):
        api_dir = tmp_path / "api"
        api_dir.mkdir()
        out_path = api_dir / "shortlinks.json"
        out_path.write_text('{"sentinel": "preserve me"}', encoding="utf-8")
        render_api._write_shortlinks_placeholder(api_dir, reproducible=True)
        assert json.loads(out_path.read_text(encoding="utf-8")) == {"sentinel": "preserve me"}

    def test_missing_shortlinks_is_written_with_placeholder(self, tmp_path: Path):
        api_dir = tmp_path / "api"
        api_dir.mkdir()
        render_api._write_shortlinks_placeholder(api_dir, reproducible=True)
        payload = json.loads((api_dir / "shortlinks.json").read_text(encoding="utf-8"))
        assert payload["shortlinks"] == {}
        assert payload["version"] == "2.0.0"


class TestTimestampAndSortHelpers:
    """``_ts`` non-reproducible branch and ``_sort_key`` non-integer
    chunks."""

    def test_ts_non_reproducible_uses_wall_clock(self, monkeypatch):
        """``_ts(False)`` must call ``datetime.now`` and emit a
        ``YYYY-MM-DDTHH:MM:SSZ`` string (covers lines 489-490)."""
        out = render_api._ts(False)
        # Format check — exact wall-clock value is non-deterministic.
        import re
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", out), out

    def test_sort_key_handles_non_integer_chunks(self):
        """Subcategory or UC ids with non-numeric chunks (e.g.
        ``"1.1.alpha"``) fall through to the string-tagged tuple branch
        (covers lines 500-501)."""
        key_numeric = render_api._sort_key("1.10.2")
        key_alpha = render_api._sort_key("1.10.alpha")
        # Numeric chunks tagged with (0, int); alpha chunks with (1, str).
        assert key_numeric == ((0, 1), (0, 10), (0, 2))
        assert key_alpha == ((0, 1), (0, 10), (1, "alpha"))
        # Sort order: numeric beats alphabetic at same position.
        assert key_numeric < key_alpha

    def test_sorted_unique(self):
        assert render_api._sorted_unique(["3.2.1", "3.2.1", "3.2.10"]) == ["3.2.1", "3.2.10"]

    def test_trim_sapp(self):
        slim = render_api._trim_sapp(
            [{"id": "x", "name": "N", "url": "u", "predecessor": [{"id": "p", "desc": "d"}]}]
        )
        assert slim == [{"id": "x", "name": "N", "predecessor": [{"id": "p"}]}]

    def test_trim_sapp_returns_non_list_unchanged(self):
        """``_trim_sapp`` is a no-op for non-list inputs (covers line 76)."""
        assert render_api._trim_sapp(None) is None
        assert render_api._trim_sapp("not-a-list") == "not-a-list"
        assert render_api._trim_sapp({"id": "x"}) == {"id": "x"}

    def test_trim_sapp_skips_non_dict_entries(self):
        """List entries that aren't dicts are silently filtered out
        (covers line 80 + the false arm of ``isinstance`` at 88)."""
        result = render_api._trim_sapp(
            [
                {"id": "good", "name": "Real App"},
                "garbage-string",
                None,
                42,
                {
                    "id": "with-pred",
                    "name": "Has Pred",
                    "predecessor": [
                        {"id": "good-pred", "name": "Old"},
                        # Non-dict predecessor entries get dropped.
                        "garbage",
                        None,
                    ],
                },
            ]
        )
        assert result == [
            {"id": "good", "name": "Real App"},
            {
                "id": "with-pred",
                "name": "Has Pred",
                "predecessor": [{"id": "good-pred", "name": "Old"}],
            },
        ]

    def test_trim_sapp_leaves_scalar_predecessor_alone(self):
        """A non-list ``predecessor`` value is preserved as-is (covers
        the false arm of ``isinstance(pred, list)`` at line 83)."""
        result = render_api._trim_sapp(
            [{"id": "x", "name": "X", "predecessor": "scalar-not-list"}]
        )
        assert result == [
            {"id": "x", "name": "X", "predecessor": "scalar-not-list"}
        ]

    def test_stub_uc_skips_none_and_empty_collections(self):
        """``_stub_uc`` skips fields whose value is ``None``, an empty
        ``[]``, or an empty ``{}`` so the catalog index stays compact
        (covers lines 102 and 104)."""
        uc = {
            "i": "1.1.1",
            "n": "Title",
            "nilfield": None,
            "emptylist": [],
            "emptydict": {},
            "kept": "yes",
        }
        stub = render_api._stub_uc(uc, 1, "1.1")
        # The nil/empty values must NOT appear; the real one does.
        assert "nilfield" not in stub
        assert "emptylist" not in stub
        assert "emptydict" not in stub
        assert stub["kept"] == "yes"

    def test_stub_uc_drops_sapp_when_trim_returns_empty(self):
        """If ``_trim_sapp`` reduces ``sapp`` to an empty list (no dict
        entries survive) the stub omits the field entirely (covers the
        false arm of ``if trimmed:`` at line 107)."""
        uc = {
            "i": "1.1.1",
            "n": "Title",
            "sapp": ["garbage", None, 42],
        }
        stub = render_api._stub_uc(uc, 1, "1.1")
        assert "sapp" not in stub

    def test_stub_uc_drops_heavy_fields_keeps_light(self, tmp_path: Path):
        uc = {
            "i": "1.1.1",
            "n": "Title",
            "q": "big spl",
            "md": "big md",
            "prio": 1,
        }
        stub = render_api._stub_uc(uc, 1, "1.1")
        assert "q" not in stub and "md" not in stub
        assert stub["i"] == "1.1.1" and stub["cat"] == 1 and stub["sub"] == "1.1"
        assert stub["prio"] == 1


class TestRenderApi:
    CATALOG_INDEX_KEYS = frozenset({
        "$schema",
        "version",
        "generatedAt",
        "counts",
        "catGroups",
        "catMeta",
        "equipment",
        "filterFacets",
        "recentlyAdded",
        "categories",
        "ucs",
        "regulations",
    })

    def test_catalog_index_structure(self, tmp_path: Path):
        catalog = _minimal_catalog(tmp_path)
        api_dir = tmp_path / "api"
        api_dir.mkdir(parents=True)
        render_api._write_catalog_index(catalog, api_dir, reproducible=True)

        path = api_dir / "catalog-index.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert set(data.keys()) == self.CATALOG_INDEX_KEYS
        assert data["counts"]["categories"] == 1
        assert data["counts"]["useCases"] == 2
        assert data["generatedAt"] == "1970-01-01T00:00:00Z"
        assert data["catGroups"] == {"g": [3]}
        assert data["equipment"] == [{"k": "v"}]
        assert data["filterFacets"] == {"foo": ["bar"]}
        assert data["recentlyAdded"] == ["3.2.10"]

        cat0 = data["categories"][0]
        assert cat0["i"] == 3
        assert cat0["lazyHref"] == "api/cat-3.json"
        assert cat0["icon"] == "net"
        assert len(cat0["subs"]) == 1
        assert cat0["subs"][0]["ucs"] == 2

        ucs = data["ucs"]
        assert len(ucs) == 2
        ids = [u["i"] for u in ucs]
        assert ids == ["3.2.5", "3.2.10"]

    def test_manifest_paths(self, tmp_path: Path):
        catalog = _minimal_catalog(tmp_path)
        api_dir = tmp_path / "api"
        api_dir.mkdir(parents=True)
        render_api._write_path_manifest(catalog, api_dir, reproducible=True)

        m = json.loads((api_dir / "manifest.json").read_text(encoding="utf-8"))
        assert m["counts"]["useCases"] == 2
        assert len(m["paths"]["ucs"]) == 2
        uc_rows = {r["id"] for r in m["paths"]["ucs"]}
        assert uc_rows == {"UC-3.2.5", "UC-3.2.10"}

    def test_render_creates_api_tree(self, tmp_path: Path):
        catalog = _minimal_catalog(tmp_path)
        dist = tmp_path / "dist"
        render_api.render(catalog, dist, reproducible=True)

        api = dist / "api"
        for name in ("catalog-index.json", "cat-3.json", "manifest.json", "shortlinks.json"):
            assert (api / name).is_file()

    def test_regulations_index_and_counts(self, tmp_path: Path):
        catalog = parse_content.Catalog(
            project_root=tmp_path,
            categories=[
                {
                    "i": 1,
                    "n": "C",
                    "s": [
                        {
                            "i": "1.1",
                            "n": "S",
                            "u": [{"i": "1.1.1", "n": "U", "regs": ["GDPR", "bogus"]}],
                        }
                    ],
                }
            ],
            regulations={
                "gdpr": {
                    "name": "General Data Protection Regulation",
                    "shortName": "GDPR",
                    "aliases": ["GDPR"],
                }
            },
        )
        idx = render_api._build_regulations_index(catalog)
        assert len(idx) == 1
        assert idx[0]["id"] == "gdpr"
        assert idx[0]["ucCount"] == 1
        assert "lazyHref" in idx[0]


class TestDefensiveIsInstanceGuards:
    """The render_api helpers carry three ``isinstance(...) -> continue``
    guards (lines 297, 348, 367) that handle malformed JSON sneaking
    past schema validation. These tests inject the malformed shapes
    directly so the defensive branches actually execute."""

    def test_build_regulations_skips_non_dict_entry(self, tmp_path: Path):
        """Line 297: ``if not isinstance(reg, dict): continue``."""
        cat = parse_content.Catalog(
            project_root=tmp_path,
            categories=[],
            regulations={
                "valid": {"name": "Valid", "shortName": "V"},
                "garbage": "not a dict",  # type: ignore[dict-item]
            },
        )
        idx = render_api._build_regulations_index(cat)
        # Garbage filtered; only valid entry returned.
        ids = [entry["id"] for entry in idx]
        assert ids == ["valid"]

    def test_count_ucs_per_regulation_skips_non_dict_regulation(
        self, tmp_path: Path
    ):
        """Line 348: alias-collection loop guards against malformed
        regulation JSON. The tag-match loop still has to run, so we
        need a UC referencing the valid regulation."""
        cat = parse_content.Catalog(
            project_root=tmp_path,
            categories=[
                {
                    "i": 1,
                    "n": "C",
                    "s": [
                        {
                            "i": "1.1",
                            "n": "S",
                            "u": [
                                {"i": "1.1.1", "n": "U", "regs": ["VALID"]},
                            ],
                        }
                    ],
                }
            ],
            regulations={
                "valid": {"name": "Valid Reg", "shortName": "VALID"},
                "garbage": 42,  # type: ignore[dict-item]
            },
        )
        counts = render_api._count_ucs_per_regulation(cat)
        # Garbage didn't crash; valid still matched.
        assert counts.get("valid") == 1

    def test_count_ucs_per_regulation_skips_non_string_tag(self, tmp_path: Path):
        """Line 367: ``if not isinstance(raw_tag, str): continue`` —
        defensive guard for malformed ``regs`` list entries."""
        cat = parse_content.Catalog(
            project_root=tmp_path,
            categories=[
                {
                    "i": 1,
                    "n": "C",
                    "s": [
                        {
                            "i": "1.1",
                            "n": "S",
                            "u": [
                                # ``regs`` carries a mix of valid and
                                # malformed entries.
                                {
                                    "i": "1.1.1",
                                    "n": "U",
                                    "regs": ["GDPR", 123, None, {"x": 1}],  # type: ignore[list-item]
                                },
                            ],
                        }
                    ],
                }
            ],
            regulations={
                "gdpr": {"name": "GDPR", "shortName": "GDPR"},
            },
        )
        counts = render_api._count_ucs_per_regulation(cat)
        # Only the string "GDPR" matched; non-string tags ignored.
        assert counts.get("gdpr") == 1
