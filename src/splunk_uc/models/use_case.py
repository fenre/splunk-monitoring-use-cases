"""The typed :class:`UseCase` dataclass + the :class:`UseCaseDict` TypedDict.

See :mod:`splunk_uc.models` (the subpackage docstring) for the design
rationale: stdlib-only, schema-respecting, round-trip-safe.

Public API
==========

* :class:`UseCase` — frozen dataclass with the most-touched fields
  typed as proper attributes, plus an ``extras`` mapping that preserves
  every other field verbatim.
* :class:`UseCaseDict` — :class:`typing.TypedDict` describing the full
  on-disk shape for code that prefers bracket access.
* :func:`load_use_case` — convenience loader from a sidecar path.
* :func:`UseCase.from_dict` — explicit dict-to-model constructor.
* :func:`UseCase.to_dict` — round-trip emitter; output is keyed in
  the canonical sidecar field order.

Invariants
==========

* ``id`` and ``title`` are **required**; missing either raises
  :class:`ValueError` from :meth:`UseCase.from_dict`. This matches the
  ``required: ["id", "title"]`` block in
  :file:`schemas/uc.schema.json`.
* ``id`` must match the bare ``X.Y.Z`` form (no ``UC-`` prefix), per
  the schema's pattern; the constructor raises :class:`ValueError` on
  a violation.
* All other fields are optional. The dataclass uses ``None`` as the
  sentinel for "absent" and an empty tuple / dict for "explicitly
  empty collection" to keep mypy strict-clean.
* Round-trip is **lossless**: every key that came in via
  :meth:`from_dict` comes back out via :meth:`to_dict`, in canonical
  order, regardless of whether it was modelled as a first-class
  attribute or stored in ``extras``.

Stability
=========

Provisional surface — see the subpackage docstring.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypedDict, cast

from .._uc_sidecar import canonical_sidecar

# UC-ID grammar (bare form, no ``UC-`` prefix). Mirrors the
# ``pattern`` clause in schemas/uc.schema.json for the ``id`` property.
# The grammar is gap-free positive integers separated by dots.
_UC_ID_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")

# Fields the dataclass surfaces as proper typed attributes. Everything
# else flows through ``extras`` so the round-trip stays lossless even
# as the schema gains new optional properties.
_MODELLED_FIELDS: frozenset[str] = frozenset(
    {
        "id",
        "title",
        "criticality",
        "difficulty",
        "monitoringType",
        "splunkPillar",
        "wave",
        "prerequisiteUseCases",
        "value",
        "app",
        "dataSources",
        "spl",
        "cimModels",
        "grandmaExplanation",
    }
)


class UseCaseDict(TypedDict, total=False):
    """The on-disk UC sidecar dict shape, typed for mypy.

    Marked ``total=False`` because every field except ``id`` and
    ``title`` is optional at the schema level. Consumers that need
    "this field is present" semantics should branch on ``key in uc``
    rather than catching :class:`KeyError`.

    Field types match the JSON shape, not the Python-runtime shape:

    * ``monitoringType``, ``prerequisiteUseCases``, and ``cimModels``
      are ``list[str]`` on disk (JSON arrays), even though
      :class:`UseCase` exposes them as ``tuple[str, ...]`` for
      immutability.
    * ``dataSources`` is a free-form narrative ``str`` per the schema
      (it names indexes / sourcetypes / CIM nodes in prose), **not**
      an array — a common mismodelling trap if you grep for
      "dataSources" in old generators that joined string lists.
    * ``compliance`` is a ``list[dict[str, Any]]`` — sub-shapes vary by
      regulation and are not typed here; consumers walking the
      compliance array typically dispatch on ``regulation``.
    """

    id: str
    title: str
    criticality: str
    difficulty: str
    monitoringType: list[str]
    splunkPillar: str
    wave: str
    prerequisiteUseCases: list[str]
    value: str
    app: str
    # ``dataSources`` is a free-form narrative string per the schema
    # (``"type": "string"``) — naming indexes, sourcetypes, or CIM
    # nodes in prose. Not a JSON array.
    dataSources: str
    spl: str
    cimModels: list[str]
    grandmaExplanation: str
    compliance: list[dict[str, Any]]
    implementation: dict[str, Any] | str
    visualization: dict[str, Any] | str
    description: str
    references: list[str]
    knownFalsePositives: str
    mitreAttack: list[str]
    detectionType: str
    securityDomain: str
    requiredFields: list[str]
    equipment: list[str]
    equipmentModels: list[str]
    status: str
    lastReviewed: str
    splunkVersions: list[str]
    reviewer: str
    premiumApps: list[str]
    attackTechnique: list[str]


@dataclass(frozen=True, slots=True)
class UseCase:
    """An immutable, typed view onto a single UC sidecar.

    Instances are produced by :meth:`from_dict` (or :func:`load_use_case`).
    Direct construction with the dataclass constructor works too but
    skips the ``id``-pattern validation — prefer :meth:`from_dict` for
    untrusted input.

    Attributes
    ----------
    id:
        UC identifier in the bare ``X.Y.Z`` form (no ``UC-`` prefix).
        The full display form is ``f"UC-{uc.id}"``.
    title:
        Human-readable title; minimum 8 characters per the schema.
    criticality, difficulty, wave, splunkPillar:
        Optional enum-valued strings. ``None`` means the field was
        absent on disk.
    monitoringType, prerequisiteUseCases, dataSources, cimModels:
        Tuples (immutable copies of the JSON arrays).
    value, app, spl, grandmaExplanation:
        Long-form strings; ``""`` means the field was present but
        empty, ``None`` means the field was absent.
    extras:
        Every other key from the source dict, preserved verbatim. This
        is the round-trip safety valve: schema growth doesn't force a
        dataclass change.
    """

    id: str
    title: str
    criticality: str | None = None
    difficulty: str | None = None
    monitoring_type: tuple[str, ...] = ()
    splunk_pillar: str | None = None
    wave: str | None = None
    prerequisite_use_cases: tuple[str, ...] = ()
    value: str | None = None
    app: str | None = None
    # ``data_sources`` is a free-form narrative string per the
    # schema (``"type": "string"``), not an array. The author names
    # indexes / sourcetypes / CIM nodes in prose; downstream code
    # that wants tokens parses them on demand.
    data_sources: str | None = None
    spl: str | None = None
    cim_models: tuple[str, ...] = ()
    grandma_explanation: str | None = None
    extras: Mapping[str, Any] = field(default_factory=dict)

    # Round-trip contract
    # ===================
    # :meth:`from_dict` accepts a sidecar in any shape the schema
    # admits; :meth:`to_dict` re-emits it in canonical form. The only
    # documented divergence between input and output is **empty
    # arrays on optional array-typed fields**: an explicit
    # ``"cimModels": []`` or ``"prerequisiteUseCases": []`` collapses
    # to ``()`` on the model and is **omitted** on output, because
    # the schema treats "absent" and "empty array" as semantically
    # equivalent and the build pipeline's enrichment layer never
    # cares about the difference. A full-corpus smoke test
    # (``tests/splunk_uc/models/test_use_case_corpus.py``) asserts
    # this is the *only* drift across all sidecars in the repo.

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    @property
    def display_id(self) -> str:
        """Return the prefixed display form, e.g. ``"UC-1.1.1"``."""
        return f"UC-{self.id}"

    # ------------------------------------------------------------------
    # Round-trip
    # ------------------------------------------------------------------

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> UseCase:
        """Build a :class:`UseCase` from a parsed UC sidecar dict.

        Raises
        ------
        ValueError
            If ``id`` or ``title`` is missing, or if ``id`` does not
            match the ``X.Y.Z`` grammar pinned by
            :file:`schemas/uc.schema.json`. The dataclass does **not**
            re-enforce the long tail of schema constraints — that is
            the job of :mod:`jsonschema` against the canonical schema.
        """
        if "id" not in data:
            raise ValueError("UC sidecar is missing required field 'id'")
        if "title" not in data:
            raise ValueError("UC sidecar is missing required field 'title'")
        uc_id_raw = data["id"]
        if not isinstance(uc_id_raw, str):
            raise ValueError(
                f"UC sidecar 'id' must be a string; got {type(uc_id_raw).__name__}"
            )
        if not _UC_ID_RE.match(uc_id_raw):
            raise ValueError(
                f"UC sidecar 'id' must match X.Y.Z (no 'UC-' prefix); got "
                f"{uc_id_raw!r}"
            )
        title_raw = data["title"]
        if not isinstance(title_raw, str):
            raise ValueError(
                f"UC sidecar 'title' must be a string; got {type(title_raw).__name__}"
            )

        extras: dict[str, Any] = {
            key: value
            for key, value in data.items()
            if key not in _MODELLED_FIELDS
        }

        return cls(
            id=uc_id_raw,
            title=title_raw,
            criticality=_opt_str(data, "criticality"),
            difficulty=_opt_str(data, "difficulty"),
            monitoring_type=_opt_str_tuple(data, "monitoringType"),
            splunk_pillar=_opt_str(data, "splunkPillar"),
            wave=_opt_str(data, "wave"),
            prerequisite_use_cases=_opt_str_tuple(data, "prerequisiteUseCases"),
            value=_opt_str(data, "value"),
            app=_opt_str(data, "app"),
            data_sources=_opt_str(data, "dataSources"),
            spl=_opt_str(data, "spl"),
            cim_models=_opt_str_tuple(data, "cimModels"),
            grandma_explanation=_opt_str(data, "grandmaExplanation"),
            extras=extras,
        )

    def to_dict(self) -> dict[str, Any]:
        """Re-emit the UC as a JSON-shaped dict in canonical key order.

        The output is byte-compatible with what the existing sidecar
        loaders / writers produce: keys are ordered per
        :data:`splunk_uc._uc_sidecar.SIDECAR_FIELD_ORDER`, modelled
        fields are emitted as native JSON types, and ``extras`` is
        appended at the canonical positions of any matching keys (with
        unknown keys retained in original insertion order at the
        tail).
        """
        out: dict[str, Any] = {}
        # ``id`` and ``title`` are always present.
        out["id"] = self.id
        out["title"] = self.title
        if self.criticality is not None:
            out["criticality"] = self.criticality
        if self.difficulty is not None:
            out["difficulty"] = self.difficulty
        if self.monitoring_type:
            out["monitoringType"] = list(self.monitoring_type)
        if self.splunk_pillar is not None:
            out["splunkPillar"] = self.splunk_pillar
        if self.wave is not None:
            out["wave"] = self.wave
        if self.prerequisite_use_cases:
            out["prerequisiteUseCases"] = list(self.prerequisite_use_cases)
        if self.value is not None:
            out["value"] = self.value
        if self.app is not None:
            out["app"] = self.app
        if self.data_sources is not None:
            out["dataSources"] = self.data_sources
        if self.spl is not None:
            out["spl"] = self.spl
        if self.cim_models:
            out["cimModels"] = list(self.cim_models)
        if self.grandma_explanation is not None:
            out["grandmaExplanation"] = self.grandma_explanation
        # Re-merge unmodelled keys, then canonicalise once.
        for key, value in self.extras.items():
            if key not in out:
                out[key] = value
        return canonical_sidecar(out)

    def to_typed_dict(self) -> UseCaseDict:
        """Return :meth:`to_dict`'s output cast to :class:`UseCaseDict`.

        Pure convenience for callers that want mypy-strict access on
        the bracket-form view without having to write the cast
        themselves.
        """
        return cast(UseCaseDict, self.to_dict())


def load_use_case(path: str | Path) -> UseCase:
    """Load a single UC sidecar from disk and return a typed view.

    Parameters
    ----------
    path:
        Filesystem path to a ``content/cat-NN-slug/UC-X.Y.Z.json``
        sidecar (or any compatible JSON file).

    Raises
    ------
    FileNotFoundError
        If ``path`` does not exist.
    json.JSONDecodeError
        If the file is not valid JSON.
    ValueError
        If the parsed dict is not a JSON object, or if
        :meth:`UseCase.from_dict` rejects it for missing or malformed
        required fields. The exception message names the file so a
        batch caller iterating over thousands of sidecars can locate
        the offending one.
    """
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    raw: Any = json.loads(text)
    if not isinstance(raw, dict):
        raise ValueError(
            f"{p}: expected a JSON object at the top level; got "
            f"{type(raw).__name__}"
        )
    try:
        return UseCase.from_dict(cast(Mapping[str, Any], raw))
    except ValueError as exc:
        raise ValueError(f"{p}: {exc}") from exc


# ----------------------------------------------------------------------
# Internal helpers
# ----------------------------------------------------------------------


def _opt_str(data: Mapping[str, Any], key: str) -> str | None:
    """Return ``data[key]`` as a ``str`` if present, ``None`` otherwise.

    A non-string value at a string-typed key is a schema violation and
    raises :class:`ValueError`. We surface the offending key in the
    message so a batch caller can locate the malformed sidecar.
    """
    if key not in data:
        return None
    value = data[key]
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(
            f"field {key!r} must be a string; got {type(value).__name__}"
        )
    return value


def _opt_str_tuple(data: Mapping[str, Any], key: str) -> tuple[str, ...]:
    """Return ``data[key]`` as an immutable tuple of strings.

    Absent or ``None`` resolves to an empty tuple — the dataclass field
    default — so callers don't have to branch on absence. A non-list
    value or a list with non-string elements is a schema violation and
    raises :class:`ValueError`.
    """
    if key not in data:
        return ()
    value = data[key]
    if value is None:
        return ()
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(
            f"field {key!r} must be an array; got {type(value).__name__}"
        )
    out: list[str] = []
    for index, element in enumerate(value):
        if not isinstance(element, str):
            raise ValueError(
                f"field {key!r}[{index}] must be a string; got "
                f"{type(element).__name__}"
            )
        out.append(element)
    return tuple(out)
