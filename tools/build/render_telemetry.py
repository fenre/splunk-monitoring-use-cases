"""tools.build.render_telemetry — per-stage build timing emitter.

Repo-overhaul plan §P8 step 3 (2026-05-09): the build pipeline runs
~10 sequential stages (parse, assets, pages, api, search, exports,
meta, public, html_rewrite, integrity, build_info, metrics). Each
already prints its wall-clock duration via ``_log()`` for human
readers, but those numbers are only visible to whoever is watching
``stdout`` in real time. There is no structured artefact recording
*per-stage* timings, so a 30%-slower ``render_pages`` that crept in
between two releases would only get noticed when somebody watching
CI happened to spot it in the log.

This module captures stage durations in a structured form and emits
them as ``dist/build-telemetry.json`` so:

* a perf-regression dashboard or CI bot can plot stage-by-stage
  timing trend lines release-over-release;
* a maintainer can answer "which stage owns the slowest build today?"
  in one ``jq`` invocation;
* a future ``render_metrics.render`` consumer can correlate
  catalogue size against build time.

Reproducibility contract
------------------------

Stage durations are inherently non-deterministic. To preserve the
project-wide byte-reproducibility guarantee enforced by
``tools/build/build.py --check`` (two consecutive ``--reproducible``
builds must be byte-identical), this emitter is **opt-out under
``--reproducible``**: when the pipeline runs in reproducible mode,
the ``render`` function is a no-op and no file is written. The
artefact is therefore only present in non-reproducible builds, which
is exactly when timing telemetry is meaningful (CI runs that aren't
gating reproducibility, plus all maintainer ``make build`` runs).

Wire format
-----------

The emitted JSON is gated by ``schemas/v2/build-telemetry.schema.json``
and pinned at ``schema_version: "1.0.0"``. Adding a new stage to the
build is non-breaking; the schema enumerates expected stage names but
also allows additional names so a new pipeline stage doesn't break
the gate the moment it lands.
"""
from __future__ import annotations

import json
import platform
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0.0"
SCHEMA_REF = "/schemas/v2/build-telemetry.schema.json"
ARTEFACT_NAME = "build-telemetry.json"


def render(
    out_dir: Path,
    stages: list[dict[str, Any]],
    *,
    reproducible: bool = False,
    total_seconds: float | None = None,
) -> Path | None:
    """Emit ``dist/build-telemetry.json`` from a list of stage records.

    ``stages`` is a list of ``{"stage": str, "duration_ms": int}``
    dicts in the order the build pipeline executed them. The caller
    in ``tools/build/build.py`` accumulates this list as each stage
    completes.

    Returns the destination path, or ``None`` when the emitter is
    skipped under ``--reproducible``.
    """
    if reproducible:
        return None

    out_dir.mkdir(parents=True, exist_ok=True)
    payload = build_payload(stages, total_seconds=total_seconds)
    dest = out_dir / ARTEFACT_NAME
    dest.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return dest


def build_payload(
    stages: list[dict[str, Any]],
    *,
    total_seconds: float | None = None,
) -> dict[str, Any]:
    """Return the JSON payload (separated from disk I/O for unit tests)."""
    cleaned_stages = [_normalise_stage(s) for s in stages]
    total_ms = (
        round(total_seconds * 1000)
        if total_seconds is not None
        else sum(s["duration_ms"] for s in cleaned_stages)
    )
    return {
        "$schema": SCHEMA_REF,
        "schema_version": SCHEMA_VERSION,
        "build": {
            "platform": platform.platform(),
            "python": _python_version(),
        },
        "totals": {
            "stages": len(cleaned_stages),
            "duration_ms": total_ms,
        },
        "stages": cleaned_stages,
    }


def _normalise_stage(stage: dict[str, Any]) -> dict[str, Any]:
    """Return a record satisfying the schema (at minimum: stage + duration_ms).

    Tolerates extra fields silently — the schema allows them — so a
    future caller can attach diagnostic metadata (e.g. file counts,
    bytes emitted) without changing this function.
    """
    name = stage.get("stage")
    if not isinstance(name, str) or not name:
        raise ValueError(f"telemetry stage record missing 'stage' name: {stage!r}")
    duration_ms = stage.get("duration_ms", 0)
    if not isinstance(duration_ms, int) or duration_ms < 0:
        raise ValueError(
            f"telemetry stage {name!r} has invalid duration_ms: {duration_ms!r}"
        )
    cleaned = {"stage": name, "duration_ms": duration_ms}
    for k, v in stage.items():
        if k in ("stage", "duration_ms"):
            continue
        cleaned[k] = v
    return cleaned


def _python_version() -> str:
    """Return ``X.Y.Z`` (no patch metadata) for build cross-comparison."""
    info = sys.version_info
    return f"{info.major}.{info.minor}.{info.micro}"
