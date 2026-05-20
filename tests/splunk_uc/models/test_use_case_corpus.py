"""Full-corpus integration test for the :class:`UseCase` model.

The unit-test file (:mod:`tests.splunk_uc.models.test_use_case`) exercises
the model with hand-crafted minimal and maximal fixtures. This file
exercises the model with the **real catalogue** under :file:`content/`
and locks in two invariants that matter for the build pipeline:

1.  **Every sidecar loads without error.** ``load_use_case`` must
    succeed for every committed ``content/cat-*/UC-*.json`` — there
    must be no schema field whose on-disk shape the model cannot
    parse. A regression here means a sidecar got committed in a
    shape the typed pipeline can't ingest, which is exactly what the
    typed model is supposed to catch up-front.
2.  **The only round-trip drift is the empty-array-collapse contract
    documented on :class:`splunk_uc.models.UseCase`.** Anything else
    (a missing scalar, a re-typed field, a re-ordered nested object,
    etc.) is a real lossy bug in the model. We assert that the
    drift set is *exactly* ``{("cimModels", []), ("prerequisiteUseCases", [])}``
    — anything beyond that pair has to be triaged.

These checks intentionally run over the entire ``content/cat-*/UC-*.json``
tree on every invocation; the asserted invariants are strong enough that
sampling would let bad shapes slip through. The test is still cheap (<2 s
for ~7,900 sidecars on a 2024 Apple Silicon laptop) because
:func:`load_use_case` skips JSON-schema validation entirely.
"""
from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

import pytest

from splunk_uc.models import load_use_case

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTENT_DIR = REPO_ROOT / "content"

# The contract: only these *exact* (key, value) drifts are tolerated
# on round-trip. See :class:`UseCase` round-trip docstring.
_TOLERATED_DRIFT: frozenset[tuple[str, str]] = frozenset(
    {
        ("cimModels", "[]"),
        ("prerequisiteUseCases", "[]"),
    }
)


def _sidecar_files() -> Iterable[Path]:
    """All committed UC sidecars, sorted for deterministic test output."""
    return sorted(CONTENT_DIR.glob("cat-*/UC-*.json"))


def test_corpus_dir_is_populated() -> None:
    """Sanity-check that we're actually reading the catalogue.

    Without this, a wrong ``CONTENT_DIR`` would silently make all the
    other tests pass-by-default.
    """
    files = list(_sidecar_files())
    assert len(files) >= 5_000, (
        f"expected at least 5k sidecars under {CONTENT_DIR}, found {len(files)}"
    )


def test_every_sidecar_loads_without_error() -> None:
    """``load_use_case`` must succeed for every committed sidecar."""
    failures: list[tuple[Path, str]] = []
    for path in _sidecar_files():
        try:
            load_use_case(path)
        except Exception as exc:  # pragma: no cover - failure path
            failures.append((path, f"{type(exc).__name__}: {exc}"))
    if failures:
        msgs = "\n".join(f"  {p}: {m}" for p, m in failures[:10])
        more = f"\n  ... and {len(failures) - 10} more" if len(failures) > 10 else ""
        pytest.fail(
            f"{len(failures)} sidecar(s) failed to load through "
            f"splunk_uc.models.UseCase.from_dict:\n{msgs}{more}"
        )


def test_corpus_round_trip_drift_is_only_empty_array_collapse() -> None:
    """The only documented drift is empty-array collapse on output.

    For every sidecar we compute the symmetric diff between the JSON
    on disk and ``UseCase.to_dict()``. Any key present on disk but
    missing on output is allowed only if its on-disk value matches
    the tolerated drift set. Any other diff (missing scalar, extra
    key, value change, re-typed value) is a real regression.
    """
    real_drift: list[tuple[Path, str, str]] = []
    for path in _sidecar_files():
        uc = load_use_case(path)
        original = json.loads(path.read_text(encoding="utf-8"))
        rebuilt = uc.to_dict()

        missing = set(original) - set(rebuilt)
        extra = set(rebuilt) - set(original)
        shared = set(original) & set(rebuilt)

        for key in missing:
            tolerated = (key, json.dumps(original[key], sort_keys=True))
            if tolerated not in _TOLERATED_DRIFT:
                real_drift.append(
                    (path, "missing", f"{key!r} = {original[key]!r}")
                )

        for key in extra:
            real_drift.append((path, "extra", f"{key!r} = {rebuilt[key]!r}"))

        for key in shared:
            if original[key] != rebuilt[key]:
                real_drift.append(
                    (
                        path,
                        "value",
                        f"{key!r}: orig={original[key]!r} vs rebuilt={rebuilt[key]!r}",
                    )
                )

    if real_drift:
        msgs = "\n".join(f"  {p.name}: [{k}] {m}" for p, k, m in real_drift[:10])
        more = (
            f"\n  ... and {len(real_drift) - 10} more"
            if len(real_drift) > 10
            else ""
        )
        pytest.fail(
            "UseCase round-trip drifted beyond the documented "
            "empty-array-collapse contract:\n"
            f"{msgs}{more}\n\n"
            "Either a real lossy bug was introduced in "
            "splunk_uc.models.use_case, or the model needs a new "
            "field. Triage before relaxing this test."
        )
