"""Regression tests for repository scripts under ``scripts/`` (generators / ES TA build)."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = str(REPO_ROOT / "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)


def test_build_es_uc_value_one_line():
    """Whitespace-only ``v`` should not crash; newlines collapse to spaces."""
    from build_es import _uc_value_one_line

    assert _uc_value_one_line({}) == ""
    assert _uc_value_one_line({"v": ""}) == ""
    assert _uc_value_one_line({"v": "   "}) == ""
    assert _uc_value_one_line({"v": "hello\nworld"}) == "hello world"
    assert _uc_value_one_line({"v": "single line"}) == "single line"


def test_build_ta_parse_quickstart():
    from build_ta import parse_quickstart

    by_cat = parse_quickstart()
    assert isinstance(by_cat, dict)
    for cat_id, uc_ids in by_cat.items():
        assert isinstance(cat_id, int)
        assert isinstance(uc_ids, list)
        assert all(isinstance(x, str) for x in uc_ids)
    assert len(by_cat) >= 1
    assert any(len(v) > 0 for v in by_cat.values())


def test_import_generate_recommender_app():
    importlib.import_module("generate_recommender_app")
