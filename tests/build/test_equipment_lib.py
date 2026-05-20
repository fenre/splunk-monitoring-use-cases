"""Tests for scripts/equipment_lib.py — shared equipment accessor."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = str(REPO_ROOT / "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from equipment_lib import load_equipment, compile_patterns, match_equipment  # noqa: E402


class TestLoadEquipment:
    def test_returns_list(self):
        eq = load_equipment()
        assert isinstance(eq, list)
        assert len(eq) > 50

    def test_entries_have_required_keys(self):
        for entry in load_equipment():
            assert "id" in entry
            assert "tas" in entry


class TestCompilePatterns:
    def test_returns_patterns(self):
        pats = compile_patterns()
        assert isinstance(pats, list)
        assert len(pats) > 100

    def test_pattern_tuples_have_three_elements(self):
        for pat in compile_patterns()[:10]:
            assert len(pat) == 3
            pattern_lower, eq_id, model_id = pat
            assert isinstance(pattern_lower, str)
            assert isinstance(eq_id, str)
            assert model_id is None or isinstance(model_id, str)


class TestMatchEquipment:
    def test_match_linux_ta(self):
        pats = compile_patterns()
        eq_ids, model_ids = match_equipment("Splunk_TA_nix for Linux monitoring", pats)
        assert "linux" in eq_ids

    def test_match_vmware(self):
        pats = compile_patterns()
        eq_ids, model_ids = match_equipment("Splunk_TA_vmware vSphere monitoring", pats)
        assert "vmware" in eq_ids

    def test_no_match_for_gibberish(self):
        pats = compile_patterns()
        eq_ids, model_ids = match_equipment("xyzzy12345", pats)
        assert len(eq_ids) == 0


class TestLoadEquipmentDefensiveBranches:
    """Pin the two ``raise RuntimeError`` branches in ``load_equipment``
    that fire when the upstream ``EQUIPMENT`` SSOT is corrupted. The
    branches are unreachable from the production registry (which is a
    well-formed list of dicts), so we monkeypatch the cached SSOT
    reference to inject malformed shapes.

    Both tests reset the module-level ``_CACHE`` to None first so the
    function's early-return doesn't short-circuit the validation.
    """

    def setup_method(self) -> None:
        """Drain the load_equipment cache before each defensive test
        so the validation branches we're targeting actually run."""
        import equipment_lib as eq_mod

        eq_mod._CACHE = None

    def teardown_method(self) -> None:
        """Drain again on exit so the next test (and the rest of the
        suite) sees a clean cache slot."""
        import equipment_lib as eq_mod

        eq_mod._CACHE = None

    # NOTE: ``equipment_lib.load_equipment`` line 62 raises if
    # ``list(_SSOT_EQUIPMENT)`` doesn't produce a list. ``list(x)``
    # in CPython is guaranteed to return a list for any iterable
    # input — and ``_SSOT_EQUIPMENT`` is constrained upstream to be
    # iterable. We document the branch as **unreachable in practice**
    # but retain it as a tripwire against future refactors that
    # replace the ``list(...)`` conversion with something else.

    def test_raises_when_entry_is_malformed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Line 66-67: every EQUIPMENT entry must be a dict with both
        ``id`` and ``tas`` keys. Pin the per-entry validation by
        stubbing the upstream registry with a malformed entry.
        """
        import equipment_lib as eq_mod

        # Replace the SSOT reference with a single malformed entry.
        # The function does ``list(_SSOT_EQUIPMENT)`` so we provide an
        # iterable whose first entry trips the validator.
        monkeypatch.setattr(
            eq_mod,
            "_SSOT_EQUIPMENT",
            [{"id": "x"}],  # missing ``tas`` key
        )
        with pytest.raises(RuntimeError, match="EQUIPMENT entry malformed"):
            eq_mod.load_equipment()

    def test_raises_when_entry_is_not_a_dict(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Companion to the malformed-dict case: a non-dict entry (e.g.
        a stray string or ``None``) must also trip the validator. Pin
        the ``isinstance(entry, dict)`` half of the same check."""
        import equipment_lib as eq_mod

        monkeypatch.setattr(
            eq_mod, "_SSOT_EQUIPMENT", ["not-a-dict"]
        )
        with pytest.raises(RuntimeError, match="EQUIPMENT entry malformed"):
            eq_mod.load_equipment()
