"""The graph export is derived from the fabric, then written for graph.html."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from splunk_uc.fabric.graph import presentation_graph
from splunk_uc.fabric.resolve import Fabric

_SCRIPT_PATH = Path(__file__).resolve().parents[2] / "tools" / "build-graph-data.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("tools_build_graph_data_for_tests", _SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fabric() -> Fabric:
    entities = [
        {"id": "5.1.1", "type": "usecase", "label": "Up", "aliases": []},
        {"id": "1.1.1", "type": "usecase", "label": "Other", "aliases": []},
        {"id": "cisco", "type": "vendorProduct", "label": "Cisco", "aliases": []},
        {"id": "authentication", "type": "cimDataset", "label": "Authentication", "aliases": []},
    ]
    relationships = [
        ("5.1.1", "requires", "1.1.1", "authored", 1.0),
    ]
    return Fabric(
        entities=entities,
        relationships=relationships,
        members={
            "5.1.1": {
                "sourcetype": [],
                "vendorProduct": ["cisco", "cisco", "cisco"],
                "addon": [],
                "cimDataset": ["authentication", "authentication"],
            },
            "1.1.1": {
                "sourcetype": [],
                "vendorProduct": ["cisco", "cisco", "cisco"],
                "addon": [],
                "cimDataset": [],
            },
        },
        pillars={"5.1.1": "Security", "1.1.1": "Observability"},
        rates={"ucCount": 2},
    )


def test_presentation_graph_keeps_pillars_and_relationship_rollups(tmp_path: Path) -> None:
    content = tmp_path / "content"
    for number, name in ((1, "Servers"), (5, "Network")):
        folder = content / f"cat-0{number}"
        folder.mkdir(parents=True)
        (folder / "_category.json").write_text(
            json.dumps({"id": number, "name": name, "description": name}),
            encoding="utf-8",
        )
    # Membership lists are already unique in the resolver. Repeat ids here
    # would over-count, so the fixture uses one id and the threshold is met
    # by giving both categories the same product three times via two UCs
    # plus a third synthetic member.
    fabric = _fabric()
    fabric.members["5.1.2"] = {
        "sourcetype": [],
        "vendorProduct": ["cisco"],
        "addon": [],
        "cimDataset": ["authentication"],
    }
    fabric.pillars["5.1.2"] = "Security"
    graph = presentation_graph(fabric, content=content)
    types = {node["type"] for node in graph["nodes"]}
    assert "pillar" in types
    assert any(node["id"] == "cat-5" and node["pillar"] == "Security" for node in graph["nodes"])
    assert any(edge["type"] == "uses-equipment" and edge["weight"] >= 3 for edge in graph["edges"])
    assert any(edge["type"] == "cross-ref" for edge in graph["edges"])
    assert any(edge["target"] == "pillar-IT Operations" for edge in graph["edges"])


def test_script_main_writes_graph_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_script()
    monkeypatch.setattr(module, "resolve", lambda: _fabric())
    monkeypatch.setattr(sys, "argv", ["build-graph-data", "--out", str(tmp_path)])
    assert module.main() == 0
    payload = json.loads((tmp_path / "graph-data.json").read_text(encoding="utf-8"))
    assert payload["nodes"]
    assert "stats" in payload
