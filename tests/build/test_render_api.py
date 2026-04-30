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

    def test_normalise_cat_meta_strips_empty(self):
        assert render_api._normalise_cat_meta({"1": {"a": 1, "b": "", "c": None}}) == {
            "1": {"a": 1}
        }

    def test_sorted_unique(self):
        assert render_api._sorted_unique(["3.2.1", "3.2.1", "3.2.10"]) == ["3.2.1", "3.2.10"]

    def test_trim_sapp(self):
        slim = render_api._trim_sapp(
            [{"id": "x", "name": "N", "url": "u", "predecessor": [{"id": "p", "desc": "d"}]}]
        )
        assert slim == [{"id": "x", "name": "N", "predecessor": [{"id": "p"}]}]

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
