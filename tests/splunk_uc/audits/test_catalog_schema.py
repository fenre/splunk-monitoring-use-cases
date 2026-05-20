"""Unit tests for ``audit-catalog-schema`` (P16 wave E).

The audit validates the top-level structure of ``catalog.json`` \u2014
the machine-readable artefact every downstream consumer (MCP
server, JSON API, frontend, RAG corpus) depends on. Until now the
module had **zero unit-test coverage** despite owning ~25 distinct
validation branches; this file pins every one.

The strategy is the standard "table per branch" approach: build a
minimum-viable correct catalog as a JSON fixture, then for each
invariant write one test that mutates the fixture *just enough* to
trigger that specific branch and asserts the corresponding error
message lands in the audit's stderr.

We exercise ``main(argv)`` through ``capsys`` so the same path CI
runs is the path the tests exercise. ``monkeypatch.setattr`` swaps
the module-level ``CATALOG_PATH`` to a tmp-file the tests own,
keeping every test hermetic.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from splunk_uc.audits import catalog_schema

# ----------------------------------------------------------------------
# Fixture: a minimum-viable correct catalog
# ----------------------------------------------------------------------


def _good_catalog() -> dict[str, Any]:
    """Return a fresh deep copy of a minimum-viable correct catalog.

    Returning a *deep copy* per call so tests can mutate the result
    freely without bleeding state between cases.
    """
    return copy.deepcopy(
        {
            "_schema_url": "https://example.test/schema.json",
            "_readme": "Stub catalog for tests.",
            "DATA": [
                {
                    "i": 1,
                    "n": "Infrastructure",
                    "s": [
                        {
                            "i": "1.1",
                            "n": "Compute",
                            "u": [
                                {
                                    "i": "1.1.1",
                                    "n": "CPU Utilization",
                                    "c": "high",
                                    "f": "easy",
                                },
                                {
                                    "i": "1.1.2",
                                    "n": "Memory Pressure",
                                    "c": "medium",
                                    "f": "medium",
                                    "wv": "walk",
                                    "pre": ["UC-1.1.1"],
                                },
                            ],
                        }
                    ],
                }
            ],
            "CAT_META": {"1": {"slug": "infra"}},
            "CAT_GROUPS": {"All": ["1"]},
            "EQUIPMENT": [],
            "implementationRoadmap": {
                "1": {
                    "crawl": ["UC-1.1.1"],
                    "walk": ["UC-1.1.2"],
                    "run": [],
                    "unassigned": [],
                }
            },
        }
    )


def _write_catalog(
    tmp_path: Path,
    catalog: dict[str, Any] | list[Any] | str | None,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    """Serialise *catalog* to a tmp file and patch the audit to read it."""
    path = tmp_path / "catalog.json"
    if isinstance(catalog, str):
        path.write_text(catalog, encoding="utf-8")
    else:
        path.write_text(json.dumps(catalog), encoding="utf-8")
    monkeypatch.setattr(catalog_schema, "CATALOG_PATH", str(path))
    return path


def _run(
    tmp_path: Path,
    catalog: dict[str, Any] | list[Any] | str | None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> tuple[int, str, str]:
    """Common helper: write catalog, invoke main(), return (rc, stdout, stderr)."""
    _write_catalog(tmp_path, catalog, monkeypatch)
    rc = catalog_schema.main([])
    captured = capsys.readouterr()
    return rc, captured.out, captured.err


# ----------------------------------------------------------------------
# Tiny purity tests for is_int / is_str / err helpers
# ----------------------------------------------------------------------


def test_is_int_rejects_bool() -> None:
    """Python booleans inherit from int; ``type(x) is int`` rejects them."""
    assert catalog_schema.is_int(1) is True
    assert catalog_schema.is_int(True) is False
    assert catalog_schema.is_int(1.0) is False
    assert catalog_schema.is_int("1") is False


def test_is_str_only_accepts_str() -> None:
    assert catalog_schema.is_str("a") is True
    assert catalog_schema.is_str(b"a") is False
    assert catalog_schema.is_str(None) is False


def test_err_appends_to_list() -> None:
    issues: list[str] = []
    catalog_schema.err(issues, "boom")
    catalog_schema.err(issues, "again")
    assert issues == ["boom", "again"]


# ----------------------------------------------------------------------
# Happy path
# ----------------------------------------------------------------------


def test_main_passes_on_minimum_viable_catalog(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc, out, err = _run(tmp_path, _good_catalog(), monkeypatch, capsys)
    assert rc == 0, err
    assert "catalog.json schema OK" in out
    assert "Categories:" in out
    assert "Use cases:" in out


def test_main_counts_categories_subcategories_and_ucs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Counts in stdout reflect the catalog's actual shape."""
    cat = _good_catalog()
    # Add another subcategory + UC
    cat["DATA"][0]["s"].append(
        {
            "i": "1.2",
            "n": "Networking",
            "u": [
                {"i": "1.2.1", "n": "Latency", "c": "low", "f": "easy"},
            ],
        }
    )
    rc, out, _ = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 0
    assert "Categories:     1" in out
    assert "Subcategories: 2" in out
    assert "Use cases:     3" in out


def test_main_passes_with_no_implementation_roadmap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``implementationRoadmap`` is optional \u2014 absence is fine."""
    cat = _good_catalog()
    del cat["implementationRoadmap"]
    rc, _, _ = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 0


# ----------------------------------------------------------------------
# File / JSON loading
# ----------------------------------------------------------------------


def test_main_returns_1_when_catalog_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        catalog_schema, "CATALOG_PATH", str(tmp_path / "nope.json")
    )
    rc = catalog_schema.main([])
    captured = capsys.readouterr()
    assert rc == 1
    assert "catalog not found" in captured.err


def test_main_returns_1_on_invalid_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc, _, err = _run(tmp_path, "{ not valid json", monkeypatch, capsys)
    assert rc == 1
    assert "invalid JSON" in err


def test_main_returns_1_when_root_is_list(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Top-level JSON must be an object, not an array."""
    rc, _, err = _run(tmp_path, [1, 2, 3], monkeypatch, capsys)
    assert rc == 1
    assert "Root JSON value must be an object" in err


# ----------------------------------------------------------------------
# Required top-level keys
# ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "missing_key",
    ["_schema_url", "_readme", "DATA", "CAT_META", "CAT_GROUPS", "EQUIPMENT"],
)
def test_main_flags_missing_top_level_keys(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    missing_key: str,
) -> None:
    cat = _good_catalog()
    del cat[missing_key]
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert f"Missing top-level key: {missing_key!r}" in err


# ----------------------------------------------------------------------
# Top-level type checks
# ----------------------------------------------------------------------


def test_main_flags_data_not_a_list(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cat = _good_catalog()
    cat["DATA"] = {"not": "a list"}
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "DATA must be a list" in err


def test_main_flags_cat_meta_not_a_dict(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cat = _good_catalog()
    cat["CAT_META"] = ["not a dict"]
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "CAT_META must be a dict" in err


def test_main_flags_cat_meta_non_numeric_keys(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """CAT_META keys must be numeric strings (one per category id)."""
    cat = _good_catalog()
    cat["CAT_META"]["bogus"] = {"slug": "x"}
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "invalid key" in err
    assert "bogus" in err


def test_main_flags_cat_groups_not_a_dict(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cat = _good_catalog()
    cat["CAT_GROUPS"] = ["nope"]
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "CAT_GROUPS must be a dict" in err


def test_main_flags_equipment_not_a_list(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cat = _good_catalog()
    cat["EQUIPMENT"] = {"not": "a list"}
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "EQUIPMENT must be a list" in err


# ----------------------------------------------------------------------
# DATA[ci] (category) validation
# ----------------------------------------------------------------------


def test_main_flags_category_not_an_object(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cat = _good_catalog()
    cat["DATA"].append("not an object")
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "category entry must be an object" in err


def test_main_flags_missing_category_id(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cat = _good_catalog()
    del cat["DATA"][0]["i"]
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "missing required key 'i'" in err


def test_main_flags_category_id_wrong_type(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cat = _good_catalog()
    cat["DATA"][0]["i"] = "1"  # str instead of int
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "'i' must be int" in err


def test_main_flags_missing_category_name(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cat = _good_catalog()
    del cat["DATA"][0]["n"]
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "missing required key 'n'" in err


def test_main_flags_category_name_wrong_type(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cat = _good_catalog()
    cat["DATA"][0]["n"] = 42
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "'n' must be str" in err


def test_main_flags_missing_subcategories_list(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cat = _good_catalog()
    del cat["DATA"][0]["s"]
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "missing required key 's'" in err


def test_main_flags_subcategories_not_a_list(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cat = _good_catalog()
    cat["DATA"][0]["s"] = "not a list"
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "'s' must be a list" in err


def test_main_flags_top_level_u_on_category(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``u`` belongs under each subcategory, not on the category itself."""
    cat = _good_catalog()
    cat["DATA"][0]["u"] = []
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "unexpected top-level 'u' on category" in err


# ----------------------------------------------------------------------
# Subcategory validation
# ----------------------------------------------------------------------


def test_main_flags_subcategory_not_an_object(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cat = _good_catalog()
    cat["DATA"][0]["s"].append("not an object")
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "subcategory must be an object" in err


def test_main_flags_missing_subcategory_id(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cat = _good_catalog()
    del cat["DATA"][0]["s"][0]["i"]
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "missing required key 'i'" in err


def test_main_flags_subcategory_id_wrong_type(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cat = _good_catalog()
    cat["DATA"][0]["s"][0]["i"] = 11  # int instead of str
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "'i' must be str" in err


def test_main_flags_subcategory_name_wrong_type(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cat = _good_catalog()
    cat["DATA"][0]["s"][0]["n"] = ["not", "a", "string"]
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "'n' must be str" in err


def test_main_flags_missing_subcategory_ucs_list(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cat = _good_catalog()
    del cat["DATA"][0]["s"][0]["u"]
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "missing required key 'u'" in err


def test_main_flags_subcategory_ucs_not_a_list(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cat = _good_catalog()
    cat["DATA"][0]["s"][0]["u"] = {"not": "a list"}
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "'u' must be a list" in err


# ----------------------------------------------------------------------
# Use-case validation
# ----------------------------------------------------------------------


def test_main_flags_uc_not_an_object(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cat = _good_catalog()
    cat["DATA"][0]["s"][0]["u"].append("not an object")
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "use case must be an object" in err


@pytest.mark.parametrize("required_key", ["i", "n", "c", "f"])
def test_main_flags_missing_required_uc_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    required_key: str,
) -> None:
    cat = _good_catalog()
    del cat["DATA"][0]["s"][0]["u"][0][required_key]
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert f"missing required key {required_key!r}" in err


def test_main_flags_uc_id_wrong_type(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cat = _good_catalog()
    cat["DATA"][0]["s"][0]["u"][0]["i"] = 111
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "'i' must be str" in err


def test_main_flags_uc_id_malformed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """UC id must match ``\\d+\\.\\d+\\.\\d+``."""
    cat = _good_catalog()
    cat["DATA"][0]["s"][0]["u"][0]["i"] = "UC-1.1.1"  # prefix not allowed
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "must match pattern" in err


@pytest.mark.parametrize("non_id_required_key", ["n", "c", "f"])
def test_main_flags_uc_text_field_wrong_type(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    non_id_required_key: str,
) -> None:
    """``n``/``c``/``f`` must be strings."""
    cat = _good_catalog()
    cat["DATA"][0]["s"][0]["u"][0][non_id_required_key] = 999
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert f"{non_id_required_key!r} must be str" in err


# ----------------------------------------------------------------------
# Optional wave (`wv`) field
# ----------------------------------------------------------------------


def test_main_flags_wv_wrong_type(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cat = _good_catalog()
    cat["DATA"][0]["s"][0]["u"][1]["wv"] = 1
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "'wv' must be str" in err


def test_main_flags_wv_unknown_value(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cat = _good_catalog()
    cat["DATA"][0]["s"][0]["u"][1]["wv"] = "sprint"  # not crawl/walk/run
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "'wv' must be one of" in err
    assert "sprint" in err


# ----------------------------------------------------------------------
# Optional prerequisites (`pre`) field
# ----------------------------------------------------------------------


def test_main_flags_pre_wrong_type(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cat = _good_catalog()
    cat["DATA"][0]["s"][0]["u"][1]["pre"] = "UC-1.1.1"
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "'pre' must be a list" in err


def test_main_flags_pre_entry_wrong_type(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cat = _good_catalog()
    cat["DATA"][0]["s"][0]["u"][1]["pre"] = [123]
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "'pre[0]' must be str" in err


def test_main_flags_pre_entry_malformed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cat = _good_catalog()
    cat["DATA"][0]["s"][0]["u"][1]["pre"] = ["1.1.1"]  # missing UC- prefix
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "must match" in err


def test_main_flags_pre_self_reference(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cat = _good_catalog()
    cat["DATA"][0]["s"][0]["u"][1]["pre"] = ["UC-1.1.2"]
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "self-references" in err


def test_main_flags_pre_duplicate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cat = _good_catalog()
    cat["DATA"][0]["s"][0]["u"][1]["pre"] = ["UC-1.1.1", "UC-1.1.1"]
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "duplicate entry" in err


# ----------------------------------------------------------------------
# CAT_META \u2194 DATA consistency
# ----------------------------------------------------------------------


def test_main_flags_cat_meta_missing_for_category(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cat = _good_catalog()
    cat["CAT_META"].pop("1")
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "CAT_META missing entries for category id(s)" in err
    assert "1" in err


def test_main_flags_cat_meta_extra_keys(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cat = _good_catalog()
    cat["CAT_META"]["999"] = {"slug": "ghost"}
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "CAT_META has keys not present in DATA" in err
    assert "999" in err


# ----------------------------------------------------------------------
# Optional implementationRoadmap
# ----------------------------------------------------------------------


def test_main_flags_roadmap_not_a_dict(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cat = _good_catalog()
    cat["implementationRoadmap"] = []
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "implementationRoadmap must be a dict" in err


def test_main_flags_roadmap_non_numeric_category_id(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cat = _good_catalog()
    cat["implementationRoadmap"]["alpha"] = {"crawl": [], "walk": [], "run": [], "unassigned": []}
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "category id must be a numeric string" in err


def test_main_flags_roadmap_wave_map_not_dict(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cat = _good_catalog()
    cat["implementationRoadmap"]["1"] = "not a dict"
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "value must be a dict" in err


def test_main_flags_roadmap_unknown_wave_bucket(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cat = _good_catalog()
    cat["implementationRoadmap"]["1"]["fly"] = []
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "unknown wave bucket(s)" in err
    assert "fly" in err


def test_main_flags_roadmap_wave_bucket_not_a_list(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cat = _good_catalog()
    cat["implementationRoadmap"]["1"]["crawl"] = "not a list"
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "wave bucket must be a list" in err


def test_main_flags_roadmap_uc_entry_wrong_type(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cat = _good_catalog()
    cat["implementationRoadmap"]["1"]["crawl"] = [123]
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "must be str" in err


def test_main_flags_roadmap_uc_entry_malformed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cat = _good_catalog()
    cat["implementationRoadmap"]["1"]["crawl"] = ["1.1.1"]
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "must match pattern" in err


# ----------------------------------------------------------------------
# Missed-branch coverage: subcategory name, partial roadmap, junk diff
# ----------------------------------------------------------------------


def test_main_flags_missing_subcategory_name(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cat = _good_catalog()
    del cat["DATA"][0]["s"][0]["n"]
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    assert "missing required key 'n'" in err


def test_main_accepts_partial_roadmap_wave_map(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Roadmap wave-maps may omit canonical buckets; absence is fine."""
    cat = _good_catalog()
    # Drop the ``walk`` key entirely \u2014 the auditor must just skip it.
    del cat["implementationRoadmap"]["1"]["walk"]
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 0, err


def test_main_does_not_crash_on_cat_meta_with_junk_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Regression: ``CAT_META`` keys flagged as non-numeric were sorted
    by ``int()`` afterwards, which crashed with ``ValueError`` on
    catalogs that legitimately contained junk keys. The fix filters
    those keys out of the diff-set so the sort can never explode.
    """
    cat = _good_catalog()
    cat["CAT_META"]["bogus"] = {"slug": "x"}
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    # Both messages present: per-key invalid-format and no crash.
    assert "invalid key" in err
    assert "bogus" in err
    # The crash signature \u2014 absence proves the fix.
    assert "ValueError" not in err


# ----------------------------------------------------------------------
# Multiple errors accumulate (issues list shape)
# ----------------------------------------------------------------------


def test_main_accumulates_multiple_issues(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Auditor walks the full tree even when early errors occur."""
    cat = _good_catalog()
    del cat["_schema_url"]
    cat["DATA"][0]["s"][0]["u"][0]["i"] = "BADID"
    cat["EQUIPMENT"] = {}
    rc, _, err = _run(tmp_path, cat, monkeypatch, capsys)
    assert rc == 1
    # At least three distinct error messages
    assert "Missing top-level key: '_schema_url'" in err
    assert "EQUIPMENT must be a list" in err
    assert "must match pattern" in err
