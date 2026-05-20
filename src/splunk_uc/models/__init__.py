"""Typed data-models for the Splunk Monitoring Use Cases catalogue.

This subpackage is the typed surface called out by repo-health phase
**P4** ("Typed Python pipeline") — its job is to give downstream code a
mypy-checked, attribute-style view onto the same JSON sidecars that
the dict-based audits already consume.

Design intent
=============

The catalogue's authoritative shape lives in
:file:`schemas/uc.schema.json` (JSON Schema 2020-12, ``additionalProperties:
false``). That schema is the source of truth; nothing in this package
re-encodes the schema's invariants. Instead we provide:

* :class:`~splunk_uc.models.use_case.UseCase` — an immutable, frozen
  :class:`dataclasses.dataclass` that types the small set of fields
  every consumer touches (``id``, ``title``, ``criticality``,
  ``difficulty``, ``monitoringType``, ``value``, ``app``,
  ``dataSources``, ``spl``, ``cimModels``, …).
* :class:`~splunk_uc.models.use_case.UseCaseDict` — a
  :class:`typing.TypedDict` that types the full on-disk dict shape so
  code that prefers dict access (e.g. ``uc["compliance"][0]["clause"]``)
  still gets mypy coverage.
* :func:`~splunk_uc.models.use_case.load_use_case` — a one-shot
  ``Path → UseCase`` loader that validates required fields are present.

Why dataclass + TypedDict instead of Pydantic
=============================================

The runtime ``dependencies`` block in :file:`pyproject.toml` is empty
by design — :doc:`/docs/adr/0004-stdlib-only-build` (the
"stdlib-only build pipeline" ADR) means a fresh CI runner can produce
``dist/`` without ``pip install`` of any third-party package. Adding
:mod:`pydantic` as a runtime dependency would violate that contract.
Validation against the JSON schema remains the job of
:mod:`jsonschema` (already in the ``audits`` extra) — :class:`UseCase`
intentionally does *not* try to replicate every constraint the schema
encodes; it surfaces the most-touched fields with proper types and
leaves schema-level validation to the schema itself.

Round-trip discipline
=====================

:meth:`UseCase.to_dict` always emits keys in the canonical sidecar
field order pinned by
:mod:`splunk_uc._uc_sidecar` so a round-trip
(JSON → :class:`UseCase` → dict → JSON) preserves the byte-identical
shape the existing generator chain and the ``--check`` drift gates
expect. Fields not modelled on the dataclass survive the round-trip
verbatim via the ``extras`` attribute.

Stability
=========

This module is **stability: provisional** — the typed surface may grow
new attributes as more fields graduate from "occasionally accessed
dict key" to "type-checked first-class property". Removing or
renaming an existing attribute requires a major version bump per
:doc:`/docs/schema-versioning`.
"""

from __future__ import annotations

from .use_case import UseCase, UseCaseDict, load_use_case

__all__ = ["UseCase", "UseCaseDict", "load_use_case"]
