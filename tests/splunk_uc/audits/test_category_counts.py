"""Category-count audit: files are the source of truth for X.Y prefixes."""

from __future__ import annotations

import json
from pathlib import Path

from splunk_uc.audits.category_counts import audit_tree, main, write_tree


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _uc(uc_id: str) -> dict:
    return {"id": uc_id, "title": f"Use case {uc_id} title"}


def _category(subs: list[dict], total: int) -> dict:
    return {
        "$schema": "../../schemas/category.schema.json",
        "id": 5,
        "name": "Network",
        "slug": "cat-05-network",
        "shortSlug": "cat-05",
        "src": "cat-05.md",
        "icon": "networkDevices",
        "description": "Network devices.",
        "quickTip": "Send syslog.",
        "quickStart": [
            {
                "id": "5.3.1",
                "title": "Pool down",
                "criticality": "critical",
                "subcategory": "Load Balancers",
            }
        ],
        "subcategories": subs,
        "useCaseCount": total,
    }


def test_audit_flags_drift_and_write_preserves_metadata(tmp_path: Path) -> None:
    cat = tmp_path / "cat-05-network"
    _write(
        cat / "_category.json",
        _category(
            [
                {
                    "id": "5.1",
                    "name": "Routers",
                    "useCaseCount": 9,
                    "guide": "docs/guides/cisco-networks.md",
                },
                {"id": "5.9", "name": "Empty", "useCaseCount": 4, "guide": "docs/guides/gone.md"},
            ],
            13,
        ),
    )
    _write(cat / "UC-5.1.1.json", _uc("5.1.1"))
    _write(cat / "UC-5.1.2.json", _uc("5.1.2"))
    _write(cat / "UC-5.3.1.json", _uc("5.3.1"))

    issues, changes, placeholders = audit_tree(tmp_path)
    assert issues
    assert changes[0]["beforeTotal"] == 13
    assert changes[0]["afterTotal"] == 3
    assert placeholders == []

    write_tree(tmp_path)
    updated = json.loads((cat / "_category.json").read_text(encoding="utf-8"))
    by_id = {item["id"]: item for item in updated["subcategories"]}
    assert updated["useCaseCount"] == 3
    assert set(by_id) == {"5.1", "5.3"}
    assert by_id["5.1"]["name"] == "Routers"
    assert by_id["5.1"]["guide"] == "docs/guides/cisco-networks.md"
    assert by_id["5.1"]["useCaseCount"] == 2
    assert by_id["5.3"]["name"] == "Load Balancers"
    assert by_id["5.3"]["useCaseCount"] == 1
    assert "5.9" not in by_id
    clean, _, _ = audit_tree(tmp_path)
    assert clean == []


def test_legacy_suffix_with_no_files_is_dropped(tmp_path: Path) -> None:
    cat = tmp_path / "cat-22-regulatory"
    meta = _category(
        [
            {"id": "22.40", "name": "PCI", "useCaseCount": 1},
            {"id": "22.40-ext", "name": "PCI extended", "useCaseCount": 2, "guide": "docs/x.md"},
        ],
        3,
    )
    meta["id"] = 22
    meta["slug"] = "cat-22-regulatory"
    meta["shortSlug"] = "cat-22"
    _write(cat / "_category.json", meta)
    _write(cat / "UC-22.40.1.json", _uc("22.40.1"))
    _write(cat / "UC-22.40.2.json", _uc("22.40.2"))
    _write(cat / "UC-22.40.3.json", _uc("22.40.3"))

    assert main(["--write", "--content", str(tmp_path)]) == 0
    updated = json.loads((cat / "_category.json").read_text(encoding="utf-8"))
    ids = [item["id"] for item in updated["subcategories"]]
    assert ids == ["22.40"]
    assert updated["subcategories"][0]["useCaseCount"] == 3
    assert updated["useCaseCount"] == 3


def test_write_preserves_unicode_escapes(tmp_path: Path) -> None:
    cat = tmp_path / "cat-11-email"
    meta = _category([{"id": "11.1", "name": "Mail", "useCaseCount": 1}], 1)
    meta["description"] = "Mail \u2014 flow"
    text = json.dumps(meta, indent=2, ensure_ascii=True) + "\n"
    assert "\\u2014" in text
    (cat).mkdir()
    (cat / "_category.json").write_text(text, encoding="utf-8")
    _write(cat / "UC-11.1.1.json", _uc("11.1.1"))
    _write(cat / "UC-11.1.2.json", _uc("11.1.2"))
    assert main(["--write", "--content", str(tmp_path)]) == 0
    written = (cat / "_category.json").read_text(encoding="utf-8")
    assert "\\u2014" in written
    assert "\u2014" not in written


def test_missing_quick_start_label_is_a_placeholder(tmp_path: Path) -> None:
    cat = tmp_path / "cat-05-network"
    meta = _category([{"id": "5.1", "name": "Routers", "useCaseCount": 1}], 1)
    meta["quickStart"] = [
        {"id": "5.1.1", "title": "Up", "criticality": "critical", "subcategory": "Routers"}
    ]
    _write(cat / "_category.json", meta)
    _write(cat / "UC-5.1.1.json", _uc("5.1.1"))
    _write(cat / "UC-5.4.1.json", _uc("5.4.1"))

    assert main(["--write", "--content", str(tmp_path)]) == 0
    updated = json.loads((cat / "_category.json").read_text(encoding="utf-8"))
    added = next(item for item in updated["subcategories"] if item["id"] == "5.4")
    assert added["name"] == "5.4"
    assert main(["--check", "--content", str(tmp_path)]) == 0
