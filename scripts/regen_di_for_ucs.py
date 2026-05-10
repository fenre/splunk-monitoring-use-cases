#!/usr/bin/env python3
"""Regenerate ``detailedImplementation`` for an explicit list of UC sidecars.

The build pipeline only auto-generates ``detailedImplementation`` when the
field is missing; once written into the JSON it is treated as frozen. After we
hand-rewrite ``spl`` / ``dataSources`` / ``implementation`` for a UC, the
surrounding "Prerequisites / Step 1 / Pipeline walkthrough" prose drifts out
of sync with the new SPL. This script rebuilds that prose by calling the
canonical generator in ``tools/build/enrichment.py``.

Usage:
    python3 scripts/regen_di_for_ucs.py path/to/UC-X.Y.Z.json [path ...]
    python3 scripts/regen_di_for_ucs.py --meraki-rewrites
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from tools.build.enrichment import generate_detailed_impl  # noqa: E402


# Canonical field -> abbreviated key in catalog.json. The generator works on
# the abbreviated form, so we translate before calling.
FIELD_MAP = {
    "title": "n",
    "description": "v",
    "value": "v",
    "criticality": "c",
    "difficulty": "f",
    "monitoringType": "x",
    "splunkPillar": "sp",
    "dataSources": "d",
    "app": "t",
    "spl": "q",
    "cimSpl": "qs",
    "implementation": "m",
    "visualization": "z",
    "cimModels": "a",
    "script": "script",
    "knownFalsePositives": "kfp",
}


def to_abbrev(uc: dict) -> dict:
    """Translate canonical UC fields to the abbreviated keys the generator expects."""
    abbrev: dict = {}
    for canonical, abbreviated in FIELD_MAP.items():
        if canonical in uc:
            abbrev[abbreviated] = uc[canonical]
    return abbrev


# Default rewrite set: the UCs we just hand-rewrote in
# ``scripts/rewrite_meraki_uc_spl.py``. Keep in sync.
MERAKI_REWRITES = [
    "content/cat-14-iot-operational-technology-ot/UC-14.1.15.json",
    "content/cat-14-iot-operational-technology-ot/UC-14.1.16.json",
    "content/cat-14-iot-operational-technology-ot/UC-14.1.17.json",
    "content/cat-14-iot-operational-technology-ot/UC-14.1.18.json",
    "content/cat-14-iot-operational-technology-ot/UC-14.1.19.json",
    "content/cat-14-iot-operational-technology-ot/UC-14.1.20.json",
    "content/cat-14-iot-operational-technology-ot/UC-14.1.21.json",
    "content/cat-14-iot-operational-technology-ot/UC-14.1.22.json",
    "content/cat-14-iot-operational-technology-ot/UC-14.1.23.json",
    "content/cat-14-iot-operational-technology-ot/UC-14.1.24.json",
    "content/cat-15-data-center-physical-infrastructure/UC-15.3.22.json",
    "content/cat-15-data-center-physical-infrastructure/UC-15.3.23.json",
    "content/cat-15-data-center-physical-infrastructure/UC-15.3.24.json",
    "content/cat-15-data-center-physical-infrastructure/UC-15.3.25.json",
    "content/cat-15-data-center-physical-infrastructure/UC-15.3.26.json",
    "content/cat-15-data-center-physical-infrastructure/UC-15.3.27.json",
    "content/cat-15-data-center-physical-infrastructure/UC-15.3.28.json",
    "content/cat-15-data-center-physical-infrastructure/UC-15.3.29.json",
    "content/cat-15-data-center-physical-infrastructure/UC-15.3.30.json",
    "content/cat-09-identity-access-management/UC-9.6.1.json",
    "content/cat-09-identity-access-management/UC-9.6.2.json",
    "content/cat-09-identity-access-management/UC-9.6.3.json",
    "content/cat-09-identity-access-management/UC-9.6.4.json",
    "content/cat-09-identity-access-management/UC-9.6.5.json",
    "content/cat-09-identity-access-management/UC-9.6.6.json",
]


# Second wave: the 39 UCs we hand-rewrote in
# ``scripts/rewrite_meraki_devices_misuse.py`` to fix the meraki:devices misuse.
MERAKI_DEVICES_FIX = [
    "content/cat-05-network-infrastructure/UC-5.1.36.json",
    "content/cat-05-network-infrastructure/UC-5.1.37.json",
    "content/cat-05-network-infrastructure/UC-5.1.45.json",
    "content/cat-05-network-infrastructure/UC-5.1.46.json",
    "content/cat-05-network-infrastructure/UC-5.1.47.json",
    "content/cat-05-network-infrastructure/UC-5.1.52.json",
    "content/cat-05-network-infrastructure/UC-5.1.53.json",
    "content/cat-05-network-infrastructure/UC-5.1.55.json",
    "content/cat-05-network-infrastructure/UC-5.2.27.json",
    "content/cat-05-network-infrastructure/UC-5.2.33.json",
    "content/cat-05-network-infrastructure/UC-5.2.40.json",
    "content/cat-05-network-infrastructure/UC-5.4.3.json",
    "content/cat-05-network-infrastructure/UC-5.4.5.json",
    "content/cat-05-network-infrastructure/UC-5.4.13.json",
    "content/cat-05-network-infrastructure/UC-5.4.15.json",
    "content/cat-05-network-infrastructure/UC-5.4.16.json",
    "content/cat-05-network-infrastructure/UC-5.4.18.json",
    "content/cat-05-network-infrastructure/UC-5.4.19.json",
    "content/cat-05-network-infrastructure/UC-5.4.21.json",
    "content/cat-05-network-infrastructure/UC-5.4.24.json",
    "content/cat-05-network-infrastructure/UC-5.4.25.json",
    "content/cat-05-network-infrastructure/UC-5.4.27.json",
    "content/cat-05-network-infrastructure/UC-5.4.28.json",
    "content/cat-05-network-infrastructure/UC-5.4.29.json",
    "content/cat-05-network-infrastructure/UC-5.4.30.json",
    "content/cat-05-network-infrastructure/UC-5.4.31.json",
    "content/cat-05-network-infrastructure/UC-5.6.15.json",
    "content/cat-05-network-infrastructure/UC-5.8.2.json",
    "content/cat-05-network-infrastructure/UC-5.8.9.json",
    "content/cat-05-network-infrastructure/UC-5.8.10.json",
    "content/cat-05-network-infrastructure/UC-5.8.12.json",
    "content/cat-05-network-infrastructure/UC-5.8.13.json",
    "content/cat-05-network-infrastructure/UC-5.8.17.json",
    "content/cat-05-network-infrastructure/UC-5.8.18.json",
    "content/cat-05-network-infrastructure/UC-5.8.19.json",
    "content/cat-05-network-infrastructure/UC-5.8.23.json",
    "content/cat-05-network-infrastructure/UC-5.13.70.json",
    "content/cat-05-network-infrastructure/UC-5.13.73.json",
    "content/cat-15-data-center-physical-infrastructure/UC-15.3.28.json",
]


# Third wave: the 31 UCs we hand-rewrote in
# ``scripts/rewrite_meraki_sc4s_misuse.py`` to fix SC4S syslog misuse
# (wrong type=, fake signature= matching, admin-activity in syslog).
MERAKI_SC4S_FIX = [
    "content/cat-05-network-infrastructure/UC-5.1.38.json",
    "content/cat-05-network-infrastructure/UC-5.1.39.json",
    "content/cat-05-network-infrastructure/UC-5.1.40.json",
    "content/cat-05-network-infrastructure/UC-5.1.41.json",
    "content/cat-05-network-infrastructure/UC-5.1.42.json",
    "content/cat-05-network-infrastructure/UC-5.1.43.json",
    "content/cat-05-network-infrastructure/UC-5.1.44.json",
    "content/cat-05-network-infrastructure/UC-5.1.48.json",
    "content/cat-05-network-infrastructure/UC-5.1.49.json",
    "content/cat-05-network-infrastructure/UC-5.1.50.json",
    "content/cat-05-network-infrastructure/UC-5.1.51.json",
    "content/cat-05-network-infrastructure/UC-5.1.54.json",
    "content/cat-05-network-infrastructure/UC-5.2.24.json",
    "content/cat-05-network-infrastructure/UC-5.2.28.json",
    "content/cat-05-network-infrastructure/UC-5.2.34.json",
    "content/cat-05-network-infrastructure/UC-5.2.35.json",
    "content/cat-05-network-infrastructure/UC-5.2.36.json",
    "content/cat-05-network-infrastructure/UC-5.2.37.json",
    "content/cat-05-network-infrastructure/UC-5.2.38.json",
    "content/cat-05-network-infrastructure/UC-5.2.39.json",
    "content/cat-05-network-infrastructure/UC-5.4.12.json",
    "content/cat-05-network-infrastructure/UC-5.4.14.json",
    "content/cat-05-network-infrastructure/UC-5.4.20.json",
    "content/cat-05-network-infrastructure/UC-5.4.22.json",
    "content/cat-05-network-infrastructure/UC-5.4.23.json",
    "content/cat-05-network-infrastructure/UC-5.4.26.json",
    "content/cat-05-network-infrastructure/UC-5.6.13.json",
    "content/cat-05-network-infrastructure/UC-5.6.14.json",
    "content/cat-05-network-infrastructure/UC-5.8.14.json",
    "content/cat-05-network-infrastructure/UC-5.8.15.json",
    "content/cat-05-network-infrastructure/UC-5.8.20.json",
]


# Fourth wave: misc cleanup (AP offline, API rate, IAQ, OT SSID rex extraction)
MERAKI_MISC_FIX = [
    "content/cat-05-network-infrastructure/UC-5.4.1.json",
    "content/cat-05-network-infrastructure/UC-5.8.11.json",
    "content/cat-05-network-infrastructure/UC-5.8.22.json",
    "content/cat-14-iot-operational-technology-ot/UC-14.1.49.json",
    "content/cat-22-regulatory-compliance/UC-22.15.53.json",
]


def regenerate_one(path: Path) -> bool:
    """Return True if the file changed."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"  ERROR: cannot parse {path}: {exc}")
        return False
    abbrev = to_abbrev(data)
    new_di = generate_detailed_impl(abbrev)
    if data.get("detailedImplementation") == new_di:
        print(f"  -- {path.relative_to(REPO)} (no change)")
        return False
    data["detailedImplementation"] = new_di
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"  OK {path.relative_to(REPO)}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths", nargs="*", help="UC JSON files to regenerate"
    )
    parser.add_argument(
        "--meraki-rewrites",
        action="store_true",
        help="Regenerate the canonical Meraki rewrite set (cat-14 / cat-15.3 / cat-9.6).",
    )
    parser.add_argument(
        "--meraki-devices-fix",
        action="store_true",
        help="Regenerate the meraki:devices misuse rewrite set (cat-5.x + cat-15.3.28).",
    )
    parser.add_argument(
        "--meraki-sc4s-fix",
        action="store_true",
        help="Regenerate the SC4S Meraki syslog rewrite set (cat-5.1 / cat-5.2 / cat-5.4 / cat-5.6 / cat-5.8 admin).",
    )
    parser.add_argument(
        "--meraki-misc-fix",
        action="store_true",
        help="Regenerate misc Meraki cleanup set (AP offline, API rate, IAQ, OT SSID rex extraction).",
    )
    args = parser.parse_args()
    targets: list[Path] = []
    if args.meraki_rewrites:
        targets.extend(REPO / rel for rel in MERAKI_REWRITES)
    if args.meraki_devices_fix:
        targets.extend(REPO / rel for rel in MERAKI_DEVICES_FIX)
    if args.meraki_sc4s_fix:
        targets.extend(REPO / rel for rel in MERAKI_SC4S_FIX)
    if args.meraki_misc_fix:
        targets.extend(REPO / rel for rel in MERAKI_MISC_FIX)
    targets.extend(Path(p).resolve() for p in args.paths)
    if not targets:
        parser.print_help()
        return 0
    changed = 0
    for path in targets:
        if not path.exists():
            print(f"  MISS {path}")
            continue
        if regenerate_one(path):
            changed += 1
    print()
    print(f"Regenerated {changed} of {len(targets)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
