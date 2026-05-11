"""Unit tests for ``src/splunk_uc/audits/sandbox_validation.py``.

The sandbox audit is the Phase 4.5c gate that walks every UC sidecar
under ``content/cat-*/UC-*.json``, follows each ``controlTest.fixtureRef``
into ``sample-data/``, and verifies that the fixture parses, matches one
of the accepted structural shapes, and is populated with at least one
positive and one negative case. A malformed or unparseable fixture is a
hard failure that blocks CI.

The tests below pin two contracts:

1. **Shape recognition** — three fixture shapes are accepted:
   *  **phase2**: top-level ``events_positive`` / ``events_negative``
      arrays (synthetic Splunk events).
   *  **phase3** (NIS2 gold-standard uplift, commit ``8fba766c8``):
      top-level ``positive`` / ``negative`` arrays of evidence-attestation
      objects (no Splunk events). Each evidence item carries an
      ``evidence_id`` / ``owner`` / ``status`` triple.
   *  **legacy**: top-level ``positiveCase`` / ``negativeCase`` objects
      with their own ``events`` arrays and ``expectedFire`` polarity.

   A fixture that matches none of the three shapes is classified
   ``malformed`` — a hard failure.

2. **Population semantics** — a fixture with both arrays populated is
   ``populated``; one populated and one empty is ``half-empty``; both
   empty is ``empty``. Only ``malformed`` and ``bad-json`` block CI.

These tests exercise ``_classify_fixture`` directly so a regression on
shape recognition (e.g. someone re-removes phase3 support, or a future
shape is added without mirror tests) is caught at unit-test speed
rather than in a 12-minute ``validate.yml`` run.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from splunk_uc.audits import sandbox_validation as audit


def _write_fixture(tmp_path: Path, name: str, payload: object) -> Path:
    """Helper: write ``payload`` as JSON to ``tmp_path/name`` and
    return the resulting path. Used to keep the per-test fixture
    construction concise.
    """
    p = tmp_path / name
    p.write_text(json.dumps(payload), encoding="utf-8")
    return p


# ----------------------------------------------------------------------
# Shape recognition
# ----------------------------------------------------------------------


def test_classify_phase2_populated(tmp_path: Path) -> None:
    """A phase2 fixture with both arrays populated → ``populated`` /
    shape ``phase2`` / two events on each side."""
    f = _write_fixture(
        tmp_path,
        "phase2.json",
        {
            "uc_id": "UC-1.2.3",
            "description": "phase2 test",
            "events_positive": [{"a": 1}, {"a": 2}],
            "events_negative": [{"b": 1}],
        },
    )
    status, shape, pos, neg, issues = audit._classify_fixture(f)
    assert status == audit.STATUS_POPULATED
    assert shape == audit.FIXTURE_SHAPE_PHASE2
    assert (pos, neg) == (2, 1)
    assert issues == []


def test_classify_phase3_populated(tmp_path: Path) -> None:
    """A phase3 (NIS2-style) fixture with both arrays populated must
    classify as ``populated`` / shape ``phase3`` — this is the
    regression guard for commit ``8fba766c8``'s NIS2 uplift, which
    introduced 57 fixtures in this shape that the original audit
    rejected as ``malformed``."""
    f = _write_fixture(
        tmp_path,
        "phase3.json",
        {
            "uc": "UC-22.2.5",
            "positive": [
                {
                    "evidence_id": "ev-22-2-5-positive",
                    "owner": "CISO",
                    "status": "gap",
                }
            ],
            "negative": [
                {
                    "evidence_id": "ev-22-2-5-negative",
                    "owner": "CISO",
                    "status": "complete",
                }
            ],
        },
    )
    status, shape, pos, neg, issues = audit._classify_fixture(f)
    assert status == audit.STATUS_POPULATED
    assert shape == audit.FIXTURE_SHAPE_PHASE3
    assert (pos, neg) == (1, 1)
    assert issues == []


def test_classify_phase3_half_empty(tmp_path: Path) -> None:
    """A phase3 fixture with one empty array → ``half-empty`` (not a
    hard failure, but a tracked gap)."""
    f = _write_fixture(
        tmp_path,
        "half.json",
        {
            "uc": "UC-22.2.99",
            "positive": [{"evidence_id": "x", "owner": "CISO", "status": "gap"}],
            "negative": [],
        },
    )
    status, shape, _, _, _ = audit._classify_fixture(f)
    assert status == audit.STATUS_HALF_EMPTY
    assert shape == audit.FIXTURE_SHAPE_PHASE3


def test_classify_phase3_empty(tmp_path: Path) -> None:
    """A phase3 fixture with both arrays empty → ``empty`` (Phase 1.6
    placeholder territory; not a hard failure)."""
    f = _write_fixture(
        tmp_path,
        "empty.json",
        {"uc": "UC-22.2.99", "positive": [], "negative": []},
    )
    status, _, pos, neg, _ = audit._classify_fixture(f)
    assert status == audit.STATUS_EMPTY
    assert (pos, neg) == (0, 0)


def test_classify_phase3_malformed_when_arrays_arent_lists(tmp_path: Path) -> None:
    """A fixture that uses the phase3 keys but has the wrong types must
    still be ``malformed`` so authors get a clean error rather than a
    silent pass."""
    f = _write_fixture(
        tmp_path,
        "bad.json",
        {"uc": "UC-22.2.99", "positive": "not a list", "negative": []},
    )
    status, shape, _, _, issues = audit._classify_fixture(f)
    assert status == audit.STATUS_MALFORMED
    assert shape == audit.FIXTURE_SHAPE_PHASE3
    assert any("'positive' is not a list" in i for i in issues)


def test_classify_legacy_populated(tmp_path: Path) -> None:
    """The legacy ``positiveCase`` / ``negativeCase`` shape still
    classifies cleanly. Pinned because phase3 lives between phase2 and
    legacy in the elif chain — this guards against an accidental
    branch-order swap dropping legacy support."""
    f = _write_fixture(
        tmp_path,
        "legacy.json",
        {
            "description": "legacy test",
            "positiveCase": {"events": [{"a": 1}], "expectedFire": True},
            "negativeCase": {"events": [{"b": 1}], "expectedFire": False},
        },
    )
    status, shape, pos, neg, _ = audit._classify_fixture(f)
    assert status == audit.STATUS_POPULATED
    assert shape == audit.FIXTURE_SHAPE_LEGACY
    assert (pos, neg) == (1, 1)


def test_classify_unknown_shape_is_malformed(tmp_path: Path) -> None:
    """A fixture that matches none of the three shapes must be reported
    as ``malformed`` with an actionable issue listing all accepted
    shapes."""
    f = _write_fixture(
        tmp_path,
        "unknown.json",
        {"uc": "UC-99.99.99", "foo": [], "bar": []},
    )
    status, shape, _, _, issues = audit._classify_fixture(f)
    assert status == audit.STATUS_MALFORMED
    assert shape is None
    assert len(issues) == 1
    msg = issues[0]
    # Error message advertises ALL three shapes so the next contributor
    # who lands a new fixture knows exactly which keys are accepted.
    assert "phase2" in msg
    assert "phase3" in msg
    assert "legacy" in msg


def test_classify_bad_json(tmp_path: Path) -> None:
    """Unparseable JSON → ``bad-json`` (hard failure)."""
    p = tmp_path / "bad.json"
    p.write_text("{not valid json", encoding="utf-8")
    status, shape, _, _, issues = audit._classify_fixture(p)
    assert status == audit.STATUS_BAD_JSON
    assert shape is None
    assert any("parse error" in i for i in issues)


def test_classify_missing_returns_missing(tmp_path: Path) -> None:
    """A fixture path that doesn't exist on disk → ``missing`` (tracked
    gap, not a hard failure)."""
    status, shape, pos, neg, issues = audit._classify_fixture(tmp_path / "nope.json")
    assert status == audit.STATUS_MISSING
    assert shape is None
    assert (pos, neg) == (0, 0)
    assert issues == []


# ----------------------------------------------------------------------
# Hard-failure contract
# ----------------------------------------------------------------------


def test_hard_fail_statuses_constant_is_stable() -> None:
    """The set of hard-failure statuses is part of the audit's public
    contract — adding ``half-empty`` or ``empty`` to it would mass-fail
    Phase 1.6 placeholder UCs that the catalogue intentionally accepts.
    Pin the set so any change has to come with an explicit test
    update."""
    assert audit.HARD_FAIL_STATUSES == {audit.STATUS_BAD_JSON, audit.STATUS_MALFORMED}


@pytest.mark.parametrize(
    "shape_const,expected_value",
    [
        ("FIXTURE_SHAPE_PHASE2", "phase2"),
        ("FIXTURE_SHAPE_PHASE3", "phase3"),
        ("FIXTURE_SHAPE_LEGACY", "legacy"),
    ],
)
def test_shape_constant_values_are_pinned(
    shape_const: str, expected_value: str
) -> None:
    """The shape constants are written into ``reports/sandbox-validation.json``
    and read by tooling and dashboards, so their string values are part
    of the audit's public contract."""
    assert getattr(audit, shape_const) == expected_value
