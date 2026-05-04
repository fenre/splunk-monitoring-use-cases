#!/usr/bin/env python3
"""One-shot Tier-A uplift for NIS2 (22.2.*) use cases.

Mechanical fixes that bring metadata parity with UC-1.1.1:

1. Add splunkVersions if missing
2. Add reviewer if missing
3. Fix cimModels: ["N/A"] → []
4. Add premiumApps where ES/SOAR referenced in app but not declared
5. Remove dataModelAcceleration when "Not applicable"
6. Remove empty cimSpl strings when cimModels is empty/N/A

Run:  python3 scripts/uplift_nis2_gold.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONTENT = REPO / "content" / "cat-22-regulatory-compliance"

PREMIUM_APPS = {
    "Splunk Enterprise Security": re.compile(
        r"Splunk\s+Enterprise\s+Security|Splunkbase\s+263|splunkbase\.splunk\.com/app/263",
        re.IGNORECASE,
    ),
    "Splunk SOAR": re.compile(
        r"Splunk\s+SOAR|Splunkbase\s+(?:3411|5165)|Phantom",
        re.IGNORECASE,
    ),
    "Splunk ITSI": re.compile(
        r"Splunk\s+ITSI|IT\s+Service\s+Intelligence|SA-ITOA",
        re.IGNORECASE,
    ),
}

CHANGES: dict[str, list[str]] = {}


def fix_file(path: Path) -> None:
    raw = path.read_text("utf-8")
    data = json.loads(raw)
    changes: list[str] = []

    # 1. splunkVersions
    if "splunkVersions" not in data:
        data["splunkVersions"] = ["9.2+", "Cloud"]
        changes.append("added splunkVersions")

    # 2. reviewer
    if "reviewer" not in data:
        data["reviewer"] = "@nis2-evidence-pack-maintainers"
        changes.append("added reviewer")

    # 3. cimModels N/A → []
    if data.get("cimModels") == ["N/A"]:
        data["cimModels"] = []
        changes.append('cimModels ["N/A"] → []')

    # 4. premiumApps
    text_fields = " ".join(
        str(data.get(f, "")) for f in ("app", "dataSources", "spl", "implementation")
    )
    existing_premium = set()
    for entry in data.get("premiumApps", []):
        if isinstance(entry, str):
            existing_premium.add(entry)
        elif isinstance(entry, dict):
            existing_premium.add(entry.get("name", ""))

    for name, regex in PREMIUM_APPS.items():
        if name not in existing_premium and regex.search(text_fields):
            if "premiumApps" not in data:
                data["premiumApps"] = []
            data["premiumApps"].append(name)
            changes.append(f"added premiumApps: {name}")

    # 5. dataModelAcceleration "Not applicable" → remove
    if data.get("dataModelAcceleration") == "Not applicable":
        cim = data.get("cimModels", [])
        if not cim or cim == ["N/A"]:
            del data["dataModelAcceleration"]
            changes.append("removed dataModelAcceleration 'Not applicable'")

    # 6. empty cimSpl when no CIM models
    cim = data.get("cimModels", [])
    if data.get("cimSpl") == "" and (not cim or cim == ["N/A"]):
        del data["cimSpl"]
        changes.append("removed empty cimSpl")

    if not changes:
        return

    out = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    path.write_text(out, "utf-8")
    CHANGES[data["id"]] = changes


def main() -> None:
    files = sorted(CONTENT.glob("UC-22.2.*.json"), key=lambda p: _sort_key(p.stem))
    print(f"Scanning {len(files)} NIS2 UC files...")

    for f in files:
        fix_file(f)

    if not CHANGES:
        print("No changes needed.")
        return

    print(f"\nModified {len(CHANGES)} files:")
    for uid, ch in sorted(CHANGES.items(), key=lambda x: _sort_key_id(x[0])):
        print(f"  UC-{uid}: {', '.join(ch)}")


def _sort_key(stem: str) -> tuple[int, ...]:
    parts = stem.replace("UC-", "").split(".")
    return tuple(int(p) for p in parts if p.isdigit())


def _sort_key_id(uid: str) -> tuple[int, ...]:
    return tuple(int(p) for p in uid.split(".") if p.isdigit())


if __name__ == "__main__":
    main()
