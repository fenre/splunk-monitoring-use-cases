"""Schema-parity gates for the typed data models.

Repo-overhaul plan §P4 step 2 (2026-05-08): the typed models in
``tools/build/models.py`` must mirror three sources of truth:

1. ``schemas/uc.schema.json`` — the JSON Schema used by
   ``python3 -m splunk_uc audit-uc-structure`` to validate every UC sidecar.
2. ``catalog.json`` — the wire format consumed by the static UI,
   ``api/cat-N.json``, ``data.js``, and external integrations.
3. ``data/regulations.json`` — the cat-22 framework taxonomy.

These tests guarantee that any field added to those files lights up
this suite if it isn't also added to the matching :mod:`tools.build.models`
TypedDict. That keeps consumers' static type checks meaningful even as
the schema evolves.

What's covered
--------------

* :func:`test_use_case_typed_dict_matches_schema` — every property in
  ``schemas/uc.schema.json`` (minus the optional ``$schema`` IDE hint)
  has a matching :class:`~tools.build.models.UseCase` TypedDict field
  and vice versa.
* :func:`test_catalog_typed_dicts_match_real_payload` — every key
  present in ``catalog.json`` for the seven catalog TypedDicts has a
  matching field in :class:`~tools.build.models.CatalogJson`,
  :class:`~tools.build.models.CatalogCategory`,
  :class:`~tools.build.models.CatalogSubcategory`,
  :class:`~tools.build.models.CatalogUC`,
  :class:`~tools.build.models.CategoryMeta`,
  :class:`~tools.build.models.EquipmentEntry`, and
  :class:`~tools.build.models.ImplementationRoadmapEntry`.
* :func:`test_regulation_typed_dicts_match_real_payload` — same for
  :class:`~tools.build.models.RegulationFramework`,
  :class:`~tools.build.models.RegulationVersionEntry`, and
  :class:`~tools.build.models.RegulationCommonClause`.
* :func:`test_typed_helpers_return_keysets` — the
  :func:`~tools.build.models.use_case_typed_keys` and
  :func:`~tools.build.models.catalog_uc_typed_keys` helpers return the
  expected number of fields. Pins the cardinality so an accidental
  removal lights up immediately.

Why these tests are cheap
-------------------------

No build-pipeline runs, no JSON Schema validation libraries (stdlib
only per ADR-0004), no fixture generation. Each test reads one or two
JSON files, builds a ``set``, and compares against the TypedDict
``__annotations__`` dict — total runtime well under 200 ms.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def types_module():
    """Import ``tools.build.models`` without permanently mutating ``sys.path``.

    The fixture is still named ``types_module`` for backwards-compatibility
    with the existing test bodies; the underlying module was renamed from
    ``types.py`` to ``models.py`` because ``types`` shadows the stdlib
    ``types`` module on ``sys.path[0]`` when ``python3 tools/build/build.py``
    is invoked directly (Python 3.12 surfaces this as a circular-import
    failure during ``import argparse``).

    The repository's Python tree puts ``tools/build/`` on ``sys.path``
    via the ``pyproject.toml`` ``pythonpath = ["tools"]`` setting in
    most invocations, but plain ``pytest`` from the repo root needs the
    explicit injection. We restore ``sys.path`` after import so other
    tests that don't expect ``tools/`` on the path stay unaffected.
    """
    sys.path.insert(0, str(REPO_ROOT / "tools"))
    try:
        from build import models  # noqa: PLC0415

        return models
    finally:
        try:
            sys.path.remove(str(REPO_ROOT / "tools"))
        except ValueError:
            pass


# ---------------------------------------------------------------------------
# UseCase ↔ schemas/uc.schema.json
# ---------------------------------------------------------------------------


def test_use_case_typed_dict_matches_schema(types_module):
    """Every property in ``uc.schema.json`` has a matching :class:`UseCase` field.

    The single allowed difference is the ``$schema`` IDE hint, which is
    a JSON Schema convention and not legal as a Python identifier. We
    handle that field separately at the JSON layer (the build strips
    it before validation).
    """
    schema = json.loads((REPO_ROOT / "schemas" / "uc.schema.json").read_text())
    schema_keys = set(schema["properties"].keys())
    schema_keys.discard("$schema")

    typed_keys = set(types_module.UseCase.__annotations__.keys())

    missing_in_typed = schema_keys - typed_keys
    extra_in_typed = typed_keys - schema_keys

    assert not missing_in_typed, (
        f"{sorted(missing_in_typed)} were added to uc.schema.json but not "
        f"to tools/build/models.py:UseCase. Update the TypedDict so static "
        f"type checking continues to cover the new fields."
    )
    assert not extra_in_typed, (
        f"{sorted(extra_in_typed)} are declared in tools/build/models.py:UseCase "
        f"but no longer exist in uc.schema.json. Remove the dead fields or "
        f"restore them to the schema."
    )


# ---------------------------------------------------------------------------
# Catalog ↔ catalog.json (wire format)
# ---------------------------------------------------------------------------


def _collect_keys(items, attribute=None):
    """Union all keys of every dict in ``items`` (optionally ``v[attribute]``)."""
    keys: set[str] = set()
    for item in items:
        v = item if attribute is None else item.get(attribute, {})
        if isinstance(v, dict):
            keys.update(v.keys())
    return keys


def test_catalog_typed_dicts_match_real_payload(types_module):
    """Every key in ``catalog.json`` has a matching TypedDict field.

    Reads ``dist/catalog.json`` as the ground-truth wire format (per
    ADR-0009 the SSOT-derived dist copy is authoritative as of P1 step
    5b, 2026-05-08). The legacy project-root ``catalog.json`` is used
    as a fallback only for the brief P1 step 5c transition window
    (one release of consumer-fallback exercise before the legacy file
    is finally `git rm`-ed). When neither exists the test skips —
    that's the post-deletion expected state and the build pipeline
    itself is exercised by ``tests/build/test_render_legacy_artifacts.py``.
    """
    candidate_dist = REPO_ROOT / "dist" / "catalog.json"
    candidate_legacy = REPO_ROOT / "catalog.json"
    if candidate_dist.exists():
        catalog_path = candidate_dist
    elif candidate_legacy.exists():
        catalog_path = candidate_legacy
    else:
        import pytest  # noqa: PLC0415

        pytest.skip(
            "Neither dist/catalog.json nor catalog.json exists. "
            "Run `make build` to generate dist/."
        )
    catalog = json.loads(catalog_path.read_text())

    # 1. Catalog top-level keys.
    expected_top = set(catalog.keys())
    typed_top = set(types_module.CatalogJson.__annotations__.keys())
    assert expected_top == typed_top, (
        f"catalog.json top-level keys: real={sorted(expected_top)!r}, "
        f"TypedDict={sorted(typed_top)!r}. Update tools/build/models.py:CatalogJson."
    )

    # 2. Per-category keys.
    cat_keys = {k for c in catalog["DATA"] for k in c.keys()}
    typed_cat = set(types_module.CatalogCategory.__annotations__.keys())
    assert cat_keys.issubset(typed_cat), (
        f"CatalogCategory missing fields: {sorted(cat_keys - typed_cat)!r}"
    )

    # 3. Per-subcategory keys.
    sub_keys = {k for c in catalog["DATA"] for s in c["s"] for k in s.keys()}
    typed_sub = set(types_module.CatalogSubcategory.__annotations__.keys())
    assert sub_keys.issubset(typed_sub), (
        f"CatalogSubcategory missing fields: {sorted(sub_keys - typed_sub)!r}"
    )

    # 4. Per-UC keys.
    uc_keys = {
        k
        for c in catalog["DATA"]
        for s in c["s"]
        for u in s["u"]
        for k in u.keys()
    }
    typed_uc = set(types_module.CatalogUC.__annotations__.keys())
    assert uc_keys.issubset(typed_uc), (
        f"CatalogUC missing fields (real keys not in TypedDict): "
        f"{sorted(uc_keys - typed_uc)!r}"
    )

    # 5. CAT_META values.
    meta_keys = {k for v in catalog["CAT_META"].values() for k in v.keys()}
    typed_meta = set(types_module.CategoryMeta.__annotations__.keys())
    assert meta_keys.issubset(typed_meta), (
        f"CategoryMeta missing fields: {sorted(meta_keys - typed_meta)!r}"
    )

    # 6. EQUIPMENT entries.
    eq_keys = {k for v in catalog["EQUIPMENT"] for k in v.keys()}
    typed_eq = set(types_module.EquipmentEntry.__annotations__.keys())
    assert eq_keys.issubset(typed_eq), (
        f"EquipmentEntry missing fields: {sorted(eq_keys - typed_eq)!r}"
    )

    # 7. implementationRoadmap inner-entry keys.
    rm_keys = {
        k
        for v in catalog.get("implementationRoadmap", {}).values()
        for k in v.keys()
    }
    typed_rm = set(types_module.ImplementationRoadmapEntry.__annotations__.keys())
    assert rm_keys.issubset(typed_rm), (
        f"ImplementationRoadmapEntry missing fields: "
        f"{sorted(rm_keys - typed_rm)!r}"
    )


# ---------------------------------------------------------------------------
# RegulationFramework ↔ data/regulations.json
# ---------------------------------------------------------------------------


def test_regulation_typed_dicts_match_real_payload(types_module):
    """Every key under ``data/regulations.json#frameworks[]`` has a TypedDict field.

    ``$comment`` is an authoring-only marker (Python can't even use it
    as an identifier) and is intentionally excluded from
    :class:`RegulationFramework`.
    """
    regs = json.loads((REPO_ROOT / "data" / "regulations.json").read_text())

    fw_keys = {k for fw in regs["frameworks"] for k in fw.keys()}
    fw_keys.discard("$comment")
    typed_fw = set(types_module.RegulationFramework.__annotations__.keys())
    assert fw_keys.issubset(typed_fw), (
        f"RegulationFramework missing fields: {sorted(fw_keys - typed_fw)!r}"
    )

    ver_keys = {
        k
        for fw in regs["frameworks"]
        for v in fw.get("versions", [])
        for k in v.keys()
    }
    typed_ver = set(types_module.RegulationVersionEntry.__annotations__.keys())
    assert ver_keys.issubset(typed_ver), (
        f"RegulationVersionEntry missing fields: {sorted(ver_keys - typed_ver)!r}"
    )

    cc_keys = {
        k
        for fw in regs["frameworks"]
        for v in fw.get("versions", [])
        for cc in v.get("commonClauses", [])
        for k in cc.keys()
    }
    typed_cc = set(types_module.RegulationCommonClause.__annotations__.keys())
    assert cc_keys.issubset(typed_cc), (
        f"RegulationCommonClause missing fields: {sorted(cc_keys - typed_cc)!r}"
    )


# ---------------------------------------------------------------------------
# Typed helpers — pin the cardinality.
# ---------------------------------------------------------------------------


def test_typed_helpers_return_keysets(types_module):
    """:func:`use_case_typed_keys` and :func:`catalog_uc_typed_keys` are non-empty.

    Pin the field counts so an accidental dataclass-style removal of a
    TypedDict field that breaks downstream consumers lights up here
    before the integration tests do.
    """
    uc_keys = types_module.use_case_typed_keys()
    cu_keys = types_module.catalog_uc_typed_keys()

    # Lower bound: schema is at least 40 fields. Asserting >= 40 lets
    # the schema grow without breaking the test, while still flagging
    # a regression that strips half the model.
    assert len(uc_keys) >= 40, (
        f"UseCase TypedDict shrunk to {len(uc_keys)} fields — likely "
        f"an accidental removal. Schema currently has 48 fields."
    )
    assert len(cu_keys) >= 40, (
        f"CatalogUC TypedDict shrunk to {len(cu_keys)} fields — likely "
        f"an accidental removal. Wire format currently has 46 fields."
    )

    # Helpers must return sets, not dict-keys-views (callers may mutate).
    assert isinstance(uc_keys, set)
    assert isinstance(cu_keys, set)


# ---------------------------------------------------------------------------
# Smoke-test: a real UC sidecar can be assigned to the UseCase TypedDict.
# ---------------------------------------------------------------------------


def test_real_uc_sidecar_is_structurally_a_use_case(types_module):
    """A loaded UC sidecar is a structural :class:`UseCase` at runtime.

    TypedDict instances are plain dicts at runtime — there's no
    ``isinstance`` check available — so we verify (a) every key in the
    sidecar is a declared TypedDict field, and (b) the required fields
    (``id``, ``title``) are present. That's the strongest check Python
    gives us without pulling in pydantic.
    """
    sample_path = (
        REPO_ROOT
        / "content"
        / "cat-17-network-security-zero-trust"
        / "UC-17.1.1.json"
    )
    sample = json.loads(sample_path.read_text())

    typed_keys = set(types_module.UseCase.__annotations__.keys())
    sample_keys = set(sample.keys())
    sample_keys.discard("$schema")

    assert sample_keys.issubset(typed_keys), (
        f"UC-17.1.1 carries fields {sorted(sample_keys - typed_keys)!r} "
        f"that are not declared in tools/build/models.py:UseCase."
    )
    assert "id" in sample, "UC sidecar missing required 'id' field"
    assert "title" in sample, "UC sidecar missing required 'title' field"
