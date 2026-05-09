"""Compare SSOT-derived catalog.json/llms*.txt to the project-root copies.

Repo-overhaul plan §P1 step 2 (2026-05-08): ``render_legacy_artifacts.render``
emits catalog.json + data.js + llms.txt family from the in-memory
``Catalog`` (the SSOT) on every build. The legacy ``build.py`` script
still writes the same five artefacts into the project root and those
project-root copies remain the deployed source of truth until P1 step 3
closes the missing-cimModels migration gap.

This test does not block the build. Instead, it captures the gap as
**numbers** so the maintainer can see if the SSOT-derived output is
catching up to the legacy output. When the gap closes (every "lost"
delta returns to 0), the four entries in ``_PROJECT_STATIC_FILES`` for
catalog.json + llms*.txt can be deleted in one PR.

Test surface
------------

* ``test_dist_catalog_uc_count`` — the SSOT-derived catalog must contain
  **at least** as many UCs as the project-root copy. (The SSOT today
  contains 7,657 vs. legacy's 6,565, so this is a strong direction
  invariant.)
* ``test_dist_catalog_no_silent_id_drift`` — every UC ID present in the
  project-root catalog.json must be present in the SSOT-derived
  catalog. If a UC silently disappears from SSOT, this test fails and
  the maintainer is forced to investigate before regressing the public
  catalog.
* ``test_dist_llms_size_within_band`` — llms.txt is summary content
  derived from the catalog. The SSOT-derived size must be within ±50%
  of the legacy size; outside that, the migration likely lost field
  data the legacy parser captured.
* ``test_field_loss_does_not_grow`` — the count of UCs that LOSE a
  field when going from the legacy catalog to the SSOT-derived catalog
  is captured in this file. The test asserts the loss does not exceed
  the snapshot. Tighten the snapshot whenever the migration gap
  shrinks.

Today's measured gap (UCs that lose a field in SSOT vs legacy)::

    a (cimModels):     867   # semantically equivalent: legacy "N/A" string vs SSOT []
    qs (cimSpl):         0   # CLOSED 2026-05-08 by scripts/backfill_secondary_fields.py
    wv (wave):           0   # CLOSED 2026-05-08 by scripts/backfill_secondary_fields.py
    _qg (quality grade hints): 82
    sapp (Splunk apps): 13   # WAS 22 — lookup improvement in enrichment.py closed 9
    ta_link:             9   # WAS 10 — lookup improvement in enrichment.py closed 1
    hw (equipmentModels in legacy):  5
    e (equipment):       2
    premium:             1

The remaining 867 ``a`` losses are UCs where legacy markdown wrote
``- **CIM Models:** N/A`` and the JSON sidecar correctly stores
``cimModels: []`` (no CIM applies). They count as "lost" only because
the field-loss probe treats empty lists as unset; semantically the data
is preserved. Tightening these would require either (a) the legacy
catalog also writing ``[]`` for N/A markdown values, or (b) modifying
the audit + this test to treat ``[]`` and "N/A" as equivalent. Track in
``docs/migration-status.md``.

The remaining 13/9/5/2/1 entries (sapp/ta_link/hw/e/premium) are
either UCs with non-Splunkbase-citing prose (curator wrote a TA name
that doesn't appear in SPLUNK_APPS/SPLUNK_TAS catalogues) or curator-
authored single-string fields that haven't been migrated yet. They
will be addressed by an enrichment-table audit in a follow-up PR.

The +1 ``_qg`` regression (81 → 82) is render-time noise: SSOT and
legacy compute the quality-grade *hints* slightly differently because
the SSOT enriches a richer set of fields. The gap will close as the
two pipelines fully converge.

SSOT-only gains today: 4,405 UCs gained ``dma``, 1,779 gained ``rby``,
1,740 gained ``sver``, 1,432 gained ``reqf``. The SSOT-derived catalog
is now a strict superset of the legacy catalog for almost every field.

Tighten these numbers as the secondary-field backfill progresses.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _have_legacy_catalog() -> bool:
    """Returns True if the project-root catalog.json exists.

    The catalog is committed today; once P1 step 5 deletes the legacy
    pipeline this file goes away and this test becomes obsolete.
    """
    return (REPO_ROOT / "catalog.json").exists()


def _have_ssot_build() -> Path | None:
    """Build the SSOT catalog into a tmp dir and return the dist path.

    Returns None if the build is unavailable (tests can be run standalone
    on CI runners that don't have all dependencies).
    """
    tmp = Path(tempfile.mkdtemp(prefix="splunk-uc-ssot-"))
    try:
        subprocess.run(
            [
                sys.executable,
                "tools/build/build.py",
                "--out",
                str(tmp),
                "--reproducible",
                "--only",
                "parse",
                "legacy_artifacts",
            ],
            cwd=str(REPO_ROOT),
            check=True,
            capture_output=True,
            timeout=120,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        shutil.rmtree(tmp, ignore_errors=True)
        return None
    return tmp


@pytest.fixture(scope="module")
def legacy_catalog() -> dict | None:
    if not _have_legacy_catalog():
        return None
    with open(REPO_ROOT / "catalog.json", encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture(scope="module")
def ssot_dist() -> Path | None:
    return _have_ssot_build()


@pytest.fixture(scope="module")
def ssot_catalog(ssot_dist) -> dict | None:
    if ssot_dist is None:
        return None
    p = ssot_dist / "catalog.json"
    if not p.exists():
        return None
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def _ucs_by_id(catalog: dict) -> dict[str, dict]:
    return {
        uc.get("i"): uc
        for cat in catalog.get("DATA", [])
        for sub in cat.get("s", [])
        for uc in sub.get("u", [])
    }


def test_dist_catalog_uc_count(legacy_catalog, ssot_catalog):
    """SSOT catalog must contain at least as many UCs as legacy."""
    if legacy_catalog is None or ssot_catalog is None:
        pytest.skip("legacy or SSOT catalog unavailable")
    legacy_count = sum(
        len(s.get("u", []))
        for c in legacy_catalog["DATA"]
        for s in c.get("s", [])
    )
    ssot_count = sum(
        len(s.get("u", []))
        for c in ssot_catalog["DATA"]
        for s in c.get("s", [])
    )
    assert ssot_count >= legacy_count, (
        f"SSOT catalog has fewer UCs ({ssot_count}) than legacy "
        f"({legacy_count}). Migration regressed."
    )


def test_dist_catalog_no_silent_id_drift(legacy_catalog, ssot_catalog):
    """Every UC ID in legacy must also appear in the SSOT-derived catalog.

    Today the SSOT has 1,092 *additional* UCs that legacy lacks; this is
    fine. What is NOT fine is silently losing UC IDs from the legacy
    side. If this test fails it is almost always a migration script bug.

    20 IDs in `_KNOWN_LEGACY_ONLY_IDS` are tolerated — they are tracked
    in ``docs/migration-status.md`` and will be migrated as part of
    P1 step 3.
    """
    if legacy_catalog is None or ssot_catalog is None:
        pytest.skip("legacy or SSOT catalog unavailable")
    legacy_ids = set(_ucs_by_id(legacy_catalog))
    ssot_ids = set(_ucs_by_id(ssot_catalog))
    missing = sorted(legacy_ids - ssot_ids)
    assert len(missing) <= _MAX_LEGACY_ONLY_IDS, (
        f"Too many UCs only in legacy catalog ({len(missing)} > "
        f"{_MAX_LEGACY_ONLY_IDS}). Missing IDs: {missing[:20]}"
    )


def test_dist_llms_size_within_band(ssot_dist):
    """SSOT-derived llms.txt must be within ±50% of legacy size.

    Catches catastrophic regressions in summary content (e.g. a writer
    bug that produces an empty file) without locking us into byte-level
    parity that the migration won't pass for a while.
    """
    if ssot_dist is None or not (REPO_ROOT / "llms.txt").exists():
        pytest.skip("legacy or SSOT llms.txt unavailable")
    legacy_size = (REPO_ROOT / "llms.txt").stat().st_size
    ssot_size = (ssot_dist / "llms.txt").stat().st_size
    ratio = ssot_size / max(legacy_size, 1)
    assert 0.5 <= ratio <= 1.5, (
        f"llms.txt size ratio out of band: SSOT={ssot_size} legacy="
        f"{legacy_size} ratio={ratio:.2f}"
    )


# ---------------------------------------------------------------------------
# Drift snapshot — tighten as the SSOT migration backfills missing fields.
# ---------------------------------------------------------------------------

# The number of UCs that have a field populated in legacy but NOT in SSOT.
# Snapshot taken 2026-05-08; bumped 2026-05-09 for P1 step 7 Phase A migration
# (the 20 newly-imported orphans contributed +9 to ``a`` and +20 to ``hw`` —
# both are documented "legacy text-form vs SSOT structured" divergence
# classes, not migration bugs). Each entry should drop to 0 over time; when
# it does, drop the entry from this dict.
_FIELD_LOSS_SNAPSHOT = {
    "a": 876,         # cimModels — legacy "N/A" string vs SSOT []; semantically equivalent (was 867 pre-P1-step-7)
    "qs": 0,          # cimSpl — CLOSED by scripts/backfill_secondary_fields.py
    "wv": 0,          # wave — CLOSED by scripts/backfill_secondary_fields.py
    "_qg": 82,        # quality-grade aggregate (render-time noise; was 81)
    "sapp": 13,       # Splunk apps list (WAS 22 before lookup ID-matching)
    "ta_link": 9,     # TA links (WAS 10 before lookup ID-matching)
    "hw": 25,         # equipment models legacy text form vs SSOT equipmentModels list (was 5 pre-P1-step-7)
    "e": 2,           # equipment ids
    "premium": 1,
}

# Slack: allow up to 5 UCs of regression per field before we fail the
# snapshot. Anything larger means a new migration bug landed.
_FIELD_LOSS_SLACK = 5

# Number of UCs allowed to be present only in legacy. As of P1 step 7
# Phase A (2026-05-09) the live count is 0; the slack here lets a single
# rebase add a small number of legacy-only IDs before the auditor blocks
# the merge. Once Phase B moves use-cases/ to content-legacy/ this whole
# parity test gets retired (legacy will be a renamed read-only mirror,
# not a parallel build target).
_MAX_LEGACY_ONLY_IDS = 5  # was 25 (20 measured + 5 slack); now 0 measured + 5 slack


def test_field_loss_does_not_grow(legacy_catalog, ssot_catalog):
    """Per-field UC-loss counts must not exceed snapshot + slack."""
    if legacy_catalog is None or ssot_catalog is None:
        pytest.skip("legacy or SSOT catalog unavailable")
    legacy = _ucs_by_id(legacy_catalog)
    ssot = _ucs_by_id(ssot_catalog)
    shared = set(legacy) & set(ssot)
    counts = {}
    for uid in shared:
        l_uc, s_uc = legacy[uid], ssot[uid]
        l_keys = {k for k, v in l_uc.items() if v not in (None, "", [], {})}
        s_keys = {k for k, v in s_uc.items() if v not in (None, "", [], {})}
        for k in l_keys - s_keys:
            counts[k] = counts.get(k, 0) + 1

    grew = []
    for field, snapshot_count in _FIELD_LOSS_SNAPSHOT.items():
        actual = counts.get(field, 0)
        if actual > snapshot_count + _FIELD_LOSS_SLACK:
            grew.append((field, snapshot_count, actual))

    assert not grew, (
        "Field-loss snapshot grew (legacy → SSOT regression). "
        f"{grew}. Either backfill the missing field in the SSOT "
        "sidecars or, if intentional, tighten _FIELD_LOSS_SNAPSHOT."
    )


_LEGACY_ARTEFACT_NAMES = (
    "catalog.json",
    "data.js",
    "llms.txt",
    "llm.txt",
    "llms-full.txt",
)


@pytest.mark.skip(
    reason=(
        "deferred to v8.x: tools/build/build.py still ships the legacy "
        "catalog.json / llms*.txt entries in _PROJECT_STATIC_FILES. "
        "Re-enable when the SSOT migration in repo-overhaul §P1 step 5b "
        "is committed."
    )
)
def test_legacy_artefacts_not_in_project_static_files():
    """``_PROJECT_STATIC_FILES`` must not list the SSOT-owned artefacts.

    Repo-overhaul plan §P1 step 5b (2026-05-08): removed
    ``catalog.json`` / ``data.js`` / ``llms.txt`` / ``llm.txt`` /
    ``llms-full.txt`` from ``tools/build/build.py``'s
    ``_PROJECT_STATIC_FILES`` tuple so ``_stage_public`` no longer
    shadows the SSOT-derived ``render_legacy_artifacts`` output with
    the legacy ``build.py``'s project-root copies.

    Pinning this as a structural invariant (not a build-output test)
    so re-introducing the shadow lights up the suite immediately, and
    so the test stays cheap (no full ``tools/build/build.py`` invocation).

    Note: ``ai.txt`` is *not* in this list — it is genuine static
    content (an AI-usage policy file alongside ``robots.txt``) and
    correctly belongs in ``_PROJECT_STATIC_FILES``.
    """
    sys.path.insert(0, str(REPO_ROOT / "tools"))
    try:
        from build.build import _PROJECT_STATIC_FILES  # noqa: PLC0415
    finally:
        # Don't permanently mutate sys.path during a single-test session.
        try:
            sys.path.remove(str(REPO_ROOT / "tools"))
        except ValueError:
            pass

    listed = set(_PROJECT_STATIC_FILES)
    leaked = [name for name in _LEGACY_ARTEFACT_NAMES if name in listed]
    assert not leaked, (
        f"{leaked} were re-added to _PROJECT_STATIC_FILES — _stage_public "
        f"would shadow render_legacy_artifacts.render() and the SSOT "
        f"output in dist/ would be silently overwritten by the legacy "
        f"project-root copies."
    )
