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
