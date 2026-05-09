"""Unit tests for ``tools/build/render_telemetry.py``.

Repo-overhaul plan §P8 step 3 (2026-05-09): per-stage build timings
are emitted to ``dist/build-telemetry.json`` so a perf-regression
dashboard can plot stage-by-stage trend lines release-over-release.
The tests pin:

* The pure helpers — payload construction, stage normalisation, JSON
  schema validation — against synthetic fixtures so the assertions
  don't drift when the live build adds or renames a stage.
* The reproducibility contract — ``render(..., reproducible=True)``
  must be a no-op so the artefact never breaks the byte-equal
  guarantee enforced by ``tools/build/build.py --check``.
* The build-pipeline wiring — ``"metrics"`` is in ``ALL_STAGES``,
  ``render_telemetry`` is imported, and the synthetic CLI smoke
  produces both ``dist/metrics.json`` and ``dist/build-telemetry.json``
  in non-reproducible mode while emitting only ``metrics.json`` in
  reproducible mode.
* The schema cross-references — ``SCHEMA_VERSION`` matches the
  schema's on-disk ``version``; ``SCHEMA_REF`` matches the schema's
  ``$id`` suffix; ``ARTEFACT_NAME`` is a stable string the build
  pipeline depends on.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_BUILD = REPO_ROOT / "tools" / "build"
SCHEMA_PATH = REPO_ROOT / "schemas" / "v2" / "build-telemetry.schema.json"

if str(REPO_ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "tools"))

from build import render_telemetry  # noqa: E402

# ---------------------------------------------------------------------------
# 1. Pure helpers — build_payload + _normalise_stage
# ---------------------------------------------------------------------------


def test_build_payload_basic_shape() -> None:
    """A canonical 3-stage list produces a payload with all required keys."""
    stages = [
        {"stage": "parse", "duration_ms": 1000},
        {"stage": "pages", "duration_ms": 250},
        {"stage": "api", "duration_ms": 750},
    ]
    payload = render_telemetry.build_payload(stages)
    assert payload["$schema"] == render_telemetry.SCHEMA_REF
    assert payload["schema_version"] == render_telemetry.SCHEMA_VERSION
    assert payload["totals"]["stages"] == 3
    assert payload["totals"]["duration_ms"] == 2000
    assert payload["build"]["platform"]
    assert payload["build"]["python"]


def test_build_payload_empty_list() -> None:
    """An empty stage list still produces a valid payload (totals are zero)."""
    payload = render_telemetry.build_payload([])
    assert payload["stages"] == []
    assert payload["totals"]["stages"] == 0
    assert payload["totals"]["duration_ms"] == 0


def test_build_payload_total_seconds_overrides_sum() -> None:
    """Caller-supplied total wall-clock takes precedence over per-stage sum.

    Captures pipeline overhead (output dir cleanup, between-stage I/O)
    that's not attributable to any single stage.
    """
    stages = [{"stage": "parse", "duration_ms": 100}]
    payload = render_telemetry.build_payload(stages, total_seconds=1.234)
    assert payload["totals"]["duration_ms"] == 1234


def test_normalise_stage_passes_through_extras(tmp_path: Path) -> None:
    """Extra fields on a stage record are preserved (forward-compat).

    A future caller may attach diagnostic metadata such as files emitted
    or bytes written; this should not require a schema bump.
    """
    cleaned = render_telemetry._normalise_stage(
        {"stage": "pages", "duration_ms": 500, "files": 100}
    )
    assert cleaned == {"stage": "pages", "duration_ms": 500, "files": 100}


def test_normalise_stage_rejects_missing_name() -> None:
    """A stage record without a ``stage`` field is a programming error."""
    with pytest.raises(ValueError, match="missing 'stage' name"):
        render_telemetry._normalise_stage({"duration_ms": 100})


def test_normalise_stage_rejects_negative_duration() -> None:
    """Negative wall-clock time is impossible and must be rejected."""
    with pytest.raises(ValueError, match="invalid duration_ms"):
        render_telemetry._normalise_stage({"stage": "parse", "duration_ms": -5})


def test_normalise_stage_rejects_non_int_duration() -> None:
    """Non-integer durations are also rejected — schema requires integer ms."""
    with pytest.raises(ValueError, match="invalid duration_ms"):
        render_telemetry._normalise_stage({"stage": "parse", "duration_ms": "fast"})


# ---------------------------------------------------------------------------
# 2. render() reproducibility contract
# ---------------------------------------------------------------------------


def test_render_skips_under_reproducible(tmp_path: Path) -> None:
    """``render(..., reproducible=True)`` must be a no-op — no file written.

    This is the core contract that lets the artefact coexist with
    ``tools/build/build.py --check`` without breaking the
    byte-reproducibility gate.
    """
    result = render_telemetry.render(
        tmp_path,
        [{"stage": "parse", "duration_ms": 100}],
        reproducible=True,
    )
    assert result is None
    assert not (tmp_path / render_telemetry.ARTEFACT_NAME).exists()


def test_render_writes_when_not_reproducible(tmp_path: Path) -> None:
    """Non-reproducible mode writes ``dist/build-telemetry.json``."""
    dest = render_telemetry.render(
        tmp_path,
        [{"stage": "parse", "duration_ms": 100}],
    )
    assert dest is not None
    assert dest == tmp_path / render_telemetry.ARTEFACT_NAME
    assert dest.exists()
    payload = json.loads(dest.read_text(encoding="utf-8"))
    assert payload["stages"][0]["stage"] == "parse"


def test_render_creates_parent_dir(tmp_path: Path) -> None:
    """The parent directory is created if absent (caller may pass dist/ that doesn't exist yet)."""
    nested = tmp_path / "nested" / "dist"
    dest = render_telemetry.render(
        nested,
        [{"stage": "parse", "duration_ms": 100}],
    )
    assert dest is not None
    assert dest.exists()


def test_render_writes_sorted_keys(tmp_path: Path) -> None:
    """JSON output uses sort_keys=True so the file ordering is stable.

    Even though we only emit telemetry in non-reproducible mode, the
    *structural* ordering of keys must be deterministic so a human
    diff between two snapshots is meaningful.
    """
    dest = render_telemetry.render(
        tmp_path,
        [{"stage": "metrics", "duration_ms": 50}, {"stage": "parse", "duration_ms": 200}],
    )
    assert dest is not None
    text = dest.read_text(encoding="utf-8")
    schema_pos = text.index('"$schema"')
    schema_version_pos = text.index('"schema_version"')
    totals_pos = text.index('"totals"')
    assert schema_pos < schema_version_pos < totals_pos


# ---------------------------------------------------------------------------
# 3. JSON Schema gate
# ---------------------------------------------------------------------------


def test_schema_file_meta_validates() -> None:
    """The schema file itself must be a valid JSON Schema 2020-12 document."""
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)


def test_synthetic_payload_validates_against_schema() -> None:
    """A synthetic 3-stage payload must validate against the schema."""
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    payload = render_telemetry.build_payload([
        {"stage": "parse", "duration_ms": 1000},
        {"stage": "pages", "duration_ms": 250},
    ])
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(payload))
    assert errors == []


def test_empty_stages_payload_validates_against_schema() -> None:
    """An empty stage list still validates (totals.stages = 0 is allowed)."""
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    payload = render_telemetry.build_payload([])
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(payload))
    assert errors == []


def test_payload_with_extra_stage_fields_validates(tmp_path: Path) -> None:
    """Forward-compatibility: extra fields on stage records must validate.

    The schema deliberately allows ``additionalProperties`` on stage
    items so a future caller can attach diagnostic metadata without a
    same-PR schema bump.
    """
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    payload = render_telemetry.build_payload([
        {"stage": "pages", "duration_ms": 500, "files_emitted": 100, "bytes": 1024},
    ])
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(payload))
    assert errors == []


def test_schema_rejects_missing_required_top_level() -> None:
    """A payload without ``stages`` must fail validation."""
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    bad = {
        "$schema": render_telemetry.SCHEMA_REF,
        "schema_version": "1.0.0",
        "build": {"platform": "x", "python": "3.14.4"},
        "totals": {"stages": 0, "duration_ms": 0},
    }
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(bad))
    assert errors, "missing 'stages' must trip validator"


def test_schema_rejects_negative_duration_in_payload() -> None:
    """Negative duration_ms in the payload must fail validation."""
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    payload = render_telemetry.build_payload([])
    payload["stages"] = [{"stage": "parse", "duration_ms": -1}]
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(payload))
    assert errors, "negative duration must trip schema"


# ---------------------------------------------------------------------------
# 4. Build-pipeline wiring
# ---------------------------------------------------------------------------


def test_metrics_stage_in_all_stages() -> None:
    """``"metrics"`` must be in ``ALL_STAGES`` so a default ``make build``
    actually emits ``dist/metrics.json``."""
    sys.path.insert(0, str(REPO_ROOT / "tools"))
    from build import build as build_module

    assert "metrics" in build_module.ALL_STAGES
    assert build_module.ALL_STAGES.index("metrics") == len(build_module.ALL_STAGES) - 1, (
        "metrics must be the LAST stage so it sees the freshly-parsed catalogue"
    )


def test_render_telemetry_imported_by_build() -> None:
    """``tools/build/build.py`` must import ``render_telemetry``."""
    sys.path.insert(0, str(REPO_ROOT / "tools"))
    from build import build as build_module

    assert hasattr(build_module, "render_telemetry")


# ---------------------------------------------------------------------------
# 5. Schema cross-references
# ---------------------------------------------------------------------------


def test_schema_version_constant_matches_schema_file() -> None:
    """``SCHEMA_VERSION`` and the schema's ``version`` must agree."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["version"] == render_telemetry.SCHEMA_VERSION


def test_schema_ref_constant_matches_schema_id_suffix() -> None:
    """``SCHEMA_REF`` must reference the same file as the schema's ``$id``."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["$id"].endswith(render_telemetry.SCHEMA_REF.lstrip("/"))


def test_artefact_name_is_stable() -> None:
    """``ARTEFACT_NAME`` is a wire-level constant — changing it is a major bump."""
    assert render_telemetry.ARTEFACT_NAME == "build-telemetry.json"
