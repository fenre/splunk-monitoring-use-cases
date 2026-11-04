"""Tests for ``splunk_uc.generators.starter_packs``."""

from __future__ import annotations

import json
from pathlib import Path

from splunk_uc.generators import api_surface
from splunk_uc.generators import starter_packs as gen


def test_render_is_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "a"
    second = tmp_path / "b"
    gen.render(first)
    gen.render(second)
    names = sorted(p.name for p in first.glob("*.json"))
    assert "index.json" in names
    assert (first / "index.html").read_bytes() == (second / "index.html").read_bytes()
    assert b"Starter packs" in (first / "index.html").read_bytes()
    assert names == sorted(p.name for p in second.glob("*.json"))
    for name in names:
        assert (first / name).read_bytes() == (second / name).read_bytes()


def test_index_shape(tmp_path: Path) -> None:
    gen.render(tmp_path)
    index = json.loads((tmp_path / "index.json").read_text(encoding="utf-8"))
    assert index["apiVersion"] == "v1"
    assert index["packCount"] == len(index["packs"]) >= 10
    assert index["sourcetypeAliases"]
    for pack in index["packs"]:
        assert pack["goal"] in {"security", "operations"}
        assert pack["status"] in {"draft", "published"}
        assert pack["stepCount"] == len(pack["steps"])
        assert "$schema" not in pack
        assert [s["order"] for s in pack["steps"]] == list(range(1, len(pack["steps"]) + 1))
        for step in pack["steps"]:
            assert step["title"]
            assert step["url"] == f"/uc/{step['ucId']}/"
            assert step["sourcetypes"] or step["indexes"]
        detail = json.loads((tmp_path / f"{pack['id']}.json").read_text(encoding="utf-8"))
        assert detail["pack"] == pack


def test_check_mode_detects_drift(tmp_path: Path) -> None:
    out = tmp_path / "starter-packs"
    assert gen.main(["--out", str(out)]) == 0
    assert gen.main(["--check", "--out", str(out)]) == 0
    (out / "index.json").write_text("{}\n", encoding="utf-8")
    assert gen.main(["--check", "--out", str(out)]) == 1


def test_check_mode_without_tree_only_renders(tmp_path: Path) -> None:
    assert gen.main(["--check", "--out", str(tmp_path / "missing")]) == 0


def test_subtree_is_external_to_api_surface() -> None:
    assert "starter-packs" in api_surface._EXTERNAL_SUBTREES
    assert api_surface._is_external(Path("starter-packs/index.json"))
