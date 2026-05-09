"""Tests for ``tools/build/render_metrics.py`` — ``dist/metrics.json`` emitter.

Per repo-overhaul plan §P8 (observability), every build emits a
top-line catalogue health snapshot to ``dist/metrics.json``. This
module verifies the **invariants of that contract** so a future
schema bump or pipeline refactor cannot silently degrade what
trend-tracking dashboards consume:

* Pure helpers (``_percentile_block``, ``_nearest_rank``, ``_top_n``)
  produce the shapes the schema declares for empty + populated input.
* ``build_metrics()`` end-to-end against a synthetic 5-UC catalogue
  exercises every section (counts / quality / coverage / distributions
  / leaderboards) so renaming a short key in ``parse_content`` is
  caught here, not in production.
* The emitter is reproducible — two consecutive calls with
  ``reproducible=True`` return byte-identical JSON.
* The emitted artefact validates against
  ``schemas/v2/metrics.schema.json`` (both the synthetic catalogue
  *and* the real one parsed from ``content/``), guaranteeing wire-shape
  parity with the JSON Schema gate.
* Stage wiring: ``ALL_STAGES`` includes ``metrics`` and the ``--only``
  argparse choices follow.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TOOLS_DIR = str(REPO_ROOT / "tools")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from build import (  # noqa: E402
    parse_content,
    render_metrics,
)

SCHEMA_PATH = REPO_ROOT / "schemas" / "v2" / "metrics.schema.json"


# ---------------------------------------------------------------------------
# Pure helpers — _nearest_rank, _percentile_block, _top_n
# ---------------------------------------------------------------------------


def test_nearest_rank_handles_empty() -> None:
    assert render_metrics._nearest_rank([], 50) == 0
    assert render_metrics._nearest_rank([], 99) == 0


def test_nearest_rank_single_value() -> None:
    assert render_metrics._nearest_rank([42], 50) == 42
    assert render_metrics._nearest_rank([42], 99) == 42


def test_nearest_rank_canonical_dataset() -> None:
    """For 1..10 the nearest-rank percentiles have well-known values."""
    values = list(range(1, 11))
    assert render_metrics._nearest_rank(values, 50) == 5
    assert render_metrics._nearest_rank(values, 90) == 9
    assert render_metrics._nearest_rank(values, 99) == 10


def test_percentile_block_empty_returns_zeros() -> None:
    block = render_metrics._percentile_block([])
    assert block == {
        "count": 0,
        "min": 0,
        "max": 0,
        "mean": 0.0,
        "p50": 0,
        "p90": 0,
        "p99": 0,
    }


def test_percentile_block_populated_uniform() -> None:
    block = render_metrics._percentile_block([10, 20, 30, 40, 50])
    assert block["count"] == 5
    assert block["min"] == 10
    assert block["max"] == 50
    assert block["mean"] == 30.0
    assert block["p50"] == 30
    assert block["p90"] == 50
    assert block["p99"] == 50


def test_percentile_block_handles_unsorted_input() -> None:
    """The helper sorts internally — caller is not required to."""
    block = render_metrics._percentile_block([50, 10, 30, 20, 40])
    assert block["min"] == 10
    assert block["max"] == 50


def test_top_n_orders_by_count_then_alphabetical() -> None:
    from collections import Counter
    c = Counter({"alpha": 5, "beta": 5, "gamma": 3, "delta": 7})
    out = render_metrics._top_n(c, 10, "id")
    assert out == [
        {"id": "delta", "count": 7},
        {"id": "alpha", "count": 5},
        {"id": "beta", "count": 5},
        {"id": "gamma", "count": 3},
    ]


def test_top_n_caps_to_n() -> None:
    from collections import Counter
    c = Counter({chr(i): i for i in range(ord("a"), ord("a") + 15)})
    out = render_metrics._top_n(c, 3, "key")
    assert len(out) == 3
    assert [row["key"] for row in out] == ["o", "n", "m"]


# ---------------------------------------------------------------------------
# Synthetic Catalog → build_metrics()
# ---------------------------------------------------------------------------


def _synthetic_catalog(project_root: Path) -> parse_content.Catalog:
    """A 5-UC catalogue exercising every code path the emitter has.

    Two categories, three subcategories, five UCs covering:

    * All four quality tiers (gold / silver / bronze / none)
    * Two distinct waves (crawl, walk; run absent — verifies zero-fill)
    * Two distinct criticalities (high / medium)
    * Two distinct difficulties (beginner / advanced)
    * GE-present (4) vs GE-empty (1)
    * Compliance regulations: gdpr/hipaa/pci-dss with deliberate ties
    * MITRE techniques + CIM models + equipment to trigger leaderboards
    * ESCU / ESCU-RBA flags

    The literal vocabularies for criticality and difficulty mirror
    ``schemas/uc.schema.json`` (and ``tools/build/models.CatalogUC``)
    so static type checking catches drift here, not in production.
    """
    return parse_content.Catalog(
        project_root=project_root,
        categories=[
            {
                "i": 1,
                "n": "Server",
                "s": [
                    {
                        "i": "1.1",
                        "n": "Linux",
                        "u": [
                            {
                                "i": "1.1.1",
                                "n": "Disk full",
                                "_qt": "gold",
                                "_qs": 80,
                                "wv": "crawl",
                                "c": "high",
                                "f": "beginner",
                                "ge": "We watch when disks fill up.",
                                "regs": ["gdpr", "hipaa"],
                                "mitre": ["T1190"],
                                "a": ["Performance"],
                                "e": ["splunk_ta_nix"],
                                "pre": ["UC-1.1.0"],
                            },
                            {
                                "i": "1.1.2",
                                "n": "CPU steal",
                                "_qt": "silver",
                                "_qs": 55,
                                "wv": "walk",
                                "c": "medium",
                                "f": "advanced",
                                "ge": "We watch CPU borrowed by other tenants.",
                                "regs": ["gdpr"],
                                "a": ["Performance"],
                                "e": ["splunk_ta_nix"],
                                "escu": True,
                            },
                        ],
                    },
                    {
                        "i": "1.2",
                        "n": "Windows",
                        "u": [
                            {
                                "i": "1.2.1",
                                "n": "Service crash",
                                "_qt": "bronze",
                                "_qs": 30,
                                "c": "high",
                                "f": "beginner",
                                "ge": "We watch services dying.",
                                "regs": ["pci-dss", "gdpr"],
                                "mitre": ["T1190", "T1078"],
                                "a": ["Endpoint"],
                                "e": ["splunk_ta_windows"],
                                "escu": True,
                                "escu_rba": True,
                            },
                        ],
                    },
                ],
            },
            {
                "i": 2,
                "n": "Network",
                "s": [
                    {
                        "i": "2.1",
                        "n": "DNS",
                        "u": [
                            {
                                "i": "2.1.1",
                                "n": "DNS spike",
                                "_qt": "none",
                                "_qs": 0,
                                "c": "medium",
                                "f": "advanced",
                                "ge": "",
                                "a": ["Network_Resolution"],
                            },
                            {
                                "i": "2.1.2",
                                "n": "DNS NXDOMAIN",
                                "_qt": "silver",
                                "_qs": 60,
                                "wv": "crawl",
                                "c": "high",
                                "f": "advanced",
                                "ge": "We watch broken DNS lookups.",
                                "mitre": ["T1190"],
                                "a": ["Network_Resolution"],
                            },
                        ],
                    },
                ],
            },
        ],
        regulations={"gdpr": {"id": "gdpr"}, "hipaa": {"id": "hipaa"}, "pci-dss": {"id": "pci-dss"}},
        equipment=[{"id": "splunk_ta_nix"}, {"id": "splunk_ta_windows"}],
    )


@pytest.fixture
def synthetic_catalog(tmp_path: Path) -> parse_content.Catalog:
    return _synthetic_catalog(tmp_path)


def test_build_metrics_counts(synthetic_catalog: parse_content.Catalog) -> None:
    m = render_metrics.build_metrics(synthetic_catalog, reproducible=True)
    assert m["counts"] == {
        "categories": 2,
        "subcategories": 3,
        "useCases": 5,
        "regulations": 3,
        "equipment": 2,
    }


def test_build_metrics_quality_tiers(synthetic_catalog: parse_content.Catalog) -> None:
    m = render_metrics.build_metrics(synthetic_catalog, reproducible=True)
    assert m["quality"]["tierCounts"] == {
        "gold": 1,
        "silver": 2,
        "bronze": 1,
        "none": 1,
    }
    pct = m["quality"]["tierPercentages"]
    assert pct["gold"] == 20.0
    assert pct["silver"] == 40.0
    assert pct["bronze"] == 20.0
    assert pct["none"] == 20.0


def test_build_metrics_depth_percentiles(synthetic_catalog: parse_content.Catalog) -> None:
    m = render_metrics.build_metrics(synthetic_catalog, reproducible=True)
    depth = m["quality"]["depthScore"]
    assert depth["count"] == 5
    assert depth["min"] == 0
    assert depth["max"] == 80
    assert depth["mean"] == 45.0  # (0+30+55+60+80)/5
    assert depth["p50"] == 55  # nearest-rank: ceil(.5*5)=3 -> 3rd value of [0,30,55,60,80]


def test_build_metrics_grandma_explanation(synthetic_catalog: parse_content.Catalog) -> None:
    m = render_metrics.build_metrics(synthetic_catalog, reproducible=True)
    ge = m["quality"]["grandmaExplanation"]
    assert ge["presentCount"] == 4
    assert ge["presentPercentage"] == 80.0
    assert ge["characterLength"]["count"] == 4
    assert ge["characterLength"]["min"] > 0


def test_build_metrics_coverage(synthetic_catalog: parse_content.Catalog) -> None:
    m = render_metrics.build_metrics(synthetic_catalog, reproducible=True)
    cov = m["coverage"]
    assert cov["compliance"] == {"count": 3, "percentage": 60.0}
    assert cov["mitreAttack"] == {"count": 3, "percentage": 60.0}
    assert cov["cimModels"] == {"count": 5, "percentage": 100.0}
    assert cov["equipment"] == {"count": 3, "percentage": 60.0}
    assert cov["prerequisites"] == {"count": 1, "percentage": 20.0}
    assert cov["escuDetections"] == {"count": 2, "percentage": 40.0}
    assert cov["escuRiskBased"] == {"count": 1, "percentage": 20.0}


def test_build_metrics_distributions(synthetic_catalog: parse_content.Catalog) -> None:
    m = render_metrics.build_metrics(synthetic_catalog, reproducible=True)
    assert m["distributions"]["wave"] == {"crawl": 2, "walk": 1, "run": 0}
    assert m["distributions"]["criticality"] == {"high": 3, "medium": 2}
    assert m["distributions"]["difficulty"] == {"advanced": 3, "beginner": 2}


def test_build_metrics_ucs_by_category(synthetic_catalog: parse_content.Catalog) -> None:
    m = render_metrics.build_metrics(synthetic_catalog, reproducible=True)
    assert m["ucsByCategory"] == {"1": 3, "2": 2}


def test_build_metrics_leaders(synthetic_catalog: parse_content.Catalog) -> None:
    m = render_metrics.build_metrics(synthetic_catalog, reproducible=True)
    leaders = m["leaders"]
    # gdpr appears 3 times, pci-dss 1, hipaa 1; ties broken alphabetically.
    assert leaders["regulations"][0] == {"regulation": "gdpr", "count": 3}
    assert sorted(
        [(row["regulation"], row["count"]) for row in leaders["regulations"]]
    ) == [("gdpr", 3), ("hipaa", 1), ("pci-dss", 1)]
    # T1190 wins MITRE (3), T1078 trails (1)
    assert leaders["mitreAttack"][0] == {"technique": "T1190", "count": 3}


def test_build_metrics_top_level_keys(synthetic_catalog: parse_content.Catalog) -> None:
    """All schema-required top-level keys are present."""
    m = render_metrics.build_metrics(synthetic_catalog, reproducible=True)
    expected = {
        "$schema",
        "schema_version",
        "generatedAt",
        "catalogueVersion",
        "build",
        "counts",
        "quality",
        "coverage",
        "distributions",
        "ucsByCategory",
        "leaders",
    }
    assert set(m.keys()) == expected


# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------


def test_build_metrics_reproducible_is_byte_identical(
    synthetic_catalog: parse_content.Catalog,
) -> None:
    """Two consecutive --reproducible calls return identical JSON bytes."""
    a = render_metrics.build_metrics(synthetic_catalog, reproducible=True)
    b = render_metrics.build_metrics(synthetic_catalog, reproducible=True)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_render_writes_reproducible_file(
    synthetic_catalog: parse_content.Catalog, tmp_path: Path
) -> None:
    """`render()` emits to dist/metrics.json deterministically."""
    out_a = tmp_path / "dist-a"
    out_b = tmp_path / "dist-b"
    p1 = render_metrics.render(synthetic_catalog, out_a, reproducible=True)
    p2 = render_metrics.render(synthetic_catalog, out_b, reproducible=True)
    assert p1.name == p2.name == "metrics.json"
    assert p1.read_bytes() == p2.read_bytes()


def test_render_creates_out_dir_if_missing(
    synthetic_catalog: parse_content.Catalog, tmp_path: Path
) -> None:
    out = tmp_path / "does" / "not" / "exist"
    p = render_metrics.render(synthetic_catalog, out, reproducible=True)
    assert p.exists()


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------


def test_schema_is_valid_json_schema_2020_12() -> None:
    with SCHEMA_PATH.open(encoding="utf-8") as f:
        schema = json.load(f)
    jsonschema.Draft202012Validator.check_schema(schema)


def test_synthetic_metrics_validates_against_schema(
    synthetic_catalog: parse_content.Catalog,
) -> None:
    with SCHEMA_PATH.open(encoding="utf-8") as f:
        schema = json.load(f)
    m = render_metrics.build_metrics(synthetic_catalog, reproducible=True)
    jsonschema.Draft202012Validator(schema).validate(m)


def test_real_catalog_metrics_validates_against_schema() -> None:
    """The full live catalogue metrics must validate, not just synthetic."""
    catalog = parse_content.load(REPO_ROOT)
    with SCHEMA_PATH.open(encoding="utf-8") as f:
        schema = json.load(f)
    m = render_metrics.build_metrics(catalog, reproducible=True)
    jsonschema.Draft202012Validator(schema).validate(m)
    # Sanity: live catalog has thousands of UCs.
    assert m["counts"]["useCases"] > 1000
    assert m["counts"]["categories"] > 5


# ---------------------------------------------------------------------------
# Build-pipeline wiring
# ---------------------------------------------------------------------------


def test_metrics_stage_wired_into_build_py() -> None:
    """`metrics` is in ALL_STAGES so `--only metrics` works."""
    from build import build as build_module
    assert "metrics" in build_module.ALL_STAGES
    # Stage should be last so it always sees the freshly-parsed catalogue.
    assert build_module.ALL_STAGES[-1] == "metrics"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_empty_catalog_returns_zero_filled_payload(tmp_path: Path) -> None:
    """An empty catalogue still emits a valid, fully-zeroed payload.

    Important so the first build of a fork doesn't crash and the
    schema gate stays meaningful even for edge cases.
    """
    empty = parse_content.empty(tmp_path)
    m = render_metrics.build_metrics(empty, reproducible=True)
    assert m["counts"]["useCases"] == 0
    assert m["quality"]["tierCounts"]["gold"] == 0
    assert m["quality"]["depthScore"]["count"] == 0
    # Schema must still validate.
    with SCHEMA_PATH.open(encoding="utf-8") as f:
        schema = json.load(f)
    jsonschema.Draft202012Validator(schema).validate(m)


def test_unknown_quality_tier_is_collapsed_to_none() -> None:
    """A UC with a stray ``_qt`` value falls into the ``none`` bucket.

    Defends against schema drift in ``parse_content`` if the tier
    vocabulary ever expands without a corresponding update here.
    """
    project_root = Path("/tmp")
    cat = parse_content.Catalog(
        project_root=project_root,
        categories=[
            {
                "i": 1,
                "n": "X",
                "s": [
                    {
                        "i": "1.1",
                        "n": "Y",
                        "u": [
                            {"i": "1.1.1", "n": "Z", "_qt": "platinum"},
                        ],
                    }
                ],
            }
        ],
    )
    m = render_metrics.build_metrics(cat, reproducible=True)
    assert m["quality"]["tierCounts"]["none"] == 1


def test_invalid_wave_value_is_dropped(tmp_path: Path) -> None:
    """A non-vocabulary wave string does not increment any bucket.

    Defends the emitter against drift in upstream content (e.g. a
    typoed wave value sneaking past schema validation). The
    ``type: ignore[typeddict-item]`` is intentional: this test
    exercises the runtime fallback path for an off-vocabulary value.
    """
    cat = parse_content.Catalog(
        project_root=tmp_path,
        categories=[
            {
                "i": 1,
                "n": "X",
                "s": [
                    {
                        "i": "1.1",
                        "n": "Y",
                        "u": [{"i": "1.1.1", "n": "Z", "wv": "stampede"}],  # type: ignore[typeddict-item]
                    }
                ],
            }
        ],
    )
    m = render_metrics.build_metrics(cat, reproducible=True)
    assert m["distributions"]["wave"] == {"crawl": 0, "walk": 0, "run": 0}


def test_empty_string_criticality_difficulty_dropped(tmp_path: Path) -> None:
    """Empty strings in criticality/difficulty don't pollute the histograms.

    Same rationale as ``test_invalid_wave_value_is_dropped``: empty
    strings violate the TypedDict literal vocabulary on purpose to
    exercise the runtime sanitiser that drops them.
    """
    cat = parse_content.Catalog(
        project_root=tmp_path,
        categories=[
            {
                "i": 1,
                "n": "X",
                "s": [
                    {
                        "i": "1.1",
                        "n": "Y",
                        "u": [{"i": "1.1.1", "n": "Z", "c": "", "f": ""}],  # type: ignore[typeddict-item]
                    }
                ],
            }
        ],
    )
    m = render_metrics.build_metrics(cat, reproducible=True)
    assert m["distributions"]["criticality"] == {}
    assert m["distributions"]["difficulty"] == {}


# ---------------------------------------------------------------------------
# Schema cross-references
# ---------------------------------------------------------------------------


def test_schema_version_matches_emitter_constant() -> None:
    """The constant in render_metrics.py and the schema's ``version`` agree."""
    with SCHEMA_PATH.open(encoding="utf-8") as f:
        schema = json.load(f)
    assert schema["version"] == render_metrics.SCHEMA_VERSION


def test_schema_id_matches_emitter_ref() -> None:
    """The emitted ``$schema`` field points at the on-disk schema."""
    with SCHEMA_PATH.open(encoding="utf-8") as f:
        schema = json.load(f)
    assert render_metrics.SCHEMA_REF.endswith("metrics.schema.json")
    assert schema["$id"].endswith(render_metrics.SCHEMA_REF.lstrip("/"))


def test_top_n_caps_match_schema_max_items() -> None:
    """If we lift _TOP_N_*, the schema ``maxItems`` must follow."""
    with SCHEMA_PATH.open(encoding="utf-8") as f:
        schema = json.load(f)
    leaders_props = schema["properties"]["leaders"]["properties"]
    assert leaders_props["regulations"]["maxItems"] >= render_metrics._TOP_N_REGULATIONS
    assert leaders_props["mitreAttack"]["maxItems"] >= render_metrics._TOP_N_MITRE
    assert leaders_props["cimModels"]["maxItems"] >= render_metrics._TOP_N_CIM
    assert leaders_props["equipment"]["maxItems"] >= render_metrics._TOP_N_EQUIPMENT


# ---------------------------------------------------------------------------
# Determinism: sort-key behaviour (defends against Python dict order regressions)
# ---------------------------------------------------------------------------


def test_emitted_json_is_sort_key_stable(
    synthetic_catalog: parse_content.Catalog, tmp_path: Path
) -> None:
    """The committed wire format uses sort_keys=True; flipping insertion order
    in `build_metrics()` must not change the bytes."""
    p = render_metrics.render(synthetic_catalog, tmp_path, reproducible=True)
    text = p.read_text(encoding="utf-8")
    parsed: dict[str, Any] = json.loads(text)
    re_emitted = json.dumps(parsed, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    assert text == re_emitted
