#!/usr/bin/env python3
"""Tier-A uplift for regulation subcategories — mechanical metadata fixes.

Same fixes as the NIS2 uplift, parameterized per regulation:

1. Add splunkVersions if missing
2. Add reviewer if missing (regulation-specific team)
3. Fix cimModels: ["N/A"] → []
4. Add premiumApps where ES/SOAR/ITSI referenced but not declared
5. Remove dataModelAcceleration when "Not applicable" and cimModels empty
6. Remove empty cimSpl strings when cimModels is empty

Usage:
  python3 scripts/uplift_regulation_tier_a.py --subcat 22.1 --reviewer @gdpr-evidence-pack-maintainers
  python3 scripts/uplift_regulation_tier_a.py --subcat 22.3 --reviewer @dora-evidence-pack-maintainers
  python3 scripts/uplift_regulation_tier_a.py --subcat 22.6 --reviewer @iso27001-evidence-pack-maintainers
  python3 scripts/uplift_regulation_tier_a.py --subcat 22.9 --reviewer @iso27001-evidence-pack-maintainers
"""
from __future__ import annotations

import argparse
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


def fix_file(path: Path, reviewer: str) -> list[str]:
    raw = path.read_text("utf-8")
    data = json.loads(raw)
    changes: list[str] = []

    if "splunkVersions" not in data:
        data["splunkVersions"] = ["9.2+", "Cloud"]
        changes.append("added splunkVersions")

    if "reviewer" not in data:
        data["reviewer"] = reviewer
        changes.append("added reviewer")

    if data.get("cimModels") == ["N/A"]:
        data["cimModels"] = []
        changes.append('cimModels ["N/A"] → []')

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

    if data.get("dataModelAcceleration") == "Not applicable":
        cim = data.get("cimModels", [])
        if not cim or cim == ["N/A"]:
            del data["dataModelAcceleration"]
            changes.append("removed dataModelAcceleration 'Not applicable'")

    cim = data.get("cimModels", [])
    if data.get("cimSpl") == "" and (not cim or cim == ["N/A"]):
        del data["cimSpl"]
        changes.append("removed empty cimSpl")

    if not changes:
        return []

    out = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    path.write_text(out, "utf-8")
    return changes


def main() -> None:
    parser = argparse.ArgumentParser(description="Tier-A metadata uplift")
    parser.add_argument("--subcat", required=True, help="Subcategory prefix, e.g. 22.1")
    parser.add_argument("--reviewer", required=True, help="Reviewer team handle")
    args = parser.parse_args()

    pattern = f"UC-{args.subcat}.*.json"
    files = sorted(CONTENT.glob(pattern), key=lambda p: _sort_key(p.stem))
    print(f"Scanning {len(files)} UCs for subcat {args.subcat}...")

    modified = 0
    for f in files:
        ch = fix_file(f, args.reviewer)
        if ch:
            uid = f.stem.replace("UC-", "")
            print(f"  UC-{uid}: {', '.join(ch)}")
            modified += 1

    if modified == 0:
        print("No changes needed.")
    else:
        print(f"\nModified {modified}/{len(files)} files.")


def _sort_key(stem: str) -> tuple[int, ...]:
    parts = stem.replace("UC-", "").split(".")
    return tuple(int(p) for p in parts if p.isdigit())


if __name__ == "__main__":
    main()
