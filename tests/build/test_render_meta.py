"""Hermetic tests for tools/build/render_meta.py.

Targets the discovery surface emitted by ``render_meta.render``:

* ``robots.txt`` (writes once, idempotent)
* ``manifest.webmanifest`` (PWA install metadata)
* ``.well-known/security.txt``
* ``.well-known/ai.txt`` (mirrored from project-root ``ai.txt``)
* ``feed.xml`` (Atom feed of the last 50 added UCs; falls back to
  reverse-chrono iter_ucs when ``recently_added`` is empty)
* ``sitemap.xml`` (sharded sitemap-index)
* ``sitemap-pages.xml`` / ``-categories.xml`` / ``-regulations.xml``
* ``sitemap-ucs-NN.xml`` (UC shards sized by ``_UC_SHARD_SIZE``)
* ``manifest.json`` (machine consumer URL index)
* ``api/v2/openapi.yaml`` (OpenAPI 3.1 description)

Every test runs against an isolated ``tmp_path`` and a hand-built
``Catalog`` so the suite never reaches the real ``content/`` tree or
the network.
"""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TOOLS_DIR = str(REPO_ROOT / "tools")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from build import render_meta as M  # noqa: E402
from build.parse_content import Catalog  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_catalog(tmp_path: Path, *, with_recently: bool = True) -> Catalog:
    """Return a small, deterministic ``Catalog`` for sitemap/manifest tests.

    Two categories, one regulation, three UCs (two in cat 1, one in
    cat 2). One UC is tagged with the regulation so the manifest /
    sitemap only counts matched frameworks.
    """
    cat = Catalog(project_root=tmp_path)
    cat.files = ["cat-01-monitoring.md", "cat-02-security.md"]
    cat.categories = [
        {
            "i": 1,
            "n": "Monitoring",
            "s": [
                {
                    "i": "1.1",
                    "n": "Server health",
                    "u": [
                        {"i": "1.1.1", "n": "CPU saturation"},
                        {"i": "1.1.2", "n": "Memory exhaustion", "regs": ["pci-dss"]},
                    ],
                }
            ],
        },
        {
            "i": 2,
            "n": "Security",
            "s": [
                {
                    "i": "2.1",
                    "n": "Authentication",
                    "u": [{"i": "2.1.1", "n": "Brute force"}],
                }
            ],
        },
    ]
    cat.regulations = {
        "pci-dss": {
            "id": "pci-dss",
            "shortName": "PCI DSS",
            "name": "Payment Card Industry Data Security Standard",
        }
    }
    if with_recently:
        cat.recently_added = ["1.1.1", "1.1.2"]
    return cat


@pytest.fixture
def catalog(tmp_path: Path) -> Catalog:
    return _make_catalog(tmp_path)


@pytest.fixture
def out_dir(tmp_path: Path) -> Path:
    d = tmp_path / "dist"
    d.mkdir()
    return d


# ---------------------------------------------------------------------------
# robots.txt / PWA manifest / security.txt — idempotent helpers
# ---------------------------------------------------------------------------


class TestWriteRobots:
    def test_creates_when_absent(self, out_dir: Path) -> None:
        M._write_robots(out_dir)
        body = (out_dir / "robots.txt").read_text(encoding="utf-8")
        assert body.startswith("User-agent: *\n")
        assert "Sitemap: " in body
        assert M.SITE_URL in body

    def test_skipped_when_already_present(self, out_dir: Path) -> None:
        (out_dir / "robots.txt").write_text("DO NOT TOUCH", encoding="utf-8")
        M._write_robots(out_dir)
        assert (out_dir / "robots.txt").read_text(encoding="utf-8") == "DO NOT TOUCH"


class TestWritePwaManifest:
    def test_creates_well_formed_manifest(self, out_dir: Path) -> None:
        M._write_pwa_manifest(out_dir)
        manifest = json.loads((out_dir / "manifest.webmanifest").read_text(encoding="utf-8"))
        assert manifest["name"] == "Splunk Monitoring Use Cases"
        assert manifest["display"] == "standalone"
        assert {i["sizes"] for i in manifest["icons"]} == {"192x192", "512x512", "any"}

    def test_idempotent(self, out_dir: Path) -> None:
        (out_dir / "manifest.webmanifest").write_text("{}", encoding="utf-8")
        M._write_pwa_manifest(out_dir)
        assert (out_dir / "manifest.webmanifest").read_text(encoding="utf-8") == "{}"


class TestWriteSecurityTxt:
    def test_creates_in_well_known(self, out_dir: Path) -> None:
        M._write_security_txt(out_dir)
        text = (out_dir / ".well-known" / "security.txt").read_text(encoding="utf-8")
        assert text.startswith("Contact:")
        assert "Expires:" in text

    def test_idempotent(self, out_dir: Path) -> None:
        target = out_dir / ".well-known" / "security.txt"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("PRESERVED", encoding="utf-8")
        M._write_security_txt(out_dir)
        assert target.read_text(encoding="utf-8") == "PRESERVED"


# ---------------------------------------------------------------------------
# .well-known/ai.txt mirror
# ---------------------------------------------------------------------------


class TestWriteWellKnownAiTxt:
    def test_mirrors_from_project_root(self, out_dir: Path) -> None:
        # ai.txt exists at the real project root; the mirror should
        # produce a copy under .well-known/.
        M._write_well_known_ai_txt(out_dir)
        dst = out_dir / ".well-known" / "ai.txt"
        assert dst.exists()
        src = REPO_ROOT / "ai.txt"
        assert dst.read_text(encoding="utf-8") == src.read_text(encoding="utf-8")

    def test_idempotent(self, out_dir: Path) -> None:
        dst = out_dir / ".well-known" / "ai.txt"
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text("KEEP-ME", encoding="utf-8")
        M._write_well_known_ai_txt(out_dir)
        assert dst.read_text(encoding="utf-8") == "KEEP-ME"

    def test_silent_skip_when_source_missing(
        self, out_dir: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # Re-route Path(__file__) by substituting the module-level path
        # walker — easiest is to monkeypatch the helper to read from a
        # fake project root that has no ai.txt.
        fake_root = tmp_path / "fake-root"
        fake_root.mkdir()
        # No ai.txt here; helper must silently skip.
        original_render_meta_file = M.__file__
        # Build a fake Path object whose grandparent.parent.parent is fake_root.
        fake_module_path = (
            fake_root / "tools" / "build" / "render_meta.py"
        )
        fake_module_path.parent.mkdir(parents=True)
        fake_module_path.write_text("# placeholder", encoding="utf-8")
        monkeypatch.setattr(M, "__file__", str(fake_module_path))
        try:
            M._write_well_known_ai_txt(out_dir)
            assert not (out_dir / ".well-known" / "ai.txt").exists()
        finally:
            monkeypatch.setattr(M, "__file__", original_render_meta_file)


# ---------------------------------------------------------------------------
# Atom feed
# ---------------------------------------------------------------------------


class TestAtomEntry:
    def test_escapes_special_chars(self) -> None:
        entry = M._atom_entry("1.1.1", "Title <X>", "https://example.com/x?y=1&z=2", "1970-01-01T00:00:00Z")
        # Title is XML-escaped
        assert "Title &lt;X&gt;" in entry
        # ampersand in link is escaped
        assert "y=1&amp;z=2" in entry
        assert "<id>https://example.com/x?y=1&amp;z=2</id>" in entry


class TestWriteAtomFeed:
    def test_uses_recently_added_first(
        self, catalog: Catalog, out_dir: Path
    ) -> None:
        M._write_atom_feed(catalog, out_dir, reproducible=True)
        body = (out_dir / "feed.xml").read_text(encoding="utf-8")
        # Both recently-added IDs are present
        assert "UC-1.1.1" in body
        assert "UC-1.1.2" in body
        # Updated timestamp is the reproducible epoch
        assert "<updated>1970-01-01T00:00:00Z</updated>" in body

    def test_falls_back_to_iter_ucs_when_recently_empty(
        self, tmp_path: Path, out_dir: Path
    ) -> None:
        cat = _make_catalog(tmp_path, with_recently=False)
        M._write_atom_feed(cat, out_dir, reproducible=True)
        body = (out_dir / "feed.xml").read_text(encoding="utf-8")
        # All three UCs surface from iter_ucs fallback
        for uc_id in ("UC-1.1.1", "UC-1.1.2", "UC-2.1.1"):
            assert uc_id in body

    def test_skips_unknown_recent_ids(self, tmp_path: Path, out_dir: Path) -> None:
        cat = _make_catalog(tmp_path)
        cat.recently_added = ["9.9.9", "1.1.1"]  # 9.9.9 is unknown; 1.1.1 known
        M._write_atom_feed(cat, out_dir, reproducible=True)
        body = (out_dir / "feed.xml").read_text(encoding="utf-8")
        assert "UC-1.1.1" in body
        assert "UC-9.9.9" not in body

    def test_dedupes_repeated_recent_ids(self, tmp_path: Path, out_dir: Path) -> None:
        cat = _make_catalog(tmp_path)
        cat.recently_added = ["1.1.1", "1.1.1", "1.1.1"]
        M._write_atom_feed(cat, out_dir, reproducible=True)
        body = (out_dir / "feed.xml").read_text(encoding="utf-8")
        assert body.count("UC-1.1.1 CPU saturation") == 1

    def test_idempotent(self, catalog: Catalog, out_dir: Path) -> None:
        (out_dir / "feed.xml").write_text("PRESERVED", encoding="utf-8")
        M._write_atom_feed(catalog, out_dir, reproducible=True)
        assert (out_dir / "feed.xml").read_text(encoding="utf-8") == "PRESERVED"

    def test_non_reproducible_uses_now(
        self, catalog: Catalog, out_dir: Path
    ) -> None:
        before = datetime.now(timezone.utc)
        M._write_atom_feed(catalog, out_dir, reproducible=False)
        body = (out_dir / "feed.xml").read_text(encoding="utf-8")
        # Updated stamp is current — verify it's NOT the reproducible epoch.
        assert "1970-01-01T00:00:00Z" not in body
        # And matches the RFC 3339 format.
        assert "<updated>" in body and "Z</updated>" in body
        # Sanity: timestamp parseable and ≥ before timestamp.
        for line in body.splitlines():
            line = line.strip()
            if line.startswith("<updated>") and line.endswith("</updated>"):
                ts = line[len("<updated>"):-len("</updated>")]
                parsed = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(
                    tzinfo=timezone.utc
                )
                assert parsed >= before.replace(microsecond=0)
                break

    def test_atom_feed_caps_at_50_entries(
        self, tmp_path: Path, out_dir: Path
    ) -> None:
        cat = Catalog(project_root=tmp_path)
        # Build 60 UCs — feed must cap at 50.
        cat.files = ["cat-01-monitoring.md"]
        ucs = [{"i": f"1.1.{i}", "n": f"UC {i}"} for i in range(1, 61)]
        cat.categories = [
            {"i": 1, "n": "Monitoring", "s": [{"i": "1.1", "n": "X", "u": ucs}]}
        ]
        # No recently_added, so we exercise the fallback path's break.
        M._write_atom_feed(cat, out_dir, reproducible=True)
        body = (out_dir / "feed.xml").read_text(encoding="utf-8")
        assert body.count("<entry>") == 50

    def test_fallback_iter_skips_empty_ids_and_dupes(
        self, tmp_path: Path, out_dir: Path
    ) -> None:
        """Pin line 168 — fallback iter ``continue`` for empty / seen IDs."""
        cat = Catalog(project_root=tmp_path)
        cat.files = ["cat-01-monitoring.md"]
        # First UC has no ``i`` field (empty string), second is duplicated
        # under two subcategories. Both branches of line 167 fire.
        cat.categories = [
            {
                "i": 1,
                "n": "Monitoring",
                "s": [
                    {
                        "i": "1.1",
                        "n": "x",
                        "u": [
                            {"i": "", "n": "missing id"},
                            {"i": "1.1.1", "n": "First"},
                        ],
                    },
                    {
                        "i": "1.2",
                        "n": "y",
                        "u": [{"i": "1.1.1", "n": "Same id again"}],
                    },
                ],
            }
        ]
        # No recently_added → fallback iter is the only producer.
        M._write_atom_feed(cat, out_dir, reproducible=True)
        body = (out_dir / "feed.xml").read_text(encoding="utf-8")
        # Empty id contributes nothing; duplicate id surfaces only once.
        assert body.count("<entry>") == 1
        assert "UC-1.1.1" in body


# ---------------------------------------------------------------------------
# Sitemap urlset / sitemap-index helpers
# ---------------------------------------------------------------------------


class TestWriteUrlset:
    def test_writes_valid_urlset(self, tmp_path: Path) -> None:
        path = tmp_path / "out" / "sitemap-x.xml"
        M._write_urlset(path, ["https://x.test/a", "https://x.test/b"], lastmod="2026-05-20")
        body = path.read_text(encoding="utf-8")
        assert body.startswith('<?xml version="1.0" encoding="UTF-8"?>')
        # Both locs encoded as <url> entries with lastmod
        assert "<loc>https://x.test/a</loc><lastmod>2026-05-20</lastmod>" in body
        assert "<loc>https://x.test/b</loc><lastmod>2026-05-20</lastmod>" in body
        # XML parses cleanly
        ET.fromstring(body)

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        nested = tmp_path / "deep" / "nest" / "site.xml"
        M._write_urlset(nested, ["https://x.test/a"], lastmod="2026-05-20")
        assert nested.exists()


class TestWriteSitemapIndex:
    def test_writes_sitemapindex(self, tmp_path: Path) -> None:
        path = tmp_path / "sitemap.xml"
        M._write_sitemap_index(
            path, sitemaps=["sitemap-pages.xml", "sitemap-categories.xml"], lastmod="2026-05-20"
        )
        body = path.read_text(encoding="utf-8")
        assert "<sitemapindex" in body
        assert M.SITE_URL + "/sitemap-pages.xml" in body
        assert M.SITE_URL + "/sitemap-categories.xml" in body
        # XML parses cleanly
        ET.fromstring(body)


class TestWriteSitemap:
    def test_writes_full_sharded_sitemap(
        self, catalog: Catalog, out_dir: Path
    ) -> None:
        M._write_sitemap(catalog, out_dir, reproducible=True)
        # Per-section files exist
        assert (out_dir / "sitemap-pages.xml").exists()
        assert (out_dir / "sitemap-categories.xml").exists()
        assert (out_dir / "sitemap-regulations.xml").exists()
        # UC shards exist (at least one) and are referenced from index
        shards = list(out_dir.glob("sitemap-ucs-*.xml"))
        assert shards, "expected at least one UC shard"
        idx_body = (out_dir / "sitemap.xml").read_text(encoding="utf-8")
        for shard in shards:
            assert shard.name in idx_body

    def test_pages_sitemap_includes_landing_browse_regulation_api(
        self, catalog: Catalog, out_dir: Path
    ) -> None:
        M._write_sitemap(catalog, out_dir, reproducible=True)
        body = (out_dir / "sitemap-pages.xml").read_text(encoding="utf-8")
        for path in ("/", "/browse/", "/regulation/", "/api/"):
            assert f"<loc>{M.SITE_URL}{path}</loc>" in body

    def test_categories_use_filename_slug(
        self, catalog: Catalog, out_dir: Path
    ) -> None:
        M._write_sitemap(catalog, out_dir, reproducible=True)
        body = (out_dir / "sitemap-categories.xml").read_text(encoding="utf-8")
        # Slug from "cat-01-monitoring.md" is "monitoring"
        assert f"{M.SITE_URL}/category/monitoring/" in body
        assert f"{M.SITE_URL}/category/security/" in body

    def test_regulations_only_includes_matched(
        self, catalog: Catalog, out_dir: Path
    ) -> None:
        M._write_sitemap(catalog, out_dir, reproducible=True)
        body = (out_dir / "sitemap-regulations.xml").read_text(encoding="utf-8")
        # PCI DSS is referenced by UC-1.1.2 → must appear
        assert "/regulation/" in body and "pci-dss" in body

    def test_drops_unmatched_frameworks(self, tmp_path: Path, out_dir: Path) -> None:
        cat = _make_catalog(tmp_path)
        cat.regulations["zzz-unused"] = {
            "id": "zzz-unused",
            "shortName": "Unused",
            "name": "Unused Framework",
        }
        M._write_sitemap(cat, out_dir, reproducible=True)
        body = (out_dir / "sitemap-regulations.xml").read_text(encoding="utf-8")
        assert "zzz-unused" not in body

    def test_uc_shard_paginates_at_size_limit(
        self, tmp_path: Path, out_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Drop the shard size to 2 so 3 UCs split into 2 shards.
        monkeypatch.setattr(M, "_UC_SHARD_SIZE", 2)
        cat = _make_catalog(tmp_path)
        M._write_sitemap(cat, out_dir, reproducible=True)
        shards = sorted(out_dir.glob("sitemap-ucs-*.xml"))
        assert [s.name for s in shards] == [
            "sitemap-ucs-01.xml",
            "sitemap-ucs-02.xml",
        ]

    def test_clears_stale_uc_shards(
        self, catalog: Catalog, out_dir: Path
    ) -> None:
        # Leave a stale shard from a prior run.
        stale = out_dir / "sitemap-ucs-99.xml"
        stale.write_text("STALE", encoding="utf-8")
        M._write_sitemap(catalog, out_dir, reproducible=True)
        assert not stale.exists()

    def test_reproducible_sorts_loc_lists(
        self, tmp_path: Path, out_dir: Path
    ) -> None:
        # Build a catalog with categories whose declaration order would
        # NOT match alphabetical slug order, to verify reproducible
        # sorting kicks in.
        cat = Catalog(project_root=tmp_path)
        cat.files = [
            "cat-01-zzz-last.md",
            "cat-02-aaa-first.md",
        ]
        cat.categories = [
            {"i": 1, "n": "ZZZ", "s": [{"i": "1.1", "n": "x", "u": [{"i": "1.1.1"}]}]},
            {"i": 2, "n": "AAA", "s": [{"i": "2.1", "n": "y", "u": [{"i": "2.1.1"}]}]},
        ]
        M._write_sitemap(cat, out_dir, reproducible=True)
        body = (out_dir / "sitemap-categories.xml").read_text(encoding="utf-8")
        # Alphabetical: "aaa-first" appears before "zzz-last" once sorted
        idx_a = body.find("aaa-first")
        idx_z = body.find("zzz-last")
        assert 0 <= idx_a < idx_z

    def test_empty_uc_list_writes_no_shards(
        self, tmp_path: Path, out_dir: Path
    ) -> None:
        # Catalog with categories but no UCs at all.
        cat = Catalog(project_root=tmp_path)
        cat.files = ["cat-01-empty.md"]
        cat.categories = [{"i": 1, "n": "Empty", "s": []}]
        M._write_sitemap(cat, out_dir, reproducible=True)
        assert not list(out_dir.glob("sitemap-ucs-*.xml"))
        # Still emits the index, even if it has no UC shards.
        assert (out_dir / "sitemap.xml").exists()

    def test_skips_categories_without_id(
        self, tmp_path: Path, out_dir: Path
    ) -> None:
        """Pin line 241 — categories that lack the ``i`` key entirely are
        skipped. (A ``None`` value would break the sort key in
        ``_build_slug_map``; the realistic missing-id case is no key.)
        """
        cat = Catalog(project_root=tmp_path)
        cat.files = ["cat-01-monitoring.md"]
        cat.categories = [
            {"n": "Bogus — missing id key", "s": []},
            {"i": 1, "n": "Monitoring", "s": [{"i": "1.1", "n": "x", "u": [{"i": "1.1.1"}]}]},
        ]
        M._write_sitemap(cat, out_dir, reproducible=True)
        body = (out_dir / "sitemap-categories.xml").read_text(encoding="utf-8")
        assert "/category/monitoring/" in body
        # Only one <url> entry — the missing-id category dropped.
        assert body.count("<url>") == 1

    def test_skips_categories_without_slug(
        self, tmp_path: Path, out_dir: Path
    ) -> None:
        """Pin line 244 — categories whose slug map returns empty are skipped.

        Inject a slug map override via monkeypatch on
        ``_render_pages._build_slug_map`` so that one category
        deliberately gets an empty slug, exercising the
        ``if not slug: continue`` branch.
        """
        cat = Catalog(project_root=tmp_path)
        cat.files = ["cat-07-hidden.md", "cat-08-visible.md"]
        cat.categories = [
            {"i": 7, "n": "Hidden", "s": [{"i": "7.1", "n": "x", "u": [{"i": "7.1.1"}]}]},
            {"i": 8, "n": "Visible", "s": [{"i": "8.1", "n": "y", "u": [{"i": "8.1.1"}]}]},
        ]
        # Patch the slug map producer to deliberately omit cat 7.
        original_builder = M._render_pages._build_slug_map
        try:
            M._render_pages._build_slug_map = lambda catalog: {7: "", 8: "visible"}
            M._write_sitemap(cat, out_dir, reproducible=True)
        finally:
            M._render_pages._build_slug_map = original_builder

        body = (out_dir / "sitemap-categories.xml").read_text(encoding="utf-8")
        assert "/category/visible/" in body
        # Only one <url> emitted — empty-slug category was skipped.
        assert body.count("<url>") == 1

    def test_unresolved_regs_tag_does_not_match(
        self, tmp_path: Path, out_dir: Path
    ) -> None:
        """Pin branch 251->249 — a ``regs`` tag that doesn't resolve to any
        framework must NOT be added to ``matched_fw_ids``.
        """
        cat = _make_catalog(tmp_path)
        # UC tagged with a regulation that has no alias entry.
        cat.categories[0]["s"][0]["u"][0]["regs"] = ["nonexistent-framework"]
        M._write_sitemap(cat, out_dir, reproducible=True)
        body = (out_dir / "sitemap-regulations.xml").read_text(encoding="utf-8")
        # Only the existing pci-dss UC contributes; nonexistent does not.
        assert "nonexistent-framework" not in body

    def test_skips_uc_without_id(self, tmp_path: Path, out_dir: Path) -> None:
        """Pin branch 263->261 — UC entries without ``i`` produce no shard locs."""
        cat = Catalog(project_root=tmp_path)
        cat.files = ["cat-01-monitoring.md"]
        cat.categories = [
            {
                "i": 1,
                "n": "Monitoring",
                "s": [
                    {
                        "i": "1.1",
                        "n": "x",
                        "u": [
                            {"i": "", "n": "no id"},
                            {"i": "1.1.1", "n": "real"},
                        ],
                    }
                ],
            }
        ]
        M._write_sitemap(cat, out_dir, reproducible=True)
        shard = next(iter(out_dir.glob("sitemap-ucs-*.xml")))
        body = shard.read_text(encoding="utf-8")
        # Only the well-formed UC made it into the shard.
        assert body.count("<url>") == 1
        assert "UC-1.1.1" in body


# ---------------------------------------------------------------------------
# manifest.json
# ---------------------------------------------------------------------------


class TestWriteMachineManifest:
    def test_writes_valid_json(self, catalog: Catalog, out_dir: Path) -> None:
        M._write_machine_manifest(catalog, out_dir, reproducible=True)
        payload = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
        assert payload["site"] == M.SITE_URL
        assert payload["version"] == "2.0.0"
        # Stats roll up from the catalog
        assert payload["stats"]["useCases"] == 3
        assert payload["stats"]["categories"] == 2
        assert payload["stats"]["regulations"] == 1
        assert payload["stats"]["totalRegulations"] == 1

    def test_endpoints_use_site_url(
        self, catalog: Catalog, out_dir: Path
    ) -> None:
        M._write_machine_manifest(catalog, out_dir, reproducible=True)
        payload = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
        for url in payload["endpoints"].values():
            assert url.startswith(M.SITE_URL)

    def test_categories_carry_html_and_json_twins(
        self, catalog: Catalog, out_dir: Path
    ) -> None:
        M._write_machine_manifest(catalog, out_dir, reproducible=True)
        payload = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
        cats = payload["categories"]
        assert len(cats) == 2
        for c in cats:
            assert c["html"].startswith(M.SITE_URL + "/category/")
            assert c["json"].endswith("/index.json")
            assert isinstance(c["useCases"], int)

    def test_only_lists_matched_regulations(
        self, tmp_path: Path, out_dir: Path
    ) -> None:
        cat = _make_catalog(tmp_path)
        # Add an unmatched framework — must not surface in manifest.
        cat.regulations["zzz"] = {
            "id": "zzz",
            "shortName": "Z",
            "name": "Zeta",
        }
        M._write_machine_manifest(cat, out_dir, reproducible=True)
        payload = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
        ids = [r["id"] for r in payload["regulations"]]
        assert ids == ["pci-dss"]
        # totalRegulations counts ALL frameworks; matched only the tagged one.
        assert payload["stats"]["totalRegulations"] == 2
        assert payload["stats"]["regulations"] == 1

    def test_overwrites_existing_manifest(
        self, catalog: Catalog, out_dir: Path
    ) -> None:
        (out_dir / "manifest.json").write_text("{}", encoding="utf-8")
        M._write_machine_manifest(catalog, out_dir, reproducible=True)
        payload = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
        # Confirm the manifest was rewritten (not preserved).
        assert payload["version"] == "2.0.0"

    def test_unresolved_regs_skip_in_manifest(
        self, tmp_path: Path, out_dir: Path
    ) -> None:
        """Pin branch 354->352 — a ``regs`` tag that resolves to no framework
        is not added to ``matched_fw_ids`` in the machine manifest either.
        """
        cat = _make_catalog(tmp_path)
        # Add an unresolvable tag — must not surface as a regulation.
        cat.categories[0]["s"][0]["u"][0]["regs"] = ["pci-dss", "nonexistent"]
        M._write_machine_manifest(cat, out_dir, reproducible=True)
        payload = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
        ids = [r["id"] for r in payload["regulations"]]
        # Only the resolvable framework appears.
        assert ids == ["pci-dss"]


# ---------------------------------------------------------------------------
# OpenAPI v2
# ---------------------------------------------------------------------------


class TestWriteOpenApiV2:
    def test_writes_yaml_with_substituted_counts(
        self, catalog: Catalog, out_dir: Path
    ) -> None:
        M._write_openapi_v2(catalog, out_dir, reproducible=True)
        spec_path = out_dir / "api" / "v2" / "openapi.yaml"
        assert spec_path.exists()
        spec = spec_path.read_text(encoding="utf-8")
        assert "openapi: 3.1.0" in spec
        assert "{site_url}" not in spec  # template substituted
        # Substituted counts appear verbatim in the description block
        assert "Catalogue: 3 use cases, 2 categories" in spec
        assert "1 regulatory frameworks" in spec
        # SITE_URL appears as a server entry
        assert M.SITE_URL in spec

    def test_creates_nested_api_dir(
        self, catalog: Catalog, out_dir: Path
    ) -> None:
        # Sanity: api/v2/ should be created lazily.
        M._write_openapi_v2(catalog, out_dir, reproducible=True)
        assert (out_dir / "api" / "v2").is_dir()


# ---------------------------------------------------------------------------
# Timestamp helpers
# ---------------------------------------------------------------------------


class TestTimestampHelpers:
    def test_reproducible_uses_source_date_epoch(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Friday, Jan 01, 2027 00:00:00 UTC == epoch 1798761600
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1798761600")
        ts = M._timestamp(reproducible=True)
        assert ts == "2027-01-01T00:00:00Z"

    def test_reproducible_falls_back_to_zero_on_unset_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
        ts = M._timestamp(reproducible=True)
        assert ts == "1970-01-01T00:00:00Z"

    def test_reproducible_falls_back_to_zero_on_invalid_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "not-a-number")
        ts = M._timestamp(reproducible=True)
        assert ts == "1970-01-01T00:00:00Z"

    def test_non_reproducible_returns_current_time(self) -> None:
        before = datetime.now(timezone.utc)
        ts = M._timestamp(reproducible=False)
        parsed = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        # Within a couple of seconds.
        delta = parsed - before
        assert abs(delta.total_seconds()) < 5

    def test_date_only_returns_first_10_chars(self) -> None:
        d = M._date_only(reproducible=True)
        assert len(d) == 10
        # Confirm it's a valid YYYY-MM-DD prefix
        datetime.strptime(d, "%Y-%m-%d")


# ---------------------------------------------------------------------------
# render() — orchestrator
# ---------------------------------------------------------------------------


class TestRenderOrchestrator:
    def test_render_emits_full_surface(
        self, catalog: Catalog, out_dir: Path
    ) -> None:
        M.render(catalog, out_dir, reproducible=True)
        # Every file the discovery surface promises must land on disk.
        expected = [
            "robots.txt",
            "manifest.webmanifest",
            ".well-known/security.txt",
            ".well-known/ai.txt",
            "feed.xml",
            "sitemap.xml",
            "sitemap-pages.xml",
            "sitemap-categories.xml",
            "sitemap-regulations.xml",
            "manifest.json",
            "api/v2/openapi.yaml",
        ]
        for rel in expected:
            assert (out_dir / rel).exists(), f"missing {rel}"

    def test_render_idempotent_on_existing_static_files(
        self, catalog: Catalog, out_dir: Path
    ) -> None:
        # First render — captures baseline.
        M.render(catalog, out_dir, reproducible=True)
        before = (out_dir / "robots.txt").read_text(encoding="utf-8")
        # Second render — robots.txt is idempotent (skip when present).
        # Atom feed is also idempotent. Sitemap + manifest are unconditional.
        M.render(catalog, out_dir, reproducible=True)
        after = (out_dir / "robots.txt").read_text(encoding="utf-8")
        assert before == after

    def test_render_default_non_reproducible(
        self, catalog: Catalog, out_dir: Path
    ) -> None:
        # Default kwarg — exercise the path without raising.
        M.render(catalog, out_dir)
        assert (out_dir / "manifest.json").exists()
