"""Example-based unit tests for ``scripts/equipment_lib.py``.

Complements ``test_equipment_lib_properties.py``: the property suite
covers the algebraic invariants of ``match_equipment`` and
``compile_patterns`` against arbitrary synthetic input. This file
covers the small set of guards that property tests can't reach:

1. ``load_equipment`` raises ``RuntimeError`` when an entry is
   missing the required ``id``/``tas`` keys (line 67 guard).
2. ``compile_patterns(None)`` falls through to ``load_equipment()``
   (line 89 — the only path that uses the real registry instead of
   the caller-supplied list).
3. The cache short-circuit returns the same list object on a
   second call (no re-validation overhead).

Hermetic isolation
------------------

Tests use ``monkeypatch`` to swap ``equipment_lib._SSOT_EQUIPMENT``
and reset ``equipment_lib._CACHE`` per test, so they don't
contaminate the real registry that
``test_equipment_lib_properties.py::test_real_equipment_registry_round_trips``
depends on.

Coverage attribution note
-------------------------

We import via the same in-tree ``equipment_lib`` module name that
``tests/build/test_equipment_lib.py`` already uses (NOT the
``importlib.util.spec_from_file_location`` shim used by
``test_equipment_lib_properties.py``). Using the canonical module
name is required so ``coverage`` attributes the lines we exercise
back to ``scripts/equipment_lib.py`` instead of a synthetic
"equipment_lib_module" loader name.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = str(REPO_ROOT / "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import equipment_lib  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_equipment_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reset the module-level cache before every test so each test
    sees a fresh ``load_equipment()`` invocation."""
    monkeypatch.setattr(equipment_lib, "_CACHE", None)


class TestLoadEquipmentGuards:
    def test_malformed_entry_missing_id_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An EQUIPMENT entry without an ``id`` key must trip the
        line-67 ``raise RuntimeError`` guard."""
        bad = [{"tas": ["foo"]}]  # missing ``id``
        monkeypatch.setattr(equipment_lib, "_SSOT_EQUIPMENT", bad)
        with pytest.raises(RuntimeError, match="EQUIPMENT entry malformed"):
            equipment_lib.load_equipment()

    def test_malformed_entry_missing_tas_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An EQUIPMENT entry without a ``tas`` key must also trip
        line 67. Both keys are part of the contract."""
        bad = [{"id": "cisco"}]  # missing ``tas``
        monkeypatch.setattr(equipment_lib, "_SSOT_EQUIPMENT", bad)
        with pytest.raises(RuntimeError, match="EQUIPMENT entry malformed"):
            equipment_lib.load_equipment()

    def test_malformed_entry_not_dict_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A non-dict entry (e.g. tuple or list) also trips line 67."""
        bad = [("cisco", ["foo"])]
        monkeypatch.setattr(equipment_lib, "_SSOT_EQUIPMENT", bad)
        with pytest.raises(RuntimeError, match="EQUIPMENT entry malformed"):
            equipment_lib.load_equipment()


class TestLoadEquipmentCache:
    def test_second_call_returns_cached_list_identity(self) -> None:
        """Second invocation hits the cache short-circuit at line
        59 and returns the exact same list object — proves the
        cache survives across calls and that the guard runs once."""
        first = equipment_lib.load_equipment()
        second = equipment_lib.load_equipment()
        assert first is second


class TestMatchEquipmentEmptyTextGuard:
    def test_empty_text_returns_empty_sets(self) -> None:
        """Pins the line-141 ``if not text: return set(), set()`` guard.
        The property suite covers this for arbitrary pattern sets,
        but it loads ``equipment_lib`` via ``importlib`` with a
        different module name. We re-cover the same line here using
        the canonical ``equipment_lib`` import so this test file
        achieves the gap-closing line attribution on its own."""
        patterns = equipment_lib.compile_patterns()
        eq_ids, models = equipment_lib.match_equipment("", patterns)
        assert eq_ids == set()
        assert models == set()


class TestCompilePatternsNoneFallthrough:
    def test_compile_patterns_with_none_loads_real_registry(self) -> None:
        """``compile_patterns(None)`` must invoke ``load_equipment()``
        instead of throwing on a missing argument. Pins the line-89
        branch where ``equipment is None`` short-circuits to the
        registry instead of being treated as "no patterns"."""
        from_default = equipment_lib.compile_patterns()
        from_explicit_none = equipment_lib.compile_patterns(None)
        assert from_default == from_explicit_none
        assert from_default, "real registry must yield at least one pattern"

    def test_compile_patterns_with_empty_list_returns_empty(self) -> None:
        """The complementary contract: ``compile_patterns([])`` must
        NOT silently fall through to the registry. The empty-list
        path was the bug surfaced by P16 (the previous ``equipment
        or load_equipment()`` expression treated ``[]`` as falsy)."""
        assert equipment_lib.compile_patterns([]) == []
