"""Hermetic tests for ``tools/build/render_meta.py``.

Covers the static-file writers (robots/security/pwa/ai), the Atom
feed builder, the sharded sitemap-index + per-section sitemaps, the
machine-consumer manifest, the OpenAPI v2 template renderer, and the
shared timestamp helpers.
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from build import render_meta as rm
from build.parse_content import Catalog


def _empty_catalog(tmp_path: Path, **overrides) -> Catalog:
    kwargs = dict(
        project_root=tmp_path,
        categories=[],
        cat_meta={},
        cat_groups={},
        equipment=[],
        regulations={},
        recently_added=[],
        facets={},
    )
    kwargs.update(overrides)
    return Catalog(**kwargs)


def _seeded_catalog(tmp_path: Path) -> Catalog:
    """Catalog with one cat, two UCs, and two regulations."""
    return _empty_catalog(
        tmp_path,
        categories=[
            {
                "i": 1,
                "n": "Network",
                "s": [
                    {
                        "i": "1.1",
                        "n": "Routing",
                        "u": [
                            {"i": "1.1.1", "n": "OSPF down", "regs": ["GDPR"]},
                            {"i": "1.1.2", "n": "BGP flapping", "regs": ["NIST"]},
                        ],
                    }
                ],
            }
        ],
        regulations={
            "gdpr": {"name": "General Data Protection Regulation", "shortName": "GDPR"},
            "nist": {"name": "NIST Cybersecurity Framework", "shortName": "NIST"},
        },
        files=["cat-01-network.md"],
        recently_added=["1.1.1"],
    )


# ---------------------------------------------------------------------------
# _write_robots / _write_pwa_manifest / _write_security_txt / _write_well_known_ai_txt
# ---------------------------------------------------------------------------


class TestStaticWriters:
    def test_write_robots_creates_file_when_absent(self, tmp_path: Path):
        rm._write_robots(tmp_path)
        body = (tmp_path / "robots.txt").read_text(encoding="utf-8")
        assert "User-agent: *" in body
        assert "Allow: /" in body
        assert "Disallow: /assets/search-shard-" in body
        assert "Sitemap: " in body

    def test_write_robots_preserves_existing_file(self, tmp_path: Path):
        """Covers the early-return on line 58."""
        (tmp_path / "robots.txt").write_text("preserve me\n", encoding="utf-8")
        rm._write_robots(tmp_path)
        assert (tmp_path / "robots.txt").read_text(encoding="utf-8") == "preserve me\n"

    def test_write_pwa_manifest_creates_file_when_absent(self, tmp_path: Path):
        rm._write_pwa_manifest(tmp_path)
        manifest = json.loads(
            (tmp_path / "manifest.webmanifest").read_text(encoding="utf-8")
        )
        assert manifest["name"] == "Splunk Monitoring Use Cases"
        assert manifest["short_name"] == "Splunk UCs"
        assert manifest["display"] == "standalone"
        # Three icons, all rooted at the SITE_URL path
        assert len(manifest["icons"]) == 3
        for icon in manifest["icons"]:
            assert icon["src"].endswith((".png", ".svg"))

    def test_write_pwa_manifest_preserves_existing_file(self, tmp_path: Path):
        """Covers the early-return on line 77."""
        (tmp_path / "manifest.webmanifest").write_text("{}", encoding="utf-8")
        rm._write_pwa_manifest(tmp_path)
        assert (tmp_path / "manifest.webmanifest").read_text(encoding="utf-8") == "{}"

    def test_write_security_txt_creates_file_with_well_known_dir(
        self, tmp_path: Path
    ):
        rm._write_security_txt(tmp_path)
        body = (tmp_path / ".well-known" / "security.txt").read_text(encoding="utf-8")
        assert body.startswith("Contact: ")
        assert "Expires: 2099-12-31T23:59:59Z" in body
        assert "Preferred-Languages: en" in body

    def test_write_security_txt_preserves_existing_file(self, tmp_path: Path):
        """Covers the early-return on line 103."""
        (tmp_path / ".well-known").mkdir()
        (tmp_path / ".well-known" / "security.txt").write_text(
            "custom", encoding="utf-8"
        )
        rm._write_security_txt(tmp_path)
        assert (
            tmp_path / ".well-known" / "security.txt"
        ).read_text(encoding="utf-8") == "custom"

    def test_write_ai_txt_skips_when_source_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """Covers the early-return on line 130 (source missing)."""
        # Point __file__ at a tmp tree that does NOT carry ai.txt.
        fake = tmp_path / "tools" / "build" / "render_meta.py"
        fake.parent.mkdir(parents=True)
        fake.touch()
        monkeypatch.setattr(rm, "__file__", str(fake))
        rm._write_well_known_ai_txt(tmp_path)
        assert not (tmp_path / ".well-known" / "ai.txt").exists()

    def test_write_ai_txt_mirrors_source_to_well_known(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """Copies the source ai.txt into ``.well-known/`` when present
        and the destination is absent."""
        fake = tmp_path / "tools" / "build" / "render_meta.py"
        fake.parent.mkdir(parents=True)
        fake.touch()
        (tmp_path / "ai.txt").write_text("AI policy\n", encoding="utf-8")
        monkeypatch.setattr(rm, "__file__", str(fake))
        out_dir = tmp_path / "dist"
        out_dir.mkdir()
        rm._write_well_known_ai_txt(out_dir)
        assert (out_dir / ".well-known" / "ai.txt").read_text(encoding="utf-8") == (
            "AI policy\n"
        )

    def test_write_ai_txt_preserves_existing_destination(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """Covers the early-return on line 133."""
        fake = tmp_path / "tools" / "build" / "render_meta.py"
        fake.parent.mkdir(parents=True)
        fake.touch()
        (tmp_path / "ai.txt").write_text("source ai\n", encoding="utf-8")
        monkeypatch.setattr(rm, "__file__", str(fake))
        out_dir = tmp_path / "dist"
        (out_dir / ".well-known").mkdir(parents=True)
        (out_dir / ".well-known" / "ai.txt").write_text(
            "dest preserved", encoding="utf-8"
        )
        rm._write_well_known_ai_txt(out_dir)
        assert (out_dir / ".well-known" / "ai.txt").read_text(encoding="utf-8") == (
            "dest preserved"
        )


# ---------------------------------------------------------------------------
# _write_atom_feed + _atom_entry
# ---------------------------------------------------------------------------


class TestAtomFeed:
    def test_atom_entry_escapes_special_characters(self):
        entry = rm._atom_entry(
            uc_id="1.1.1",
            title="Quotes & ampersands",
            link="https://example.test/uc/UC-1.1.1/",
            updated="2026-01-01T00:00:00Z",
        )
        assert "&amp;" in entry  # 'Quotes & ampersands' escaped
        assert "<id>https://example.test/uc/UC-1.1.1/</id>" in entry
        assert "<updated>2026-01-01T00:00:00Z</updated>" in entry

    def test_write_atom_feed_uses_recently_added_first(self, tmp_path: Path):
        cat = _seeded_catalog(tmp_path)
        rm._write_atom_feed(cat, tmp_path, reproducible=True)
        body = (tmp_path / "feed.xml").read_text(encoding="utf-8")
        assert "<feed " in body
        # UC-1.1.1 came from recently_added
        assert "UC-1.1.1 OSPF down" in body

    def test_write_atom_feed_falls_back_to_uc_iterator_when_recently_added_empty(
        self, tmp_path: Path
    ):
        """Covers the fallback loop on lines 164-174."""
        cat = _empty_catalog(
            tmp_path,
            categories=[
                {
                    "i": 1, "n": "X",
                    "s": [{"i": "1.1", "u": [{"i": "1.1.1", "n": "Alpha"}]}],
                }
            ],
        )
        rm._write_atom_feed(cat, tmp_path, reproducible=True)
        body = (tmp_path / "feed.xml").read_text(encoding="utf-8")
        assert "UC-1.1.1 Alpha" in body

    def test_write_atom_feed_fallback_caps_at_50_entries(self, tmp_path: Path):
        """The fallback loop on line 173 breaks at 50 entries.
        Generate >50 UCs in a catalog with empty ``recently_added`` and
        assert the entry count is exactly 50."""
        ucs = [{"i": f"1.1.{i}", "n": f"UC {i}"} for i in range(1, 56)]
        cat = _empty_catalog(
            tmp_path,
            categories=[
                {"i": 1, "n": "X", "s": [{"i": "1.1", "u": ucs}]},
            ],
        )
        rm._write_atom_feed(cat, tmp_path, reproducible=True)
        body = (tmp_path / "feed.xml").read_text(encoding="utf-8")
        # Each entry block starts with "  <entry>" on its own line.
        entry_count = body.count("<entry>")
        assert entry_count == 50

    def test_write_atom_feed_preserves_existing_file(self, tmp_path: Path):
        """Covers the early-return on line 146."""
        (tmp_path / "feed.xml").write_text("preserved", encoding="utf-8")
        cat = _seeded_catalog(tmp_path)
        rm._write_atom_feed(cat, tmp_path, reproducible=True)
        assert (tmp_path / "feed.xml").read_text(encoding="utf-8") == "preserved"

    def test_write_atom_feed_uses_wall_clock_when_not_reproducible(
        self, tmp_path: Path
    ):
        """Covers the ``datetime.now(...)`` branch on line 149."""
        cat = _seeded_catalog(tmp_path)
        rm._write_atom_feed(cat, tmp_path, reproducible=False)
        body = (tmp_path / "feed.xml").read_text(encoding="utf-8")
        assert re.search(
            r"<updated>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z</updated>", body
        )

    def test_write_atom_feed_deduplicates_recently_added(self, tmp_path: Path):
        """If ``recently_added`` carries the same id twice, the
        ``seen`` set drops the duplicate (covers line 157 false arm)."""
        cat = _seeded_catalog(tmp_path)
        cat.recently_added = ["1.1.1", "1.1.1", "1.1.2"]
        rm._write_atom_feed(cat, tmp_path, reproducible=True)
        body = (tmp_path / "feed.xml").read_text(encoding="utf-8")
        assert body.count("<id>https://fenre.github.io/splunk-monitoring-use-cases/uc/UC-1.1.1/</id>") == 1

    def test_write_atom_feed_skips_unknown_uc_ids(self, tmp_path: Path):
        """An id in ``recently_added`` that doesn't resolve via
        ``uc_by_id`` is silently skipped (covers line 157 — ``not uc``)."""
        cat = _seeded_catalog(tmp_path)
        cat.recently_added = ["9.9.9", "1.1.1"]  # 9.9.9 doesn't exist
        rm._write_atom_feed(cat, tmp_path, reproducible=True)
        body = (tmp_path / "feed.xml").read_text(encoding="utf-8")
        assert "UC-9.9.9" not in body
        assert "UC-1.1.1 OSPF down" in body


# ---------------------------------------------------------------------------
# _write_sitemap and the urlset / sitemap-index helpers
# ---------------------------------------------------------------------------


class TestSitemap:
    def test_write_sitemap_emits_index_plus_per_section_files(
        self, tmp_path: Path
    ):
        cat = _seeded_catalog(tmp_path)
        rm._write_sitemap(cat, tmp_path, reproducible=True)
        for name in (
            "sitemap.xml",
            "sitemap-pages.xml",
            "sitemap-categories.xml",
            "sitemap-regulations.xml",
            "sitemap-ucs-01.xml",
        ):
            assert (tmp_path / name).exists(), f"missing {name}"

        # sitemap-pages always has the 4 fixed entries
        pages = (tmp_path / "sitemap-pages.xml").read_text(encoding="utf-8")
        for path in ("/", "/browse/", "/regulation/", "/api/"):
            assert path in pages

        # sitemap-categories points at the 'network' slug
        cats = (tmp_path / "sitemap-categories.xml").read_text(encoding="utf-8")
        assert "/category/network/" in cats

        # sitemap-regulations carries both matched regs
        regs = (tmp_path / "sitemap-regulations.xml").read_text(encoding="utf-8")
        assert "/regulation/" in regs

        # UC sitemap shard carries both UCs
        ucs_shard = (tmp_path / "sitemap-ucs-01.xml").read_text(encoding="utf-8")
        assert "/uc/UC-1.1.1/" in ucs_shard
        assert "/uc/UC-1.1.2/" in ucs_shard

        # sitemap.xml index references every emitted file
        idx = (tmp_path / "sitemap.xml").read_text(encoding="utf-8")
        for name in (
            "sitemap-pages.xml",
            "sitemap-categories.xml",
            "sitemap-regulations.xml",
            "sitemap-ucs-01.xml",
        ):
            assert name in idx

    def test_write_sitemap_removes_stale_uc_shards(self, tmp_path: Path):
        """Pre-existing ``sitemap-ucs-NN.xml`` files from larger prior
        catalogs are unlinked before the new shards are written
        (covers line 277-278)."""
        (tmp_path / "sitemap-ucs-99.xml").write_text("stale", encoding="utf-8")
        cat = _seeded_catalog(tmp_path)
        rm._write_sitemap(cat, tmp_path, reproducible=True)
        assert not (tmp_path / "sitemap-ucs-99.xml").exists()

    def test_write_sitemap_skips_category_without_id_or_slug(
        self, tmp_path: Path
    ):
        """A category without ``i`` (line 240) or without a slug in
        ``cat_slug_for`` (line 243) is omitted from the category
        sitemap."""
        cat = _empty_catalog(
            tmp_path,
            categories=[
                {"i": 1, "n": "Network", "s": []},
                {"n": "Headless"},  # no `i` → skipped
            ],
        )
        rm._write_sitemap(cat, tmp_path, reproducible=True)
        body = (tmp_path / "sitemap-categories.xml").read_text(encoding="utf-8")
        # The headless category isn't present.
        assert body.count("<url>") == 1

    def test_write_sitemap_with_empty_catalog_still_emits_index(
        self, tmp_path: Path
    ):
        """An empty catalog (no UCs, no regs) still emits the index +
        the three fixed-section sitemaps; no UC shard is written
        because ``uc_locs`` is empty (covers the false arm of
        ``if uc_locs:`` on line 281)."""
        cat = _empty_catalog(tmp_path)
        rm._write_sitemap(cat, tmp_path, reproducible=True)
        assert (tmp_path / "sitemap.xml").exists()
        assert (tmp_path / "sitemap-pages.xml").exists()
        assert (tmp_path / "sitemap-categories.xml").exists()
        assert (tmp_path / "sitemap-regulations.xml").exists()
        assert not list(tmp_path.glob("sitemap-ucs-*.xml"))

    def test_write_sitemap_non_reproducible_skips_sort(
        self, tmp_path: Path
    ):
        """``reproducible=False`` (the developer default) MUST NOT
        sort the URL lists — preserves the natural catalog order so
        local previews match what the SPA renders. Covers the false
        arm of ``if reproducible:`` (branch 266→271)."""
        cat = _empty_catalog(
            tmp_path,
            categories=[
                {
                    "i": 1, "n": "X",
                    "s": [
                        {"i": "1.1", "u": [
                            {"i": "1.1.2", "n": "Bravo"},
                            {"i": "1.1.1", "n": "Alpha"},
                        ]}
                    ],
                }
            ],
            files=["cat-01-x.md"],
        )
        rm._write_sitemap(cat, tmp_path, reproducible=False)
        shard = (tmp_path / "sitemap-ucs-01.xml").read_text(encoding="utf-8")
        # Natural insertion order preserved: 1.1.2 first, then 1.1.1.
        pos_111 = shard.find("/uc/UC-1.1.1/")
        pos_112 = shard.find("/uc/UC-1.1.2/")
        assert 0 <= pos_112 < pos_111

    def test_write_sitemap_skips_uc_without_id(self, tmp_path: Path):
        """A UC dict without ``i`` (or empty ``i``) is excluded from
        the UC sitemap (covers branch 263→261)."""
        cat = _empty_catalog(
            tmp_path,
            categories=[
                {
                    "i": 1, "n": "X",
                    "s": [
                        {"i": "1.1", "u": [
                            {"i": "1.1.1", "n": "Alpha"},
                            {"n": "Headless"},  # no `i` → skipped
                        ]}
                    ],
                }
            ],
            files=["cat-01-x.md"],
        )
        rm._write_sitemap(cat, tmp_path, reproducible=True)
        shard = (tmp_path / "sitemap-ucs-01.xml").read_text(encoding="utf-8")
        # Only the real UC made it in.
        assert shard.count("<url>") == 1
        assert "/uc/UC-1.1.1/" in shard

    def test_write_sitemap_unmatched_reg_tag_does_not_promote_to_matched_set(
        self, tmp_path: Path
    ):
        """When a UC carries a ``regs`` entry that doesn't resolve to
        any known framework (``_resolve_alias`` returns empty), the
        false arm of ``if fw_id:`` (branch 251→249) is taken and the
        regulation sitemap is empty."""
        cat = _empty_catalog(
            tmp_path,
            categories=[
                {
                    "i": 1, "n": "X",
                    "s": [
                        {"i": "1.1", "u": [
                            {"i": "1.1.1", "regs": ["Made-Up Framework"]}
                        ]}
                    ],
                }
            ],
            regulations={
                "gdpr": {"name": "GDPR", "shortName": "GDPR"},
            },
            files=["cat-01-x.md"],
        )
        rm._write_sitemap(cat, tmp_path, reproducible=True)
        regs = (tmp_path / "sitemap-regulations.xml").read_text(encoding="utf-8")
        # No URL inside the urlset block.
        assert "<url>" not in regs

    def test_write_sitemap_sorts_locs_when_reproducible(self, tmp_path: Path):
        """``reproducible=True`` sorts the URL lists before emitting
        (covers lines 266-269)."""
        # Two UCs whose natural insertion order ≠ lex-sorted order.
        cat = _empty_catalog(
            tmp_path,
            categories=[
                {
                    "i": 1, "n": "X",
                    "s": [
                        {"i": "1.1", "u": [
                            {"i": "1.1.2", "n": "Bravo"},
                            {"i": "1.1.1", "n": "Alpha"},
                        ]}
                    ],
                }
            ],
            files=["cat-01-x.md"],
        )
        rm._write_sitemap(cat, tmp_path, reproducible=True)
        shard = (tmp_path / "sitemap-ucs-01.xml").read_text(encoding="utf-8")
        # Verify 1.1.1 appears before 1.1.2 (lex-sorted)
        pos_111 = shard.find("/uc/UC-1.1.1/")
        pos_112 = shard.find("/uc/UC-1.1.2/")
        assert 0 <= pos_111 < pos_112


class TestUrlsetAndSitemapIndex:
    def test_write_urlset_escapes_xml_special_chars(self, tmp_path: Path):
        path = tmp_path / "out.xml"
        rm._write_urlset(
            path,
            ["https://example.test/path?a=1&b=2"],
            lastmod="2026-01-01",
        )
        body = path.read_text(encoding="utf-8")
        assert "&amp;" in body
        # Parses as valid XML
        ET.fromstring(body)

    def test_write_urlset_creates_parent_directory(self, tmp_path: Path):
        path = tmp_path / "nested" / "out.xml"
        rm._write_urlset(path, ["https://example.test/"], lastmod="2026-01-01")
        assert path.exists()
        assert path.parent.is_dir()

    def test_write_sitemap_index_emits_one_sitemap_per_entry(self, tmp_path: Path):
        path = tmp_path / "index.xml"
        rm._write_sitemap_index(
            path,
            sitemaps=["a.xml", "b.xml"],
            lastmod="2026-01-01",
        )
        body = path.read_text(encoding="utf-8")
        assert body.count("<sitemap>") == 2
        # Parses as valid XML
        ET.fromstring(body)


# ---------------------------------------------------------------------------
# _write_machine_manifest
# ---------------------------------------------------------------------------


class TestMachineManifest:
    def test_emits_well_formed_manifest_with_expected_stats(
        self, tmp_path: Path
    ):
        cat = _seeded_catalog(tmp_path)
        rm._write_machine_manifest(cat, tmp_path, reproducible=True)
        manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))

        assert manifest["$schema"] == "/schemas/v2/manifest.schema.json"
        assert manifest["version"] == "2.0.0"
        assert manifest["stats"]["useCases"] == 2
        assert manifest["stats"]["categories"] == 1
        assert manifest["stats"]["totalRegulations"] == 2
        # Both regulations are matched (each has 1 UC carrying its
        # shortName), so the count is 2.
        assert manifest["stats"]["regulations"] == 2
        assert manifest["categories"][0]["id"] == 1
        assert manifest["categories"][0]["name"] == "Network"
        assert manifest["categories"][0]["useCases"] == 2
        assert len(manifest["regulations"]) == 2

    def test_machine_manifest_drops_unresolved_reg_tags(self, tmp_path: Path):
        """When a UC's ``regs`` entry doesn't resolve via
        ``_resolve_alias``, the false arm of ``if fw_id:`` (branch
        354→352) is taken and the regulation never appears in the
        manifest's ``regulations`` array."""
        cat = _empty_catalog(
            tmp_path,
            categories=[
                {
                    "i": 1, "n": "X",
                    "s": [
                        {"i": "1.1", "u": [
                            {"i": "1.1.1", "regs": ["Unknown Framework"]}
                        ]}
                    ],
                }
            ],
            regulations={
                "gdpr": {"name": "GDPR", "shortName": "GDPR"},
            },
            files=["cat-01-x.md"],
        )
        rm._write_machine_manifest(cat, tmp_path, reproducible=True)
        manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["stats"]["regulations"] == 0
        assert manifest["regulations"] == []

    def test_categories_skips_entries_without_id(self, tmp_path: Path):
        """A category without ``i`` is excluded from the manifest's
        ``categories`` array (covers line 390 ``if cat.get('i') is not
        None``)."""
        cat = _empty_catalog(
            tmp_path,
            categories=[
                {"i": 1, "n": "Network", "s": []},
                {"n": "Headless"},
            ],
            files=["cat-01-network.md"],
        )
        rm._write_machine_manifest(cat, tmp_path, reproducible=True)
        manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
        assert [c["id"] for c in manifest["categories"]] == [1]


# ---------------------------------------------------------------------------
# _write_openapi_v2
# ---------------------------------------------------------------------------


class TestOpenApiV2:
    def test_emits_well_formed_yaml_with_counts(self, tmp_path: Path):
        cat = _seeded_catalog(tmp_path)
        rm._write_openapi_v2(cat, tmp_path, reproducible=True)
        spec = (tmp_path / "api" / "v2" / "openapi.yaml").read_text(encoding="utf-8")
        assert "openapi: 3.1.0" in spec
        assert "Splunk Monitoring Use Cases — SSG Catalog API (v2)" in spec
        # Counts are formatted into the body
        assert "2 use cases" in spec
        assert "1 categories" in spec
        assert "2 regulatory frameworks" in spec
        # Paths block exists
        assert "/manifest.json:" in spec
        assert "/uc/{useCaseId}/index.json:" in spec


# ---------------------------------------------------------------------------
# _timestamp / _date_only
# ---------------------------------------------------------------------------


class TestTimestampHelpers:
    def test_timestamp_reproducible_uses_source_date_epoch(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
        assert rm._timestamp(reproducible=True) == "2023-11-14T22:13:20Z"

    def test_timestamp_reproducible_invalid_epoch_falls_back_to_unix_epoch(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "not-an-int")
        assert rm._timestamp(reproducible=True) == "1970-01-01T00:00:00Z"

    def test_timestamp_reproducible_missing_env_defaults_to_zero(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
        assert rm._timestamp(reproducible=True) == "1970-01-01T00:00:00Z"

    def test_timestamp_non_reproducible_uses_wall_clock(self):
        out = rm._timestamp(reproducible=False)
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", out), out

    def test_date_only_returns_first_10_chars_of_timestamp(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
        assert rm._date_only(reproducible=True) == "2023-11-14"


# ---------------------------------------------------------------------------
# render() — top-level orchestrator smoke test
# ---------------------------------------------------------------------------


class TestRender:
    def test_render_emits_all_top_level_artefacts(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """End-to-end: every static + sitemap + manifest + openapi
        artefact lands under ``out_dir`` and parses as expected."""
        # Source an ai.txt for the well-known mirror
        (tmp_path / "ai.txt").write_text("AI policy\n", encoding="utf-8")
        fake = tmp_path / "tools" / "build" / "render_meta.py"
        fake.parent.mkdir(parents=True)
        fake.touch()
        monkeypatch.setattr(rm, "__file__", str(fake))

        cat = _seeded_catalog(tmp_path)
        out_dir = tmp_path / "dist"
        out_dir.mkdir()  # render() expects an existing out_dir
        rm.render(cat, out_dir, reproducible=True)

        for name in (
            "robots.txt",
            "manifest.webmanifest",
            ".well-known/security.txt",
            ".well-known/ai.txt",
            "feed.xml",
            "sitemap.xml",
            "manifest.json",
            "api/v2/openapi.yaml",
        ):
            assert (out_dir / name).exists(), f"missing {name}"
