"""Hermetic tests for tools/build/parse_content.py helper functions.

These tests target previously-uncovered branches:

* Catalog helpers (iter_ucs, uc_count, uc_by_id, empty)
* Loader env-var deprecation warning
* Per-category JSON loader edge cases (missing slug, bad id type,
  malformed UC.json, missing meta.json)
* Canonical → legacy converters (_premium_to_legacy,
  _references_to_legacy, _list_to_csv)
* Compliance loop edge cases (cmp rows with optional fields)
* Cat-meta loader (icon/desc/quick branches, missing dirs)
* Regulations loader (frameworks key, regulations key, list root,
  malformed JSON, missing file)
* Recently-added loader (missing file, malformed JSON, ValueError)
* Quality scoring (boilerplate detection, depth bonuses,
  vendor-UI references, troubleshooting recognition)
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

from build import parse_content  # noqa: E402


# ---------------------------------------------------------------------------
# Catalog helpers — uc_count, iter_ucs, uc_by_id, empty()
# ---------------------------------------------------------------------------


class TestCatalogHelpers:
    """Catalog dataclass methods that are bypassed by load()-only tests."""

    def test_empty_returns_empty_catalog(self):
        cat = parse_content.empty()
        assert isinstance(cat, parse_content.Catalog)
        assert cat.categories == []
        assert cat.uc_count == 0
        assert list(cat.iter_ucs()) == []

    def test_empty_with_explicit_root(self, tmp_path):
        cat = parse_content.empty(project_root=tmp_path)
        assert cat.project_root == tmp_path

    def test_uc_count_sums_across_categories(self):
        cat = parse_content.empty()
        cat.categories = [
            {
                "i": 1,
                "n": "A",
                "s": [
                    {"i": "1.1", "n": "X", "u": [{"i": "1.1.1"}, {"i": "1.1.2"}]},
                    {"i": "1.2", "n": "Y", "u": [{"i": "1.2.1"}]},
                ],
            },
            {
                "i": 2,
                "n": "B",
                "s": [{"i": "2.1", "n": "Z", "u": [{"i": "2.1.1"}]}],
            },
        ]
        assert cat.uc_count == 4

    def test_iter_ucs_yields_triples_in_order(self):
        cat = parse_content.empty()
        cat.categories = [
            {
                "i": 1,
                "n": "A",
                "s": [{"i": "1.1", "n": "X", "u": [{"i": "1.1.1"}, {"i": "1.1.2"}]}],
            }
        ]
        result = list(cat.iter_ucs())
        assert len(result) == 2
        # (cat, sub, uc) triple
        assert result[0][0]["i"] == 1
        assert result[0][1]["i"] == "1.1"
        assert result[0][2]["i"] == "1.1.1"
        assert result[1][2]["i"] == "1.1.2"

    def test_uc_by_id_finds_match(self):
        cat = parse_content.empty()
        cat.categories = [
            {
                "i": 1,
                "n": "A",
                "s": [{"i": "1.1", "n": "X", "u": [{"i": "1.1.1", "n": "Found"}]}],
            }
        ]
        uc = cat.uc_by_id("1.1.1")
        assert uc is not None
        assert uc["n"] == "Found"

    def test_uc_by_id_returns_none_for_missing(self):
        cat = parse_content.empty()
        cat.categories = [
            {
                "i": 1,
                "n": "A",
                "s": [{"i": "1.1", "n": "X", "u": [{"i": "1.1.1"}]}],
            }
        ]
        assert cat.uc_by_id("99.99.99") is None


# ---------------------------------------------------------------------------
# _resolve_loader_kind — env var deprecation warning
# ---------------------------------------------------------------------------


class TestResolveLoaderKind:
    """The env var is kept for backward compat. A non-default value
    triggers a one-line stderr deprecation notice (line 136) and still
    returns ``"content"``."""

    def test_default_returns_content(self, monkeypatch):
        monkeypatch.delenv("SPLUNK_UC_LOADER", raising=False)
        assert parse_content._resolve_loader_kind() == "content"

    def test_empty_string_returns_content_silently(self, monkeypatch, capsys):
        monkeypatch.setenv("SPLUNK_UC_LOADER", "")
        assert parse_content._resolve_loader_kind() == "content"
        captured = capsys.readouterr()
        assert "deprecated" not in captured.err

    def test_legacy_value_emits_deprecation_warning(self, monkeypatch, capsys):
        monkeypatch.setenv("SPLUNK_UC_LOADER", "legacy")
        result = parse_content._resolve_loader_kind()
        assert result == "content"
        captured = capsys.readouterr()
        assert "deprecated" in captured.err
        assert "legacy" in captured.err

    def test_content_value_no_warning(self, monkeypatch, capsys):
        monkeypatch.setenv("SPLUNK_UC_LOADER", "content")
        assert parse_content._resolve_loader_kind() == "content"
        captured = capsys.readouterr()
        assert "deprecated" not in captured.err


# ---------------------------------------------------------------------------
# _load_categories_from_content — missing/malformed inputs
# ---------------------------------------------------------------------------


class TestLoadCategoriesFromContentEdgeCases:
    """Defensive code paths in the per-category JSON loader."""

    def test_missing_content_dir_returns_empty(self, tmp_path):
        # No content/ dir at all → loader returns silently (line 256).
        cat = parse_content.empty(project_root=tmp_path)
        parse_content._load_categories_from_content(cat, tmp_path, reproducible=False)
        assert cat.categories == []
        assert cat.files == []

    def test_skips_dir_without_meta_file(self, tmp_path):
        # cat-NN/ exists but has no _category.json → skipped.
        content = tmp_path / "content"
        content.mkdir()
        (content / "cat-99-test").mkdir()
        cat = parse_content.empty(project_root=tmp_path)
        parse_content._load_categories_from_content(cat, tmp_path, reproducible=False)
        assert cat.categories == []

    def test_skips_dir_with_malformed_meta(self, tmp_path, capsys):
        # Bad JSON in _category.json triggers warn-and-skip (lines 274-276).
        content = tmp_path / "content"
        content.mkdir()
        bad = content / "cat-99-test"
        bad.mkdir()
        (bad / "_category.json").write_text("{ this is not json }", encoding="utf-8")
        cat = parse_content.empty(project_root=tmp_path)
        parse_content._load_categories_from_content(cat, tmp_path, reproducible=False)
        assert cat.categories == []
        err = capsys.readouterr().err
        assert "skipping" in err

    def test_skips_meta_without_id(self, tmp_path):
        # ``id`` key missing → skipped (line 279).
        content = tmp_path / "content"
        content.mkdir()
        d = content / "cat-99-test"
        d.mkdir()
        (d / "_category.json").write_text(
            json.dumps({"name": "Test"}), encoding="utf-8"
        )
        cat = parse_content.empty(project_root=tmp_path)
        parse_content._load_categories_from_content(cat, tmp_path, reproducible=False)
        assert cat.categories == []

    def test_skips_meta_with_non_int_id(self, tmp_path):
        # ``id`` is non-int → ValueError → skipped (lines 282-283).
        content = tmp_path / "content"
        content.mkdir()
        d = content / "cat-99-test"
        d.mkdir()
        (d / "_category.json").write_text(
            json.dumps({"id": "not-a-number", "name": "Test"}),
            encoding="utf-8",
        )
        cat = parse_content.empty(project_root=tmp_path)
        parse_content._load_categories_from_content(cat, tmp_path, reproducible=False)
        assert cat.categories == []

    def test_skips_subcategory_without_id(self, tmp_path):
        # subcategory missing ``id`` → skipped (line 322).
        content = tmp_path / "content"
        content.mkdir()
        d = content / "cat-99-test"
        d.mkdir()
        (d / "_category.json").write_text(
            json.dumps(
                {
                    "id": 99,
                    "name": "Test Cat",
                    "slug": "cat-99-test",
                    "subcategories": [
                        {"name": "No ID Here"},
                        {"id": "99.1", "name": "Has ID"},
                    ],
                }
            ),
            encoding="utf-8",
        )
        cat = parse_content.empty(project_root=tmp_path)
        parse_content._load_categories_from_content(cat, tmp_path, reproducible=False)
        # Only the well-formed subcategory should be present.
        assert len(cat.categories) == 1
        assert len(cat.categories[0]["s"]) == 1
        assert cat.categories[0]["s"][0]["i"] == "99.1"

    def test_skips_uc_with_malformed_json(self, tmp_path, capsys):
        # UC-X.Y.Z.json that's malformed → warn-and-skip (lines 349-351).
        content = tmp_path / "content"
        content.mkdir()
        d = content / "cat-99-test"
        d.mkdir()
        (d / "_category.json").write_text(
            json.dumps(
                {
                    "id": 99,
                    "name": "Test",
                    "slug": "cat-99-test",
                    "subcategories": [{"id": "99.1", "name": "Sub"}],
                }
            ),
            encoding="utf-8",
        )
        (d / "UC-99.1.1.json").write_text("{ malformed }", encoding="utf-8")
        cat = parse_content.empty(project_root=tmp_path)
        parse_content._load_categories_from_content(cat, tmp_path, reproducible=False)
        # Cat is created but the malformed UC is skipped.
        assert len(cat.categories) == 1
        assert len(cat.categories[0]["s"][0]["u"]) == 0
        assert "skipping" in capsys.readouterr().err

    def test_skips_uc_without_id(self, tmp_path):
        # UC-X.Y.Z.json with no ``id`` → skipped silently (line 354).
        content = tmp_path / "content"
        content.mkdir()
        d = content / "cat-99-test"
        d.mkdir()
        (d / "_category.json").write_text(
            json.dumps(
                {
                    "id": 99,
                    "name": "Test",
                    "slug": "cat-99-test",
                    "subcategories": [{"id": "99.1", "name": "Sub"}],
                }
            ),
            encoding="utf-8",
        )
        (d / "UC-99.1.1.json").write_text(
            json.dumps({"title": "no id present"}),
            encoding="utf-8",
        )
        cat = parse_content.empty(project_root=tmp_path)
        parse_content._load_categories_from_content(cat, tmp_path, reproducible=False)
        # Cat is created but UC is dropped because id is missing.
        assert len(cat.categories) == 1
        assert len(cat.categories[0]["s"][0]["u"]) == 0

    def test_uc_with_unknown_subcategory_creates_stub(self, tmp_path):
        # UC's natural id prefix doesn't match any declared sub →
        # auto-stub bucket created (line 363-365).
        content = tmp_path / "content"
        content.mkdir()
        d = content / "cat-99-test"
        d.mkdir()
        (d / "_category.json").write_text(
            json.dumps(
                {
                    "id": 99,
                    "name": "Test",
                    "slug": "cat-99-test",
                    # Only declares 99.1 — UC-99.5.1 will fall to auto-stub.
                    "subcategories": [{"id": "99.1", "name": "Sub"}],
                }
            ),
            encoding="utf-8",
        )
        (d / "UC-99.5.1.json").write_text(
            json.dumps(
                {
                    "id": "99.5.1",
                    "title": "Orphaned UC",
                    "criticality": "low",
                    "difficulty": "beginner",
                    "value": "x",
                    "app": "y",
                    "dataSources": "z",
                    "spl": "search",
                    "implementation": "i",
                    "visualization": "v",
                    "cimModels": [],
                    "grandmaExplanation": "Just a test UC. Plain language fine.",
                    "monitoringType": ["Performance"],
                }
            ),
            encoding="utf-8",
        )
        cat = parse_content.empty(project_root=tmp_path)
        parse_content._load_categories_from_content(cat, tmp_path, reproducible=False)
        # Two subcategories now: declared "99.1" + auto-stub "99.5".
        sub_ids = [s["i"] for s in cat.categories[0]["s"]]
        assert "99.1" in sub_ids
        assert "99.5" in sub_ids

    def test_reproducible_sorts_categories_by_i(self, tmp_path):
        # ``reproducible=True`` triggers a sort by category id (line 382-383).
        content = tmp_path / "content"
        content.mkdir()
        for i in (3, 1, 2):
            d = content / f"cat-{i:02}-test"
            d.mkdir()
            (d / "_category.json").write_text(
                json.dumps({"id": i, "name": f"C{i}", "slug": f"cat-{i:02}-test"}),
                encoding="utf-8",
            )
        cat = parse_content.empty(project_root=tmp_path)
        parse_content._load_categories_from_content(cat, tmp_path, reproducible=True)
        assert [c["i"] for c in cat.categories] == [1, 2, 3]


# ---------------------------------------------------------------------------
# _premium_to_legacy / _references_to_legacy / _list_to_csv
# ---------------------------------------------------------------------------


class TestPremiumToLegacy:
    """Flatten canonical premiumApps (list of str / object) → legacy string."""

    def test_non_list_returns_empty(self):
        assert parse_content._premium_to_legacy(None) == ""
        assert parse_content._premium_to_legacy("ES") == ""
        assert parse_content._premium_to_legacy({"name": "ES"}) == ""

    def test_empty_list_returns_empty(self):
        assert parse_content._premium_to_legacy([]) == ""

    def test_list_of_strings(self):
        # Plain-string entries (line 449).
        result = parse_content._premium_to_legacy(["ES", "ITSI"])
        assert result == "ES, ITSI"

    def test_dict_without_displayname_skipped(self):
        # Dict missing displayName/name → skipped (line 452).
        result = parse_content._premium_to_legacy(
            [{"note": "expensive"}, {"displayName": "ES"}]
        )
        assert result == "ES"

    def test_dict_with_note_appended(self):
        # Note rendered as parenthetical when not already in displayName.
        result = parse_content._premium_to_legacy(
            [{"displayName": "ITSI", "note": "5.x"}]
        )
        assert result == "ITSI (5.x)"

    def test_dict_with_note_already_in_displayname_no_double_paren(self):
        # When displayName already contains ``(note)``, don't duplicate.
        result = parse_content._premium_to_legacy(
            [{"displayName": "ITSI (5.x)", "note": "5.x"}]
        )
        assert result == "ITSI (5.x)"

    def test_dict_falls_back_to_name(self):
        # When ``displayName`` is missing, ``name`` is used.
        result = parse_content._premium_to_legacy([{"name": "SOAR"}])
        assert result == "SOAR"

    def test_non_dict_non_string_skipped(self):
        # Items that are neither str nor dict are silently skipped.
        result = parse_content._premium_to_legacy([42, "ES", None, ["nested"]])
        assert result == "ES"


class TestReferencesToLegacy:
    """Flatten canonical references (list of objects) → legacy string."""

    def test_non_list_returns_empty(self):
        # Line 463-464.
        assert parse_content._references_to_legacy(None) == ""
        assert parse_content._references_to_legacy("https://x") == ""

    def test_skips_non_dict(self):
        # Items that are not dicts → continue (line 467-468).
        result = parse_content._references_to_legacy(
            ["https://x", {"url": "https://y", "title": "Y"}]
        )
        assert result == "[Y](https://y)"

    def test_skips_entries_without_url(self):
        # Empty url → skipped (line 470-471).
        result = parse_content._references_to_legacy(
            [{"title": "No URL"}, {"url": "", "title": "Empty"}, {"url": "https://x"}]
        )
        assert result == "https://x"

    def test_url_only_emits_bare_link(self):
        # No title → bare URL.
        result = parse_content._references_to_legacy([{"url": "https://x"}])
        assert result == "https://x"

    def test_with_title_emits_markdown(self):
        result = parse_content._references_to_legacy(
            [{"url": "https://x", "title": "X Docs"}]
        )
        assert result == "[X Docs](https://x)"


class TestListToCsv:
    def test_non_list_returns_empty(self):
        assert parse_content._list_to_csv(None) == ""
        assert parse_content._list_to_csv("string") == ""

    def test_strips_and_filters_empty(self):
        # Whitespace-only entries are dropped.
        result = parse_content._list_to_csv(["a", "  ", "b"])
        assert result == "a, b"

    def test_coerces_non_strings(self):
        # ``str(v)`` is applied to every entry.
        result = parse_content._list_to_csv([1, 2, 3])
        assert result == "1, 2, 3"


# ---------------------------------------------------------------------------
# _canonical_uc_to_legacy — compliance + cmp paths
# ---------------------------------------------------------------------------


class TestCanonicalUcToLegacyComplianceCmp:
    """Compliance/cmp loops have several optional-field branches."""

    def test_compliance_skips_non_dict_entries(self):
        # Line 605: continue when entry is not a dict.
        canonical = {
            "id": "1.1.1",
            "title": "T",
            "compliance": [
                "junk",
                {"regulation": "PCI DSS", "version": "4.0", "clause": "1.1"},
            ],
        }
        uc = parse_content._canonical_uc_to_legacy(canonical)
        assert uc.get("regs") == ["PCI DSS"]

    def test_regs_list_supplements_compliance(self):
        # Lines 613-616: ``regs`` field on canonical is merged with
        # compliance regulations (de-duped).
        canonical = {
            "id": "1.1.1",
            "title": "T",
            "compliance": [
                {"regulation": "PCI DSS", "version": "4.0", "clause": "1.1"},
            ],
            "regs": ["GDPR", "PCI DSS"],  # PCI DSS is duplicate.
        }
        uc = parse_content._canonical_uc_to_legacy(canonical)
        assert uc.get("regs") == ["PCI DSS", "GDPR"]

    def test_cmp_drops_entry_missing_regulation(self):
        # Lines 637-649: clause requires reg+version+clause.
        canonical = {
            "id": "1.1.1",
            "title": "T",
            "compliance": [
                {"version": "4.0", "clause": "1.1"},  # missing regulation
                {"regulation": "PCI DSS", "version": "4.0"},  # missing clause
                {
                    "regulation": "PCI DSS",
                    "version": "4.0",
                    "clause": "1.1",
                    "mode": "monitor",
                    "assurance": "high",
                    "controlObjective": "obj",
                    "evidenceArtifact": "e",
                    "clauseUrl": "https://x",
                },
            ],
        }
        uc = parse_content._canonical_uc_to_legacy(canonical)
        # Only the well-formed entry survives in cmp.
        assert "cmp" in uc
        assert len(uc["cmp"]) == 1
        row = uc["cmp"][0]
        assert row["r"] == "PCI DSS"
        assert row["v"] == "4.0"
        assert row["cl"] == "1.1"
        assert row["m"] == "monitor"
        assert row["a"] == "high"
        assert row["co"] == "obj"
        assert row["ea"] == "e"
        assert row["u"] == "https://x"

    def test_cmp_rows_sorted(self):
        # Line 671-672: rows are sorted by (r, v, cl).
        canonical = {
            "id": "1.1.1",
            "title": "T",
            "compliance": [
                {"regulation": "Z-Reg", "version": "1.0", "clause": "1.1"},
                {"regulation": "A-Reg", "version": "1.0", "clause": "2.2"},
                {"regulation": "A-Reg", "version": "1.0", "clause": "1.1"},
            ],
        }
        uc = parse_content._canonical_uc_to_legacy(canonical)
        rows = uc["cmp"]
        assert [(r["r"], r["cl"]) for r in rows] == [
            ("A-Reg", "1.1"),
            ("A-Reg", "2.2"),
            ("Z-Reg", "1.1"),
        ]


# ---------------------------------------------------------------------------
# _load_cat_meta_from_content — icon/desc/quick paths
# ---------------------------------------------------------------------------


class TestLoadCatMetaFromContent:
    def test_no_content_dir_no_op(self, tmp_path):
        # Line 962-963.
        cat = parse_content.empty(project_root=tmp_path)
        parse_content._load_cat_meta_from_content(cat, tmp_path)
        assert cat.cat_meta == {}

    def test_skips_non_dir_entries(self, tmp_path):
        # Stray file in content/ is ignored (line 966-967).
        content = tmp_path / "content"
        content.mkdir()
        (content / "stray.txt").write_text("not a dir")
        cat = parse_content.empty(project_root=tmp_path)
        parse_content._load_cat_meta_from_content(cat, tmp_path)
        assert cat.cat_meta == {}

    def test_skips_dir_without_meta(self, tmp_path):
        # No _category.json → skipped (line 969-970).
        content = tmp_path / "content"
        content.mkdir()
        (content / "cat-99").mkdir()
        cat = parse_content.empty(project_root=tmp_path)
        parse_content._load_cat_meta_from_content(cat, tmp_path)
        assert cat.cat_meta == {}

    def test_skips_dir_with_malformed_meta(self, tmp_path):
        # Malformed JSON → continue (line 974-975).
        content = tmp_path / "content"
        content.mkdir()
        d = content / "cat-99"
        d.mkdir()
        (d / "_category.json").write_text("{ broken", encoding="utf-8")
        cat = parse_content.empty(project_root=tmp_path)
        parse_content._load_cat_meta_from_content(cat, tmp_path)
        assert cat.cat_meta == {}

    def test_skips_meta_without_id(self, tmp_path):
        # No id field → skipped (line 977-978).
        content = tmp_path / "content"
        content.mkdir()
        d = content / "cat-99"
        d.mkdir()
        (d / "_category.json").write_text(json.dumps({"name": "X"}), encoding="utf-8")
        cat = parse_content.empty(project_root=tmp_path)
        parse_content._load_cat_meta_from_content(cat, tmp_path)
        assert cat.cat_meta == {}

    def test_loads_icon_desc_quick(self, tmp_path):
        # All three optional fields populated (lines 980, 982, 984).
        content = tmp_path / "content"
        content.mkdir()
        d = content / "cat-99"
        d.mkdir()
        (d / "_category.json").write_text(
            json.dumps(
                {
                    "id": 99,
                    "name": "X",
                    "icon": "🚀",
                    "description": "Test cat",
                    "quickTip": "Run audits often.",
                }
            ),
            encoding="utf-8",
        )
        cat = parse_content.empty(project_root=tmp_path)
        parse_content._load_cat_meta_from_content(cat, tmp_path)
        assert cat.cat_meta == {
            "99": {"icon": "🚀", "desc": "Test cat", "quick": "Run audits often."}
        }

    def test_loads_partial_fields(self, tmp_path):
        # Only icon set — desc/quick stay at defaults.
        content = tmp_path / "content"
        content.mkdir()
        d = content / "cat-99"
        d.mkdir()
        (d / "_category.json").write_text(
            json.dumps({"id": 99, "name": "X", "icon": "📊"}),
            encoding="utf-8",
        )
        cat = parse_content.empty(project_root=tmp_path)
        parse_content._load_cat_meta_from_content(cat, tmp_path)
        assert cat.cat_meta["99"]["icon"] == "📊"
        assert cat.cat_meta["99"]["desc"] == ""
        assert "quick" not in cat.cat_meta["99"]


# ---------------------------------------------------------------------------
# _load_regulations
# ---------------------------------------------------------------------------


class TestLoadRegulations:
    def test_missing_file_no_op(self, tmp_path):
        # Lines 1002-1003.
        cat = parse_content.empty(project_root=tmp_path)
        parse_content._load_regulations(cat, tmp_path)
        assert cat.regulations == {}

    def test_malformed_json_no_op(self, tmp_path):
        # Lines 1007-1008.
        (tmp_path / "data").mkdir()
        (tmp_path / "data" / "regulations.json").write_text("{ broken")
        cat = parse_content.empty(project_root=tmp_path)
        parse_content._load_regulations(cat, tmp_path)
        assert cat.regulations == {}

    def test_loads_from_frameworks_key(self, tmp_path):
        # Line 1012-1014: ``frameworks`` wrapper key.
        (tmp_path / "data").mkdir()
        (tmp_path / "data" / "regulations.json").write_text(
            json.dumps(
                {
                    "frameworks": [
                        {"id": "PCI DSS", "name": "PCI DSS", "version": "4.0"},
                    ]
                }
            ),
            encoding="utf-8",
        )
        cat = parse_content.empty(project_root=tmp_path)
        parse_content._load_regulations(cat, tmp_path)
        assert "PCI DSS" in cat.regulations

    def test_loads_from_regulations_key(self, tmp_path):
        # Line 1012-1014: ``regulations`` alternate wrapper key.
        (tmp_path / "data").mkdir()
        (tmp_path / "data" / "regulations.json").write_text(
            json.dumps(
                {
                    "regulations": [
                        {"id": "GDPR", "name": "GDPR"},
                    ]
                }
            ),
            encoding="utf-8",
        )
        cat = parse_content.empty(project_root=tmp_path)
        parse_content._load_regulations(cat, tmp_path)
        assert "GDPR" in cat.regulations

    def test_loads_from_root_list(self, tmp_path):
        # Line 1016-1017: top-level array (no wrapper).
        (tmp_path / "data").mkdir()
        (tmp_path / "data" / "regulations.json").write_text(
            json.dumps([{"id": "ISO27001", "name": "ISO 27001"}]),
            encoding="utf-8",
        )
        cat = parse_content.empty(project_root=tmp_path)
        parse_content._load_regulations(cat, tmp_path)
        assert "ISO27001" in cat.regulations

    def test_skips_non_dict_entries(self, tmp_path):
        # Line 1020-1021.
        (tmp_path / "data").mkdir()
        (tmp_path / "data" / "regulations.json").write_text(
            json.dumps([{"id": "A"}, "garbage", {"id": "B"}]),
            encoding="utf-8",
        )
        cat = parse_content.empty(project_root=tmp_path)
        parse_content._load_regulations(cat, tmp_path)
        assert "A" in cat.regulations
        assert "B" in cat.regulations
        assert len(cat.regulations) == 2

    def test_skips_entries_without_id_or_short_or_name(self, tmp_path):
        # Line 1022-1024.
        (tmp_path / "data").mkdir()
        (tmp_path / "data" / "regulations.json").write_text(
            json.dumps([{"description": "no id"}, {"name": "Has Name"}]),
            encoding="utf-8",
        )
        cat = parse_content.empty(project_root=tmp_path)
        parse_content._load_regulations(cat, tmp_path)
        assert "Has Name" in cat.regulations
        assert len(cat.regulations) == 1

    def test_falls_back_to_short_name(self, tmp_path):
        (tmp_path / "data").mkdir()
        (tmp_path / "data" / "regulations.json").write_text(
            json.dumps([{"shortName": "S", "name": "Full Name"}]),
            encoding="utf-8",
        )
        cat = parse_content.empty(project_root=tmp_path)
        parse_content._load_regulations(cat, tmp_path)
        # shortName is preferred over name when id absent.
        assert "S" in cat.regulations


# ---------------------------------------------------------------------------
# _load_recently_added
# ---------------------------------------------------------------------------


class TestLoadRecentlyAdded:
    def test_missing_file_no_op(self, tmp_path):
        # Lines 1032-1033.
        cat = parse_content.empty(project_root=tmp_path)
        parse_content._load_recently_added(cat, tmp_path)
        assert cat.recently_added == []

    def test_malformed_json_resets_to_empty(self, tmp_path):
        # Lines 1037-1038.
        (tmp_path / "recently-added.json").write_text("{ broken")
        cat = parse_content.empty(project_root=tmp_path)
        parse_content._load_recently_added(cat, tmp_path)
        assert cat.recently_added == []

    def test_loads_list(self, tmp_path):
        (tmp_path / "recently-added.json").write_text(
            json.dumps(["UC-1.1.1", "UC-2.2.2"]),
            encoding="utf-8",
        )
        cat = parse_content.empty(project_root=tmp_path)
        parse_content._load_recently_added(cat, tmp_path)
        assert cat.recently_added == ["UC-1.1.1", "UC-2.2.2"]

    def test_null_value_resets_to_empty(self, tmp_path):
        # JSON ``null`` → load returns None → ``or []``.
        (tmp_path / "recently-added.json").write_text("null")
        cat = parse_content.empty(project_root=tmp_path)
        parse_content._load_recently_added(cat, tmp_path)
        assert cat.recently_added == []


# ---------------------------------------------------------------------------
# _load_cat_meta — RuntimeError fallback when loader != content
# ---------------------------------------------------------------------------


class TestLoadCatMetaLoaderFallback:
    def test_legacy_loader_raises_runtimeerror(self, tmp_path):
        # Lines 941-950.
        cat = parse_content.empty(project_root=tmp_path)
        cat.loader = "legacy"
        with pytest.raises(RuntimeError, match="Legacy markdown loader"):
            parse_content._load_cat_meta(cat, tmp_path)


# ---------------------------------------------------------------------------
# _compute_quality — edge branches
# ---------------------------------------------------------------------------


class TestComputeQuality:
    """Cover quality scoring branches that are hard to hit via real UCs."""

    def test_missing_bronze_field_returns_none_tier(self):
        # Line 790-791: missing required bronze fields shortcuts to none.
        uc = {"i": "1.1.1", "n": "T"}
        tier, depth, gaps = parse_content._compute_quality(uc)
        assert tier == "none"
        assert depth < 25
        # All bronze fields except (i,n) are missing.
        assert any("missing:" in g for g in gaps)

    def test_silver_with_short_md_emits_gap(self):
        # Lines 808-813: md_text under 200 chars triggers a Silver gap.
        uc = {
            "i": "1.1.1",
            "n": "T",
            "c": "high",
            "f": "easy",
            "q": "search",
            "v": "v",
            "d": "d",
            "t": "t",
            "m": "m",
            "mtype": ["Performance"],
            "md": "Short impl.",
            "refs": "https://x",
            "e": ["eq1"],
            "ge": "Plain explanation.",
            "wv": "crawl",
        }
        tier, depth, gaps = parse_content._compute_quality(uc)
        # Silver gates failed because md_text < 200 chars.
        assert any("too short for Silver" in g for g in gaps)

    def test_gold_with_short_md_emits_gap(self):
        # Lines 838-842: md_text >= 200 (passes Silver) but < 500
        # (fails Gold) → "too short for Gold" gap.
        md = (
            "Step 0 prerequisite: install TA. "
            "Step 1 configure data collection. "
            "Step 2 understanding this SPL query stage by stage. "
            "Step 3 validate the result. "
            "Step 5 operationalize this content. "
            + ("Some explanatory body content. " * 5)
        )
        # Check it's between 200 and 500.
        assert 200 <= len(md) < 500
        uc = {
            "i": "1.1.1",
            "n": "T",
            "c": "high",
            "f": "easy",
            "q": "search",
            "v": "v",
            "d": "d",
            "t": "t",
            "m": "m",
            "mtype": ["Performance"],
            "md": md,
            "refs": "[X](https://x), [Y](https://y)",
            "e": ["eq1"],
            "em": ["model1"],
            "ge": "Plain explanation that's long enough.",
            "wv": "crawl",
            "z": "Single value.",
        }
        tier, depth, gaps = parse_content._compute_quality(uc)
        # Gold gate failed because md_text < 500 chars.
        assert any("too short for Gold" in g for g in gaps)

    def test_specificity_bonus_applied(self):
        # Lines 864-867: specificity >= 5 yields +10 to depth.
        md = (
            "Step 0 prerequisite. Step 1 configure data. "
            "Step 2 understanding this SPL. Step 3 validate. "
            "Step 5 operationalize. "
            "sourcetype=cisco:ise index=ise /api/v1/health "
            "GET /endpoint inputs.conf RBAC role required "
            "Splunkbase 12345 modular input. "
            + "details about implementation. " * 30
        )
        uc = {
            "i": "1.1.1",
            "n": "T",
            "c": "high",
            "f": "easy",
            "q": "search",
            "v": "v",
            "d": "d",
            "t": "t",
            "m": "m",
            "mtype": ["Performance"],
            "md": md,
            "refs": "[X](https://x), [Y](https://y)",
            "e": ["eq1"],
            "em": ["model1"],
            "ge": "Plain explanation.",
            "wv": "crawl",
            "z": "Single value.",
        }
        tier, depth, gaps = parse_content._compute_quality(uc)
        # Should be Gold + specificity bonus.
        assert tier == "gold"
        assert depth >= 75

    def test_boilerplate_penalty_applied(self):
        # Lines 877-881: >50% generic boilerplate penalises by 15.
        boiler = (
            "Install the TA and configure the input. "
            "Check splunkd.log. Ensure your TA is installed. "
        ) * 5
        uc = {
            "i": "1.1.1",
            "n": "T",
            "c": "high",
            "f": "easy",
            "q": "search",
            "v": "v",
            "d": "d",
            "t": "t",
            "m": "m",
            "md": boiler,
        }
        tier, depth, gaps = parse_content._compute_quality(uc)
        # Bronze passes because all required fields present;
        # Silver/Gold fail. Gap mentions boilerplate.
        assert any("boilerplate" in g for g in gaps)


# ---------------------------------------------------------------------------
# _inject_quality_scores
# ---------------------------------------------------------------------------


class TestInjectQualityScores:
    def test_subcategory_with_no_ucs_skipped(self):
        record = {"i": 1, "n": "C", "s": [{"i": "1.1", "n": "Empty", "u": []}]}
        parse_content._inject_quality_scores(record)
        # No qa/qd injected on empty sub.
        assert "qa" not in record["s"][0]

    def test_subcategory_aggregate_score(self):
        # qa = average depth, qd = tier distribution.
        record = {
            "i": 1,
            "n": "C",
            "s": [
                {
                    "i": "1.1",
                    "n": "S",
                    "u": [
                        {
                            "i": "1.1.1",
                            "n": "T",
                            "c": "high",
                            "f": "easy",
                            "q": "search",
                            "v": "v",
                            "d": "d",
                            "t": "t",
                            "m": "m",
                        },
                    ],
                }
            ],
        }
        parse_content._inject_quality_scores(record)
        assert "qa" in record["s"][0]
        assert "qd" in record["s"][0]


# ---------------------------------------------------------------------------
# _validate_uc_json — jsonschema-not-available fallback
# ---------------------------------------------------------------------------


class TestValidateUcJsonFallback:
    def test_returns_empty_when_jsonschema_unavailable(self, monkeypatch):
        # Line 105-106: defensive return when jsonschema is None.
        monkeypatch.setattr(parse_content, "jsonschema", None, raising=True)
        # Pass a UC dict that would normally fail validation.
        errors = parse_content._validate_uc_json(
            {"definitely_invalid": "no_id"}, Path("test.json"), {}
        )
        assert errors == []


# ---------------------------------------------------------------------------
# _post_process_category — ESCU short-impl regen and equipment fallback
# ---------------------------------------------------------------------------


class TestPostProcessCategoryEscuShortImpl:
    """Lines 697-699: ESCU detections regenerate ``uc['m']`` (short
    implementation) when the canonical ``m`` is the generic prefix
    or empty."""

    def test_escu_with_generic_short_impl_gets_regenerated(self):
        from build import enrichment as legacy

        record = {
            "i": 99,
            "n": "C",
            "s": [
                {
                    "i": "99.1",
                    "n": "S",
                    "u": [
                        {
                            "i": "99.1.1",
                            "n": "T",
                            "c": "high",
                            "f": "easy",
                            "v": "v",
                            "t": "ESCU",
                            "d": "d",
                            # Mark as ESCU (the simulator does this through
                            # the JSON schema; here we set the marker
                            # directly).
                            "escu": True,
                            "dtype": "TTP",
                            "q": "search",
                            # Generic prefix → triggers regen.
                            "m": legacy.ESCU_GENERIC_IMPL_PREFIX
                            + " standard install line.",
                        },
                    ],
                }
            ],
        }
        parse_content._post_process_category(record, legacy)
        uc = record["s"][0]["u"][0]
        # md must be the regenerated detailed impl, m the regenerated short.
        assert uc.get("md")
        assert "ESCU" in uc.get("md", "") or "Enterprise Security" in uc.get("md", "")

    def test_escu_with_empty_short_impl_gets_regenerated(self):
        from build import enrichment as legacy

        record = {
            "i": 99,
            "n": "C",
            "s": [
                {
                    "i": "99.1",
                    "n": "S",
                    "u": [
                        {
                            "i": "99.1.1",
                            "n": "T",
                            "c": "high",
                            "f": "easy",
                            "v": "v",
                            "t": "ESCU",
                            "d": "d",
                            "escu": True,
                            "dtype": "TTP",
                            "q": "search",
                            "m": "",  # empty triggers regen
                        },
                    ],
                }
            ],
        }
        parse_content._post_process_category(record, legacy)
        # md regenerated, m regenerated to non-empty.
        uc = record["s"][0]["u"][0]
        assert uc.get("m") and uc["m"].strip() != ""


class TestPostProcessCategoryEquipmentFromSidecar:
    """Lines 707-721: equipment lookup paths.

    Three branches:
    * sidecar provides equipment (line 704-706)
    * no sidecar AND no ``e`` already → derive from TA string (line 707-710)
    * sidecar absent, ``e`` present, ``em`` is None → re-derive em only
      (line 711-721)
    """

    def test_no_sidecar_no_existing_equipment_derives_from_ta(
        self, monkeypatch
    ):
        """When ``uc['e']`` is empty and the TA string matches an entry
        in EQUIPMENT, equipment_ids_for_ta_string should populate it."""
        from build import enrichment as legacy

        # No sidecars on disk → _sidecar_equipment_tags returns (None, None).
        monkeypatch.setattr(
            legacy, "_sidecar_equipment_tags", lambda *a, **kw: (None, None)
        )
        # Patch equipment_ids_for_ta_string to return known IDs.
        monkeypatch.setattr(
            legacy,
            "equipment_ids_for_ta_string",
            lambda ta: (["eq-router"], ["model-asr-9000"]),
        )

        record = {
            "i": 99,
            "n": "C",
            "s": [
                {
                    "i": "99.1",
                    "n": "S",
                    "u": [
                        {
                            "i": "99.1.1",
                            "n": "T",
                            "c": "high",
                            "f": "easy",
                            "v": "v",
                            "d": "d",
                            "t": "ASR-9000-TA",
                            "q": "search",
                        },
                    ],
                }
            ],
        }
        parse_content._post_process_category(record, legacy)
        uc = record["s"][0]["u"][0]
        assert uc["e"] == ["eq-router"]
        assert uc["em"] == ["model-asr-9000"]

    def test_existing_equipment_with_none_em_re_derives(self, monkeypatch):
        """Line 711-721: ``e`` arrived from canonical but ``em`` is None
        (the empty-list got dropped during JSON migration). Re-derive
        ``em`` only — don't overwrite ``e``."""
        from build import enrichment as legacy

        monkeypatch.setattr(
            legacy, "_sidecar_equipment_tags", lambda *a, **kw: (None, None)
        )
        monkeypatch.setattr(
            legacy,
            "equipment_ids_for_ta_string",
            lambda ta: (["wrong-equipment"], ["correct-model"]),
        )
        record = {
            "i": 99,
            "n": "C",
            "s": [
                {
                    "i": "99.1",
                    "n": "S",
                    "u": [
                        {
                            "i": "99.1.1",
                            "n": "T",
                            "c": "high",
                            "f": "easy",
                            "v": "v",
                            "d": "d",
                            "t": "T",
                            "q": "s",
                            # ``e`` populated but ``em`` is None.
                            "e": ["existing-equipment"],
                            "em": None,
                        },
                    ],
                }
            ],
        }
        parse_content._post_process_category(record, legacy)
        uc = record["s"][0]["u"][0]
        # ``e`` MUST be preserved (not overwritten with "wrong-equipment").
        assert uc["e"] == ["existing-equipment"]
        # ``em`` is re-derived from the TA string.
        assert uc["em"] == ["correct-model"]

    def test_sidecar_provides_equipment(self, monkeypatch):
        """Line 704-706: when sidecar returns non-None equipment, use it."""
        from build import enrichment as legacy

        monkeypatch.setattr(
            legacy,
            "_sidecar_equipment_tags",
            lambda cat_id, uc_id: (["sidecar-eq"], ["sidecar-model"]),
        )
        record = {
            "i": 99,
            "n": "C",
            "s": [
                {
                    "i": "99.1",
                    "n": "S",
                    "u": [
                        {
                            "i": "99.1.1",
                            "n": "T",
                            "c": "high",
                            "f": "easy",
                            "v": "v",
                            "d": "d",
                            "t": "T",
                            "q": "s",
                            "e": ["initial-stale"],  # gets overwritten.
                            "em": ["initial-stale-model"],
                        },
                    ],
                }
            ],
        }
        parse_content._post_process_category(record, legacy)
        uc = record["s"][0]["u"][0]
        assert uc["e"] == ["sidecar-eq"]
        assert uc["em"] == ["sidecar-model"]


# ---------------------------------------------------------------------------
# _canonical_uc_to_legacy — empty list paths (lines 538, 546, 550, 554)
# ---------------------------------------------------------------------------


class TestCanonicalUcToLegacyEmptyLists:
    """Optional list fields (``mtype``, ``cimModels``, ``mitreAttack``,
    ``equipment``, ``equipmentModels``) — verify the empty-list paths
    that simply don't set the short-key (so default stays in place)."""

    def test_empty_monitoring_type_leaves_no_mtype_key(self):
        canonical = {"id": "1.1.1", "title": "T", "monitoringType": []}
        uc = parse_content._canonical_uc_to_legacy(canonical)
        # ``mtype`` should not be set when input list is empty.
        assert uc.get("mtype") is None or uc.get("mtype") == [] or "mtype" not in uc

    def test_empty_cim_models_leaves_no_a_key(self):
        canonical = {"id": "1.1.1", "title": "T", "cimModels": []}
        uc = parse_content._canonical_uc_to_legacy(canonical)
        assert uc.get("a") is None or uc.get("a") == [] or "a" not in uc

    def test_empty_mitre_leaves_default(self):
        canonical = {"id": "1.1.1", "title": "T", "mitreAttack": []}
        uc = parse_content._canonical_uc_to_legacy(canonical)
        # mitre default is [] from _legacy_default_uc.
        assert uc.get("mitre") == []

    def test_empty_equipment_leaves_no_e_key(self):
        canonical = {"id": "1.1.1", "title": "T", "equipment": []}
        uc = parse_content._canonical_uc_to_legacy(canonical)
        assert uc.get("e") is None or uc.get("e") == [] or "e" not in uc

    def test_empty_equipment_models_leaves_no_em_key(self):
        canonical = {"id": "1.1.1", "title": "T", "equipmentModels": []}
        uc = parse_content._canonical_uc_to_legacy(canonical)
        assert uc.get("em") is None or uc.get("em") == [] or "em" not in uc


# ---------------------------------------------------------------------------
# _load_facets — defensive when extract_filter_facets isn't present
# ---------------------------------------------------------------------------


class TestLoadFacets:
    def test_facets_loaded_when_helper_present(self):
        cat = parse_content.empty()
        cat.categories = [
            {"i": 1, "n": "C", "s": [{"i": "1.1", "n": "S", "u": []}]}
        ]
        # extract_filter_facets is present in enrichment by default.
        parse_content._load_facets(cat)
        assert isinstance(cat.facets, dict)

    def test_no_op_when_helper_missing(self, monkeypatch):
        # Line 1043: skip when extract_filter_facets isn't on enrichment.
        from build import enrichment as legacy

        # Remove the attribute temporarily.
        monkeypatch.delattr(legacy, "extract_filter_facets", raising=False)
        cat = parse_content.empty()
        parse_content._load_facets(cat)
        # No facets injected; default stays empty dict.
        assert cat.facets == {}


# ---------------------------------------------------------------------------
# Final coverage push — narrow remaining gaps
# ---------------------------------------------------------------------------


class TestPostProcessSidecarPathSkippedWhenComplete:
    """Line 711->723: when sidecar is None, ``e`` is set, AND ``em`` is
    NOT None (legacy fully-populated UC), neither re-derivation branch
    fires — the loop just falls through to apps_for_ta_string."""

    def test_sidecar_none_e_set_em_set_no_re_derivation(self, monkeypatch):
        from build import enrichment as legacy

        monkeypatch.setattr(
            legacy, "_sidecar_equipment_tags", lambda *a, **kw: (None, None)
        )

        # Mark as a tracker so we can assert it wasn't called.
        derive_calls = []

        def _track_derive(ta):
            derive_calls.append(ta)
            return (["WRONG"], ["WRONG"])

        monkeypatch.setattr(legacy, "equipment_ids_for_ta_string", _track_derive)

        record = {
            "i": 99,
            "n": "C",
            "s": [
                {
                    "i": "99.1",
                    "n": "S",
                    "u": [
                        {
                            "i": "99.1.1",
                            "n": "T",
                            "c": "high",
                            "f": "easy",
                            "v": "v",
                            "d": "d",
                            "t": "T",
                            "q": "s",
                            # Both e and em are present and not None
                            # → no re-derivation.
                            "e": ["existing"],
                            "em": ["existing-model"],
                        },
                    ],
                }
            ],
        }
        parse_content._post_process_category(record, legacy)
        # equipment_ids_for_ta_string MUST NOT be called (line 711->723).
        assert derive_calls == []
        uc = record["s"][0]["u"][0]
        assert uc["e"] == ["existing"]
        assert uc["em"] == ["existing-model"]


class TestComputeQualityGoldMissingFields:
    """Lines 847-854: when silver passes but gold_missing has entries
    (z or em missing), the gold-tier gap-list-extension branch fires."""

    def test_silver_passes_gold_fails_on_missing_em(self):
        # Long enough md, sections present, all silver fields set —
        # but ``em`` (gold-extra) missing.
        md = (
            "Step 0 prerequisite: install. "
            "Step 1 configure data collection. "
            "Step 2 understanding this SPL stage by stage. "
            "Step 3 validate outputs against the vendor portal. "
            "Step 5 operationalize. "
            + ("Detail body content here. " * 60)
        )
        uc = {
            "i": "1.1.1",
            "n": "T",
            "c": "high",
            "f": "easy",
            "q": "search",
            "v": "v",
            "d": "d",
            "t": "t",
            "m": "m",
            "mtype": ["Performance"],
            "md": md,
            "refs": "[A](https://a), [B](https://b)",
            "e": ["eq"],
            # ``em`` and ``z`` both missing → silver passes, gold fails.
            "ge": "Plain.",
            "wv": "crawl",
        }
        tier, depth, gaps = parse_content._compute_quality(uc)
        # Silver tier; gaps mention the gold-extras.
        assert tier == "silver"
        assert any("equipment models" in g for g in gaps)
        assert any("visualization guidance" in g for g in gaps)


class TestLoadRegulationsDictWithoutKnownKey:
    """Lines 1012-1018: dict regulations.json that has neither
    ``frameworks`` nor ``regulations`` keys → ``candidates`` stays
    empty, no entries loaded."""

    def test_dict_with_unknown_key_loads_nothing(self, tmp_path):
        (tmp_path / "data").mkdir()
        (tmp_path / "data" / "regulations.json").write_text(
            json.dumps({"unknown_key": [{"id": "X"}]}),
            encoding="utf-8",
        )
        cat = parse_content.empty(project_root=tmp_path)
        parse_content._load_regulations(cat, tmp_path)
        assert cat.regulations == {}

    def test_root_value_neither_dict_nor_list(self, tmp_path):
        # Line 1011-1018 + 1019: scalar root falls through to empty
        # candidates and the for-loop becomes a no-op.
        (tmp_path / "data").mkdir()
        (tmp_path / "data" / "regulations.json").write_text(
            json.dumps("just a string"),
            encoding="utf-8",
        )
        cat = parse_content.empty(project_root=tmp_path)
        parse_content._load_regulations(cat, tmp_path)
        assert cat.regulations == {}


class TestLoadCategoriesNoSlugBranch:
    """Line 297->318: ``if slug:`` partial — when slug is empty, neither
    cat.files append nor record["src"] set."""

    def test_meta_with_empty_slug_skips_files_and_src(self, tmp_path):
        content = tmp_path / "content"
        content.mkdir()
        d = content / "cat-99-test"
        d.mkdir()
        (d / "_category.json").write_text(
            # Note: explicit slug = "" (empty string is falsy).
            json.dumps({"id": 99, "name": "X", "slug": ""}),
            encoding="utf-8",
        )
        # Override `cat_dir.name` heuristic by leaving slug empty;
        # the loader falls back to ``cat_dir.name`` so the slug ends
        # up populated. To actually hit "if slug: false", we need
        # both slug="" AND cat_dir.name to be empty — which can't
        # happen on disk. Instead, this test verifies that the loader
        # doesn't crash with empty slug and that cat.files is non-empty
        # via the cat_dir.name fallback (line 296).
        cat = parse_content.empty(project_root=tmp_path)
        parse_content._load_categories_from_content(cat, tmp_path, reproducible=False)
        # cat.files SHOULD be populated via the cat_dir.name fallback.
        assert "cat-99-test" in cat.files
