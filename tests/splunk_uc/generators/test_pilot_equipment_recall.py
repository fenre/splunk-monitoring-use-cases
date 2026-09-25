"""Live precision/recall checks for the six pilot equipment slugs."""

from __future__ import annotations

import json
from pathlib import Path

from splunk_uc.generators import equipment_tags as et

CONTENT = Path(__file__).resolve().parents[3] / "content"


def _sidecars():
    for path in sorted(CONTENT.glob("cat-*/UC-*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        yield path, data


def test_ise_titled_ucs_receive_cisco_ise() -> None:
    misses = []
    for path, data in _sidecars():
        title = str(data.get("title") or "")
        if "Cisco ISE" not in title and "Identity Services Engine" not in title:
            continue
        eq, _ = et._refine_pilot_tags(data, set(), set())
        if "cisco_ise" not in eq:
            misses.append(f"{data.get('id')} {title}")
    assert misses == [], misses[:20]


def test_paloalto_not_on_vmware_titles() -> None:
    hits = []
    for path, data in _sidecars():
        title = str(data.get("title") or "")
        if "VMware" not in title and "vSphere" not in title and "vCenter" not in title:
            continue
        if "Palo Alto" in title:
            continue
        eq = set(data.get("equipment") or [])
        if "paloalto" in eq:
            hits.append(f"{data.get('id')} {title}")
    assert hits == [], hits[:20]
