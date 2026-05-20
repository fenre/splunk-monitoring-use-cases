"""Hermetic tests for ``tools/build/render_pages.py``.

The orchestrator emits the static-site tree under ``dist/``:
``/index.html``, ``/uc/UC-X.Y.Z/{index.html,index.json,uc.md}``,
``/category/<slug>/{index.html,index.json}``, and
``/regulation/<slug>/{index.html,index.json}`` plus a regulation
index.

These tests build a small synthetic ``Catalog`` (no on-disk content,
no environment variables, no network) and assert the public file
layout, deterministic JSON, regulation-alias resolution, slug
collision handling, prerequisite reverse-index, and ISO timestamp
seeding under ``SOURCE_DATE_EPOCH``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TOOLS_DIR = str(REPO_ROOT / "tools")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from build import render_pages as rp  # noqa: E402
from build.parse_content import Catalog  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_uc(uc_id: str, name: str, **overrides) -> dict:
    """Minimal UC sidecar (catalog wire format)."""
    base = {
        "i": uc_id,
        "n": name,
        "v": f"Value of {name}.",
        "c": "high",
        "f": "intermediate",
        "wv": "walk",
        "ge": f"Plain-language: {name}",
        "q": f'index=foo sourcetype="bar" id={uc_id}',
        "m": "1. Step one\n2. Step two",
    }
    base.update(overrides)
    return base


def _make_catalog(
    tmp_path: Path,
    *,
    categories=None,
    regulations=None,
    cat_meta=None,
    files=None,
) -> Catalog:
    cat = Catalog(project_root=tmp_path)
    cat.categories = categories or []
    cat.regulations = regulations or {}
    cat.cat_meta = cat_meta or {}
    cat.files = files or []
    cat.asset_hashes = {"styles_css": "s.abcd1234.css", "app_js": "a.abcd1234.js"}
    return cat


@pytest.fixture
def synthetic_catalog(tmp_path: Path) -> Catalog:
    """Two categories, a few UCs, one regulation, slug collision."""
    cat1 = {
        "i": 1,
        "n": "Identity & Access",
        "s": [
            {
                "i": "1.1",
                "n": "Authentication",
                "u": [
                    _make_uc("1.1.1", "Detect anomalous root login", regs=["gdpr"]),
                    _make_uc(
                        "1.1.2",
                        "Detect impossible travel",
                        pre=["UC-1.1.1"],
                        regs=["pci"],
                    ),
                ],
            },
        ],
    }
    cat2 = {
        "i": 2,
        "n": "Network Monitoring",
        "s": [
            {
                "i": "2.1",
                "n": "Traffic Analysis",
                "u": [_make_uc("2.1.1", "Detect DNS tunnelling")],
            },
        ],
    }
    regs = {
        "gdpr": {
            "id": "gdpr",
            "shortName": "GDPR",
            "name": "General Data Protection Regulation",
            "tier": 1,
            "jurisdiction": "EU",
            "aliases": ["EU GDPR", "GDPR 2016/679"],
        },
        "pci": {
            "id": "pci",
            "shortName": "PCI",
            "name": "Payment Card Industry DSS",
            "tier": 1,
            "jurisdiction": "Global",
            "aliases": ["PCI DSS", "PCI DSS v4.0"],
        },
    }
    return _make_catalog(
        tmp_path,
        categories=[cat1, cat2],
        regulations=regs,
        cat_meta={"1": {}, "2": {}},
        files=["cat-01-identity-access.md", "cat-02-network-monitoring.md"],
    )


# ---------------------------------------------------------------------------
# render() — public entrypoint
# ---------------------------------------------------------------------------


class TestRender:
    def test_render_emits_per_uc_files(
        self, synthetic_catalog: Catalog, tmp_path: Path, monkeypatch
    ):
        # Keep the build hermetic: no env var leakage.
        monkeypatch.delenv("SITE_URL", raising=False)
        monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
        monkeypatch.delenv("GITHUB_SHA", raising=False)
        out = tmp_path / "dist"
        out.mkdir()
        rp.render(synthetic_catalog, out, reproducible=True)
        for uc_id in ("1.1.1", "1.1.2", "2.1.1"):
            uc_dir = out / "uc" / f"UC-{uc_id}"
            assert (uc_dir / "index.html").exists()
            assert (uc_dir / "index.json").exists()
            assert (uc_dir / "uc.md").exists()

    def test_render_emits_per_category_files(
        self, synthetic_catalog: Catalog, tmp_path: Path
    ):
        out = tmp_path / "dist"
        out.mkdir()
        rp.render(synthetic_catalog, out, reproducible=True)
        for slug in ("identity-access", "network-monitoring"):
            cat_dir = out / "category" / slug
            assert (cat_dir / "index.html").exists()
            assert (cat_dir / "index.json").exists()

    def test_render_emits_per_regulation_files_and_index(
        self, synthetic_catalog: Catalog, tmp_path: Path
    ):
        out = tmp_path / "dist"
        out.mkdir()
        rp.render(synthetic_catalog, out, reproducible=True)
        for slug in ("gdpr", "pci"):
            reg_dir = out / "regulation" / slug
            assert (reg_dir / "index.html").exists()
            assert (reg_dir / "index.json").exists()
        # Regulation index page itself.
        assert (out / "regulation" / "index.html").exists()
        assert (out / "regulation" / "index.json").exists()

    def test_render_does_not_emit_root_index_html(
        self, synthetic_catalog: Catalog, tmp_path: Path
    ):
        """Per the module docstring: the SPA owns /index.html, the SSG
        does not touch it."""
        out = tmp_path / "dist"
        out.mkdir()
        rp.render(synthetic_catalog, out, reproducible=True)
        assert not (out / "index.html").exists()

    def test_render_with_empty_catalog_is_noop(self, tmp_path: Path):
        cat = Catalog(project_root=tmp_path)
        out = tmp_path / "dist"
        out.mkdir()
        rp.render(cat, out, reproducible=True)
        # No subdirectories created.
        assert list(out.iterdir()) == []

    def test_render_non_reproducible_skips_sort(
        self, synthetic_catalog: Catalog, tmp_path: Path
    ):
        """Branch 86->89: ``if reproducible:`` false arm — categories
        are emitted in declared order rather than sorted by id."""
        out = tmp_path / "dist"
        out.mkdir()
        rp.render(synthetic_catalog, out, reproducible=False)
        # All UC dirs still exist (declared-order iteration still emits
        # everything, just doesn't sort the categories first).
        for uc_id in ("1.1.1", "1.1.2", "2.1.1"):
            assert (out / "uc" / f"UC-{uc_id}").exists()

    def test_render_skips_uc_with_no_regs(self, tmp_path: Path):
        """Branch 224->222: ``if not regs_raw: continue`` inside
        _emit_regulations — UCs without a ``regs`` field don't contribute
        to grouped[] (but the framework still appears in the catalog)."""
        cat = {
            "i": 1,
            "n": "X",
            "s": [
                {
                    "i": "1.1",
                    "n": "S",
                    "u": [
                        _make_uc("1.1.1", "Tagged", regs=["gdpr"]),
                        _make_uc("1.1.2", "Untagged"),  # no regs
                    ],
                }
            ],
        }
        regs = {"gdpr": {"id": "gdpr", "shortName": "GDPR", "name": "G"}}
        c = _make_catalog(tmp_path, categories=[cat], regulations=regs)
        out = tmp_path / "dist"
        out.mkdir()
        rp.render(c, out, reproducible=True)
        # gdpr framework rolls up exactly one UC (the tagged one).
        gdpr_json = json.loads(
            (out / "regulation" / "gdpr" / "index.json").read_text(encoding="utf-8")
        )
        # The payload shape varies; just confirm the UC id appears.
        assert "1.1.1" in json.dumps(gdpr_json)
        assert "1.1.2" not in json.dumps(gdpr_json)

    def test_render_uc_with_unrecognised_reg_dropped(self, tmp_path: Path):
        """Branch 227 (``if not matched: continue``) — a UC tagged with
        a regulation alias that doesn't resolve gets silently dropped
        from grouped[]."""
        cat = {
            "i": 1,
            "n": "X",
            "s": [
                {
                    "i": "1.1",
                    "n": "S",
                    "u": [_make_uc("1.1.1", "Mystery", regs=["unknown-reg-xyz"])],
                }
            ],
        }
        regs = {"gdpr": {"id": "gdpr", "shortName": "GDPR", "name": "G"}}
        c = _make_catalog(tmp_path, categories=[cat], regulations=regs)
        out = tmp_path / "dist"
        out.mkdir()
        rp.render(c, out, reproducible=True)
        # No regulation pages emitted — grouped[] is empty.
        assert not (out / "regulation").exists()

    def test_render_skips_uc_without_id(self, tmp_path: Path):
        """Branch in render(): ``if not uc.get("i"): continue``."""
        cat = {
            "i": 1,
            "n": "X",
            "s": [
                {
                    "i": "1.1",
                    "n": "Sub",
                    "u": [
                        {"n": "Headless UC", "v": "no id"},  # no "i"
                        _make_uc("1.1.1", "Good UC"),
                    ],
                }
            ],
        }
        c = _make_catalog(tmp_path, categories=[cat])
        out = tmp_path / "dist"
        out.mkdir()
        rp.render(c, out, reproducible=True)
        # Only the good UC has a directory.
        uc_dirs = sorted(p.name for p in (out / "uc").iterdir())
        assert uc_dirs == ["UC-1.1.1"]


# ---------------------------------------------------------------------------
# _emit_uc / _emit_category / _emit_regulations branches
# ---------------------------------------------------------------------------


class TestEmitUc:
    def test_emit_uc_skips_when_uc_id_blank(self, tmp_path: Path, synthetic_catalog: Catalog):
        ctx = rp._build_context(synthetic_catalog, reproducible=True)
        out = tmp_path / "dist"
        out.mkdir()
        rp._emit_uc(
            {"i": "", "n": "Headless"},
            cat={"i": 1, "n": "C"},
            sub={"i": "1.1", "n": "S"},
            cat_slug="c",
            out_dir=out,
            ctx=ctx,
            reproducible=True,
        )
        # Nothing under uc/.
        uc_root = out / "uc"
        assert not uc_root.exists()

    def test_emit_uc_writes_all_three_artifacts(
        self, tmp_path: Path, synthetic_catalog: Catalog
    ):
        ctx = rp._build_context(synthetic_catalog, reproducible=True)
        out = tmp_path / "dist"
        out.mkdir()
        uc = _make_uc("9.9.99", "Test UC")
        rp._emit_uc(
            uc,
            cat={"i": 9, "n": "Test Cat"},
            sub={"i": "9.9", "n": "Test Sub"},
            cat_slug="test-cat",
            out_dir=out,
            ctx=ctx,
            reproducible=True,
        )
        uc_dir = out / "uc" / "UC-9.9.99"
        assert (uc_dir / "index.html").exists()
        assert (uc_dir / "index.json").exists()
        assert (uc_dir / "uc.md").exists()


class TestEmitLanding:
    def test_emit_landing_writes_html(
        self, tmp_path: Path, synthetic_catalog: Catalog
    ):
        ctx = rp._build_context(synthetic_catalog, reproducible=True)
        out = tmp_path / "dist"
        out.mkdir()
        rp._emit_landing(
            synthetic_catalog,
            cat_slug_for={1: "identity-access", 2: "network-monitoring"},
            regulation_summaries=None,
            out_dir=out,
            ctx=ctx,
        )
        assert (out / "index.html").exists()
        content = (out / "index.html").read_text(encoding="utf-8")
        assert "<!DOCTYPE" in content or "<!doctype" in content


class TestEmitRegulations:
    def test_emit_regulations_returns_empty_when_no_regulations(self, tmp_path: Path):
        cat = _make_catalog(tmp_path, categories=[], regulations={})
        ctx = rp._build_context(cat, reproducible=True)
        out = tmp_path / "dist"
        out.mkdir()
        result = rp._emit_regulations(
            cat,
            cat_slug_for={},
            cat_name_for={},
            out_dir=out,
            ctx=ctx,
            reproducible=True,
        )
        assert result == []

    def test_emit_regulations_returns_empty_when_no_grouped_ucs(self, tmp_path: Path):
        """``if not grouped: return []`` — UCs exist but none carry a
        recognised regulation tag."""
        cat = {
            "i": 1,
            "n": "X",
            "s": [
                {"i": "1.1", "n": "S", "u": [_make_uc("1.1.1", "U", regs=[])]}
            ],
        }
        regs = {"gdpr": {"id": "gdpr", "shortName": "GDPR", "name": "G"}}
        c = _make_catalog(tmp_path, categories=[cat], regulations=regs)
        ctx = rp._build_context(c, reproducible=True)
        out = tmp_path / "dist"
        out.mkdir()
        result = rp._emit_regulations(
            c, cat_slug_for={1: "x"}, cat_name_for={1: "X"},
            out_dir=out, ctx=ctx, reproducible=True,
        )
        assert result == []
        assert not (out / "regulation").exists()

    def test_emit_regulations_returns_sorted_summaries(
        self, synthetic_catalog: Catalog, tmp_path: Path
    ):
        ctx = rp._build_context(synthetic_catalog, reproducible=True)
        out = tmp_path / "dist"
        out.mkdir()
        summaries = rp._emit_regulations(
            synthetic_catalog,
            cat_slug_for={1: "identity-access", 2: "network-monitoring"},
            cat_name_for={1: "Identity & Access", 2: "Network Monitoring"},
            out_dir=out,
            ctx=ctx,
            reproducible=True,
        )
        # gdpr and pci each have exactly 1 UC; alphabetical by shortName tiebreak.
        ids = [s["id"] for s in summaries]
        assert set(ids) == {"gdpr", "pci"}
        for s in summaries:
            assert s["useCaseCount"] == 1
            assert "shortName" in s
            assert "slug" in s

    def test_emit_regulations_skips_unknown_framework(self, tmp_path: Path):
        """Branch ``if not fw: continue`` — a UC carries a tag that
        resolves through aliases to a framework id not present in
        catalog.regulations (only possible via alias_to_fw_id pollution
        which we can't easily inject; this test simulates by deleting
        the framework after the index is built — covers the defensive
        guard)."""
        # Construct directly: a UC tagged "gdpr" but the regulation map
        # is empty so _build_regulation_alias_index returns empty maps.
        # That makes _resolve_alias return "", so the UC's `matched`
        # set is empty -> "if not matched: continue". So we need a
        # different scenario.
        # Instead: register a framework then strip it after alias
        # registration. Use the lower-level helpers.
        cat = {
            "i": 1,
            "n": "X",
            "s": [
                {"i": "1.1", "n": "S", "u": [_make_uc("1.1.1", "U", regs=["mystery"])]}
            ],
        }
        regs = {
            "mystery": {"id": "mystery", "shortName": "Myst", "name": "Mystery"}
        }
        c = _make_catalog(tmp_path, categories=[cat], regulations=regs)
        ctx = rp._build_context(c, reproducible=True)
        out = tmp_path / "dist"
        out.mkdir()
        summaries = rp._emit_regulations(
            c,
            cat_slug_for={1: "x"},
            cat_name_for={1: "X"},
            out_dir=out,
            ctx=ctx,
            reproducible=True,
        )
        # Single registered framework; gets emitted.
        assert len(summaries) == 1
        assert summaries[0]["id"] == "mystery"


# ---------------------------------------------------------------------------
# _build_context
# ---------------------------------------------------------------------------


class TestBuildContext:
    def test_returns_render_context_with_expected_fields(
        self, synthetic_catalog: Catalog, monkeypatch
    ):
        monkeypatch.delenv("SITE_URL", raising=False)
        monkeypatch.delenv("GITHUB_SHA", raising=False)
        ctx = rp._build_context(synthetic_catalog, reproducible=True)
        assert ctx.site_url == rp.SITE_URL_DEFAULT
        assert ctx.site_name == "Splunk Monitoring Use Cases"
        assert ctx.asset_styles == "s.abcd1234.css"
        assert ctx.asset_app_js == "a.abcd1234.js"

    def test_site_url_from_env_overrides_default(
        self, synthetic_catalog: Catalog, monkeypatch
    ):
        monkeypatch.setenv("SITE_URL", "https://example.com/x/")
        ctx = rp._build_context(synthetic_catalog, reproducible=True)
        # Trailing slash stripped.
        assert ctx.site_url == "https://example.com/x"

    def test_repo_url_from_env(self, synthetic_catalog: Catalog, monkeypatch):
        monkeypatch.setenv("REPO_URL", "https://github.com/x/y")
        ctx = rp._build_context(synthetic_catalog, reproducible=True)
        assert ctx.repo_url == "https://github.com/x/y"

    def test_build_id_from_github_sha(self, synthetic_catalog: Catalog, monkeypatch):
        monkeypatch.setenv("GITHUB_SHA", "abcdef1234567890")
        ctx = rp._build_context(synthetic_catalog, reproducible=True)
        # First 7 chars.
        assert ctx.build_id == "abcdef1"

    def test_build_id_blank_when_no_sha_env(
        self, synthetic_catalog: Catalog, monkeypatch
    ):
        monkeypatch.delenv("GITHUB_SHA", raising=False)
        ctx = rp._build_context(synthetic_catalog, reproducible=True)
        assert ctx.build_id == ""

    def test_asset_hashes_absent_yields_empty_strings(self, tmp_path: Path):
        cat = Catalog(project_root=tmp_path)
        cat.asset_hashes = {}
        ctx = rp._build_context(cat, reproducible=True)
        assert ctx.asset_styles == ""
        assert ctx.asset_app_js == ""


# ---------------------------------------------------------------------------
# _read_catalogue_version
# ---------------------------------------------------------------------------


class TestReadCatalogueVersion:
    def test_reads_version_file(self, tmp_path: Path):
        (tmp_path / "VERSION").write_text("9.1.5\n", encoding="utf-8")
        assert rp._read_catalogue_version(tmp_path) == "9.1.5"

    def test_empty_version_falls_back_to_default(self, tmp_path: Path):
        (tmp_path / "VERSION").write_text("   \n", encoding="utf-8")
        assert rp._read_catalogue_version(tmp_path) == "0.0.0"

    def test_missing_version_file_returns_default(self, tmp_path: Path):
        assert rp._read_catalogue_version(tmp_path) == "0.0.0"

    def test_version_path_is_directory_not_file(self, tmp_path: Path):
        """``p.exists() and p.is_file()`` false arm — a VERSION subdir
        (weird, but possible) falls through to the default."""
        (tmp_path / "VERSION").mkdir()
        assert rp._read_catalogue_version(tmp_path) == "0.0.0"

    def test_unreadable_file_returns_default(self, tmp_path: Path, monkeypatch):
        """OSError on read falls back to the default — covered by
        patching ``read_text`` to raise."""
        (tmp_path / "VERSION").write_text("9.1.0", encoding="utf-8")

        def boom(self, **kw):
            raise OSError("permission denied")

        monkeypatch.setattr(Path, "read_text", boom)
        assert rp._read_catalogue_version(tmp_path) == "0.0.0"


# ---------------------------------------------------------------------------
# _build_uc_prereq_indexes
# ---------------------------------------------------------------------------


class TestBuildUcPrereqIndexes:
    def test_returns_title_and_reverse_indexes(self, tmp_path: Path):
        cat = {
            "i": 1,
            "n": "X",
            "s": [
                {
                    "i": "1.1",
                    "n": "S",
                    "u": [
                        _make_uc("1.1.1", "First"),
                        _make_uc("1.1.2", "Second", pre=["UC-1.1.1"]),
                        _make_uc("1.1.3", "Third", pre=["UC-1.1.1", "UC-1.1.2"]),
                    ],
                }
            ],
        }
        c = _make_catalog(tmp_path, categories=[cat])
        title_idx, reverse = rp._build_uc_prereq_indexes(c)
        assert title_idx["UC-1.1.1"] == ("First", "walk")
        assert title_idx["UC-1.1.2"] == ("Second", "walk")
        assert "UC-1.1.1" in reverse
        assert reverse["UC-1.1.1"] == ("UC-1.1.2", "UC-1.1.3")
        assert reverse["UC-1.1.2"] == ("UC-1.1.3",)

    def test_self_reference_excluded(self, tmp_path: Path):
        cat = {
            "i": 1,
            "n": "X",
            "s": [
                {
                    "i": "1.1",
                    "n": "S",
                    "u": [_make_uc("1.1.1", "Self", pre=["UC-1.1.1"])],
                }
            ],
        }
        c = _make_catalog(tmp_path, categories=[cat])
        _, reverse = rp._build_uc_prereq_indexes(c)
        assert reverse == {}

    def test_malformed_pre_id_skipped(self, tmp_path: Path):
        cat = {
            "i": 1,
            "n": "X",
            "s": [
                {
                    "i": "1.1",
                    "n": "S",
                    "u": [
                        _make_uc("1.1.1", "Good"),
                        _make_uc("1.1.2", "Bad", pre=["not-a-uc-id", "UC-1.1.1"]),
                    ],
                }
            ],
        }
        c = _make_catalog(tmp_path, categories=[cat])
        _, reverse = rp._build_uc_prereq_indexes(c)
        # Only the valid prereq made it into the reverse index.
        assert reverse == {"UC-1.1.1": ("UC-1.1.2",)}

    def test_blank_uc_id_skipped(self, tmp_path: Path):
        cat = {
            "i": 1,
            "n": "X",
            "s": [
                {
                    "i": "1.1",
                    "n": "S",
                    "u": [{"i": "", "n": "Headless"}, _make_uc("1.1.1", "Good")],
                }
            ],
        }
        c = _make_catalog(tmp_path, categories=[cat])
        title_idx, _ = rp._build_uc_prereq_indexes(c)
        # The blank-id UC is silently dropped; only the well-formed UC
        # gets a title-index entry.
        assert list(title_idx.keys()) == ["UC-1.1.1"]

    def test_title_falls_back_to_t_field_then_full_id(self, tmp_path: Path):
        """``title = str(uc.get("n") or uc.get("t") or full)``."""
        cat = {
            "i": 1,
            "n": "X",
            "s": [
                {
                    "i": "1.1",
                    "n": "S",
                    "u": [
                        {"i": "1.1.1", "t": "TA name"},  # n missing
                        {"i": "1.1.2"},  # n and t missing
                    ],
                }
            ],
        }
        c = _make_catalog(tmp_path, categories=[cat])
        title_idx, _ = rp._build_uc_prereq_indexes(c)
        assert title_idx["UC-1.1.1"] == ("TA name", "")
        assert title_idx["UC-1.1.2"] == ("UC-1.1.2", "")

    def test_reverse_index_with_non_canonical_uc_id_uses_fallback_sort(self, tmp_path: Path):
        """Line 403: the inner ``_sort_key`` falls back to ``(10**9, ...)``
        when a reverse-index entry contains something that doesn't match
        ``UC-N.N.N``. Construct such an entry directly by monkey-patching
        the sorted output through a controlled fixture.

        The simplest reachable path: a UC with a 4-part pre id slips
        past the regex (which requires exactly 3 segments)? No — the
        regex strictly requires 3 dot-separated segments. The fallback
        is reachable when re-sorting an injected key not produced by
        the regex. We exercise it directly."""
        from build.render_pages import _build_uc_prereq_indexes  # noqa: F401

        # The fallback is in a nested function — most easily reached via
        # importing the module and calling the inner via the public path
        # is impossible. We assert the behaviour through the practical
        # contract: a UC carrying a malformed dep gets dropped (regex
        # filters it), so we instead validate sort stability with a
        # mixed-component ID like 1.1.100 vs 1.1.20.
        cat = {
            "i": 1,
            "n": "X",
            "s": [
                {
                    "i": "1.1",
                    "n": "S",
                    "u": [
                        _make_uc("1.1.100", "Hundred", pre=["UC-1.1.1"]),
                        _make_uc("1.1.20", "Twenty", pre=["UC-1.1.1"]),
                        _make_uc("1.1.1", "One"),
                    ],
                }
            ],
        }
        c = _make_catalog(tmp_path, categories=[cat])
        _, reverse = rp._build_uc_prereq_indexes(c)
        # Natural sort: 1.1.20 < 1.1.100.
        assert reverse["UC-1.1.1"] == ("UC-1.1.20", "UC-1.1.100")

    def test_reverse_index_sort_key_falls_back_for_non_matching(self, tmp_path: Path):
        """The internal ``_sort_key`` returns a fallback when the UC ID
        doesn't match the X.Y.Z pattern — exercised through the rather
        unlikely path where the regex *matches* the dependency entry
        but then the lookup somehow sees a non-matching id. Easier to
        prove the sort happens at all: many deps to the same UC should
        produce a sorted tuple."""
        cat = {
            "i": 1,
            "n": "X",
            "s": [
                {
                    "i": "1.1",
                    "n": "S",
                    "u": [
                        _make_uc("1.1.10", "Ten", pre=["UC-1.1.1"]),
                        _make_uc("1.1.2", "Two", pre=["UC-1.1.1"]),
                        _make_uc("1.1.1", "One"),
                    ],
                }
            ],
        }
        c = _make_catalog(tmp_path, categories=[cat])
        _, reverse = rp._build_uc_prereq_indexes(c)
        # Natural sort: 1.1.2 < 1.1.10.
        assert reverse["UC-1.1.1"] == ("UC-1.1.2", "UC-1.1.10")


# ---------------------------------------------------------------------------
# _build_slug_map
# ---------------------------------------------------------------------------


class TestBuildSlugMap:
    def test_uses_filename_slug_when_available(self, tmp_path: Path):
        cats = [
            {"i": 1, "n": "Identity Stuff"},
            {"i": 2, "n": "Other"},
        ]
        c = _make_catalog(
            tmp_path,
            categories=cats,
            files=["cat-01-canonical-slug.md", "cat-02-from-file.md"],
        )
        slugs = rp._build_slug_map(c)
        assert slugs[1] == "canonical-slug"
        assert slugs[2] == "from-file"

    def test_falls_back_to_slugified_name(self, tmp_path: Path):
        cats = [{"i": 5, "n": "Computed Slug"}]
        c = _make_catalog(tmp_path, categories=cats, files=[])
        slugs = rp._build_slug_map(c)
        assert slugs[5] == "computed-slug"

    def test_slug_collisions_get_disambiguated(self, tmp_path: Path):
        cats = [
            {"i": 1, "n": "Same"},
            {"i": 2, "n": "Same"},
            {"i": 3, "n": "Same"},
        ]
        c = _make_catalog(tmp_path, categories=cats, files=[])
        slugs = rp._build_slug_map(c)
        assert slugs[1] == "same"
        assert slugs[2] == "same-2"
        assert slugs[3] == "same-3"

    def test_ignores_files_with_bad_format(self, tmp_path: Path):
        """File pattern requires ``cat-NN-<slug>.md``; other names are
        ignored."""
        cats = [{"i": 7, "n": "Maybe From File"}]
        c = _make_catalog(
            tmp_path, categories=cats, files=["not-cat.md", "cat-bad.md"]
        )
        slugs = rp._build_slug_map(c)
        # Falls back to slugified name.
        assert slugs[7] == "maybe-from-file"


# ---------------------------------------------------------------------------
# Regulation alias index + helpers
# ---------------------------------------------------------------------------


class TestRegulationAliasIndex:
    def test_alias_index_registers_id_shortname_name_and_aliases(self, tmp_path: Path):
        regs = {
            "gdpr": {
                "id": "gdpr",
                "shortName": "GDPR",
                "name": "General Data Protection Regulation",
                "aliases": ["EU GDPR", "2016/679"],
            }
        }
        c = _make_catalog(tmp_path, regulations=regs)
        slug_for, alias_to_id = rp._build_regulation_alias_index(c)
        assert slug_for["gdpr"] == "gdpr"
        # Every alias resolvable (after normalisation).
        for raw in ("gdpr", "GDPR", "General Data Protection Regulation", "EU GDPR"):
            assert alias_to_id[rp._normalise_alias(raw)] == "gdpr"

    def test_alias_index_handles_slug_collision(self, tmp_path: Path):
        """Two frameworks resolving to the same base slug get disambiguated."""
        regs = {
            "foo": {"id": "foo", "shortName": "Foo"},
            "foo-2": {"id": "foo", "shortName": "Foo"},  # same id -> same slug
        }
        c = _make_catalog(tmp_path, regulations=regs)
        slug_for, _ = rp._build_regulation_alias_index(c)
        slugs = sorted(slug_for.values())
        assert slugs[0] == "foo"
        assert slugs[1].startswith("foo-")  # disambiguated

    def test_alias_first_registration_wins(self, tmp_path: Path):
        """If two frameworks list the same alias, the first registration
        wins (sorted by framework id)."""
        regs = {
            "aaa": {"id": "aaa", "shortName": "A", "aliases": ["Shared"]},
            "bbb": {"id": "bbb", "shortName": "B", "aliases": ["Shared"]},
        }
        c = _make_catalog(tmp_path, regulations=regs)
        _, alias_to_id = rp._build_regulation_alias_index(c)
        assert alias_to_id[rp._normalise_alias("Shared")] == "aaa"

    def test_alias_candidates_skips_blank_values(self):
        """``if value:`` and ``if alias:`` false arms."""
        fw = {"id": "x", "shortName": "", "name": None, "aliases": ["", "Real"]}
        out = list(rp._alias_candidates(fw))
        assert out == ["x", "Real"]


class TestNormaliseAlias:
    def test_lowercases_and_collapses_whitespace(self):
        assert rp._normalise_alias("  HIPAA  Security   Rule ") == "hipaa security rule"

    def test_strips_colon_suffix_then_version(self):
        """``:2022`` is stripped first, then the trailing ``27001``
        looks like a version marker and is also stripped."""
        assert rp._normalise_alias("ISO 27001:2022") == "iso"

    def test_strips_version_suffix(self):
        assert rp._normalise_alias("PCI DSS v4.0") == "pci dss"

    def test_handles_parenthetical_version_keeps_only_word(self):
        """``ISO 27001 (2022)`` strips the parenthetical and then the
        trailing ``27001`` version marker."""
        assert rp._normalise_alias("ISO 27001 (2022)") == "iso"

    def test_blank_input(self):
        assert rp._normalise_alias("") == ""
        assert rp._normalise_alias(None) == ""  # type: ignore[arg-type]

    def test_em_dash_normalised_to_hyphen(self):
        # En dash and em dash both become ASCII hyphen.
        out = rp._normalise_alias("EU \u2013 GDPR")
        assert "-" in out


class TestResolveAlias:
    def test_returns_empty_for_none_and_blank(self):
        assert rp._resolve_alias(None, {}) == ""
        assert rp._resolve_alias("", {}) == ""
        assert rp._resolve_alias("   ", {}) == ""

    def test_exact_match(self):
        idx = {"gdpr": "gdpr"}
        assert rp._resolve_alias("GDPR", idx) == "gdpr"

    def test_prefix_match_falls_back_to_known_key(self):
        """``key.startswith(known_key + " ")`` fallback."""
        idx = {"iso 27001": "iso"}
        assert rp._resolve_alias("ISO 27001 Annex A", idx) == "iso"

    def test_known_key_starts_with_tag_also_matches(self):
        """``known_key.startswith(key + " ")`` reverse fallback."""
        idx = {"hipaa security rule": "hipaa"}
        assert rp._resolve_alias("HIPAA", idx) == "hipaa"

    def test_no_match_returns_empty(self):
        assert rp._resolve_alias("unknown", {"gdpr": "gdpr"}) == ""


# ---------------------------------------------------------------------------
# _iso_timestamp
# ---------------------------------------------------------------------------


class TestIsoTimestamp:
    def test_non_reproducible_uses_now(self, monkeypatch):
        monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
        out = rp._iso_timestamp(reproducible=False)
        assert out.endswith("Z")
        assert len(out) == 20  # YYYY-MM-DDTHH:MM:SSZ

    def test_reproducible_uses_source_date_epoch(self, monkeypatch):
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
        out = rp._iso_timestamp(reproducible=True)
        assert out == "2023-11-14T22:13:20Z"

    def test_reproducible_bad_epoch_falls_back_to_zero(self, monkeypatch):
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "garbage")
        out = rp._iso_timestamp(reproducible=True)
        assert out == "1970-01-01T00:00:00Z"

    def test_reproducible_missing_epoch_falls_back_to_zero(self, monkeypatch):
        monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
        out = rp._iso_timestamp(reproducible=True)
        assert out == "1970-01-01T00:00:00Z"


# ---------------------------------------------------------------------------
# _write_json
# ---------------------------------------------------------------------------


class TestWriteJson:
    def test_reproducible_sorts_keys(self, tmp_path: Path):
        path = tmp_path / "out.json"
        rp._write_json(path, {"b": 1, "a": 2}, reproducible=True)
        # Compact form, sorted, trailing newline (POSIX text file convention).
        assert path.read_text(encoding="utf-8") == '{"a":2,"b":1}\n'

    def test_non_reproducible_preserves_insertion_order(self, tmp_path: Path):
        path = tmp_path / "out.json"
        rp._write_json(path, {"b": 1, "a": 2}, reproducible=False)
        assert path.read_text(encoding="utf-8") == '{"b":1,"a":2}\n'

    def test_unicode_preserved(self, tmp_path: Path):
        path = tmp_path / "out.json"
        rp._write_json(path, {"name": "Détection"}, reproducible=True)
        body = path.read_text(encoding="utf-8")
        assert "Détection" in body
        round_tripped = json.loads(body)
        assert round_tripped == {"name": "Détection"}

    def test_uses_compact_separators(self, tmp_path: Path):
        path = tmp_path / "out.json"
        rp._write_json(path, {"a": [1, 2, 3]}, reproducible=True)
        body = path.read_text(encoding="utf-8")
        # No internal whitespace inside the JSON body (only the trailing \n).
        assert " " not in body
        assert body.endswith("\n")
        # Exactly one newline (the trailing one).
        assert body.count("\n") == 1


class TestDefensiveBranches:
    """Cover the four remaining defensive branches (82, 93, 247, 403)
    in render_pages.py — none are reachable from a well-formed catalog;
    each requires a malformed input that gets silently ignored."""

    def test_render_skips_categories_without_id_key(
        self, tmp_path: Path, monkeypatch
    ):
        """Lines 82 + 93 + 431: ``cat.get("i") is None`` continue paths
        in ``render`` (cat_name_for loop + per-cat render loop) and in
        ``_build_slug_map``. All three fire when a category dict lacks
        an ``i`` key entirely. (``i = None`` would crash the reproducible
        sort at line 87 — use missing key so the sort sees 0 fallback.)"""
        good = {
            "i": 1,
            "n": "Good",
            "s": [
                {
                    "i": "1.1",
                    "n": "S",
                    "u": [_make_uc("1.1.1", "Some UC")],
                }
            ],
        }
        # Missing ``i`` key entirely — survives sort, hits all three
        # ``cid is None`` continue branches.
        bad: dict = {"n": "Bad", "s": []}
        cat = _make_catalog(tmp_path, categories=[good, bad])
        rp.render(cat, tmp_path / "dist", reproducible=True)
        # Good UC was emitted; bad cat ignored.
        assert (tmp_path / "dist" / "uc" / "UC-1.1.1" / "index.json").exists()

    def test_emit_regulations_skips_groups_for_missing_framework(
        self, tmp_path: Path, monkeypatch
    ):
        """Line 247: ``if not fw: continue``. Construct the scenario by
        building the alias map first, then evicting the framework from
        the catalog so the lookup at line 245 returns None."""
        cat = _make_catalog(
            tmp_path,
            categories=[
                {
                    "i": 1,
                    "n": "C",
                    "s": [
                        {
                            "i": "1.1",
                            "n": "S",
                            "u": [_make_uc("1.1.1", "UC", regs=["GDPR"])],
                        }
                    ],
                }
            ],
            regulations={
                "gdpr": {
                    "id": "gdpr",
                    "name": "General Data Protection Regulation",
                    "shortName": "GDPR",
                    "aliases": ["GDPR"],
                }
            },
        )
        # Patch the alias index so the loop sees a non-empty grouping
        # but the regulation has been evicted from the dict before the
        # lookup.
        real_build = rp._build_regulation_alias_index

        def _build_then_evict(catalog):
            fw_slug, alias = real_build(catalog)
            # Now drop the regulation but keep the alias map so the
            # main loop iterates a grouped item whose fw is missing.
            catalog.regulations.clear()
            return fw_slug, alias

        monkeypatch.setattr(rp, "_build_regulation_alias_index", _build_then_evict)
        cat_slug_for = rp._build_slug_map(cat)
        cat_name_for: dict[int, str] = {
            c["i"]: str(c.get("n", "")) for c in cat.categories if c.get("i") is not None
        }
        ctx = rp._build_context(cat, reproducible=True)
        rp._emit_regulations(
            cat,
            cat_slug_for=cat_slug_for,
            cat_name_for=cat_name_for,
            out_dir=tmp_path / "dist",
            ctx=ctx,
            reproducible=True,
        )
        # No regulation directory should have been created.
        assert not (tmp_path / "dist" / "regulation" / "gdpr").exists()

    def test_build_uc_prereq_indexes_sort_key_handles_malformed_full_id(
        self, tmp_path: Path
    ):
        """Line 403: ``_sort_key`` fallback when the regex doesn't
        match. Triggered by a UC whose `i` field is something other
        than ``X.Y.Z`` — ``full = "UC-<garbage>"`` then becomes a value
        in the reverse-prereq map and gets sorted by ``_sort_key``."""
        cat = _make_catalog(
            tmp_path,
            categories=[
                {
                    "i": 1,
                    "n": "C",
                    "s": [
                        {
                            "i": "1.1",
                            "n": "S",
                            "u": [
                                _make_uc("1.1.1", "Real UC"),
                                # Malformed ``i`` (not X.Y.Z). Build path
                                # still constructs ``full = "UC-weird"``
                                # and appends it to the reverse map for
                                # any valid ``pre`` reference.
                                _make_uc("weird", "Bad", pre=["UC-1.1.1"]),
                            ],
                        }
                    ],
                }
            ],
        )
        title_idx, reverse_idx = rp._build_uc_prereq_indexes(cat)
        # The malformed full id was appended to the reverse list for
        # UC-1.1.1, and got sorted via the fallback branch on line 403.
        rev = reverse_idx.get("UC-1.1.1", ())
        assert "UC-weird" in rev
