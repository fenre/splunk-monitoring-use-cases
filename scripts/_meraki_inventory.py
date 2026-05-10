#!/usr/bin/env python3
"""Inventory all Meraki UCs in the JSON SSOT for the Phase-2 sweep.

Groups UCs by:
  - the sourcetype tokens referenced in their SPL
  - the dataSources path (API TA vs SC4S vs webhook vs other)
  - presence of bug-class patterns we already know about

Outputs:
  /tmp/meraki-inventory.json  (one record per UC)
  /tmp/meraki-by-sourcetype.json  (sourcetype -> [UC paths])

Used as input by _meraki_lint.py and the Phase-3 fixer.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONTENT = REPO / "content"


SOURCETYPE_RE = re.compile(r'sourcetype\s*=\s*"?(meraki[:\w-]*)"?', re.IGNORECASE)
INDEX_RE = re.compile(r'index\s*=\s*"?([\w*-]+)"?', re.IGNORECASE)


# Known bug patterns (classes documented in the live-test report).
# Each entry: (label, regex, applies-only-to-sourcetype-prefix-or-None)
BUG_PATTERNS = [
    ("deviceType_lowercase",
     re.compile(r'deviceType\s*=\s*"(wireless|switch|appliance|camera|sensor|cellular)"', re.IGNORECASE),
     None),
    ("deviceSerial_short_form",
     re.compile(r'\b(deviceSerial|deviceName)\b'),
     "meraki:assurancealerts"),
    ("networkName_short_form",
     re.compile(r'\b(networkName|networkId)\b'),
     "meraki:assurancealerts"),
    ("isnull_dismissedAt",
     re.compile(r'isnull\(\s*dismissed_?at\s*\)', re.IGNORECASE),
     None),
    ("vpnPeers_wrong_array",
     re.compile(r'\bvpnPeers\b'),
     "meraki:appliancesdwanstatuses"),
    ("peerNetwork_prefix",
     re.compile(r'\b(peerNetworkId|peerNetworkName)\b'),
     None),
    ("usage_dot_sent_received_on_statuses",
     re.compile(r'usage\.(sent|received)'),
     "meraki:appliancesdwanstatuses"),
    ("sc4s_sourcetype_in_api_ta_app",
     re.compile(r'sourcetype\s*=\s*"?meraki"?(?!\:)'),
     None),  # also needs cross-check against `app` field; flagged later
]


def referenced_sourcetypes(spl: str) -> list[str]:
    return sorted({m.group(1) for m in SOURCETYPE_RE.finditer(spl or "")})


def referenced_indexes(spl: str) -> list[str]:
    return sorted({m.group(1) for m in INDEX_RE.finditer(spl or "")})


def is_meraki_uc(payload: dict) -> bool:
    """A UC counts as Meraki if its app/dataSources/spl references Meraki."""
    blob = " ".join(
        str(payload.get(k, "")) for k in ("app", "dataSources", "spl", "implementation", "title", "description")
    ).lower()
    return ("meraki" in blob) or ("cisco_meraki" in blob)


def detect_bugs(payload: dict) -> list[str]:
    spl = payload.get("spl", "") or ""
    sourcetypes = referenced_sourcetypes(spl)
    flagged = []
    for label, pattern, st_constraint in BUG_PATTERNS:
        if not pattern.search(spl):
            continue
        if st_constraint is None:
            flagged.append(label)
            continue
        if any(st.startswith(st_constraint) for st in sourcetypes):
            flagged.append(label)
    # Cross-check: SC4S sourcetype but app says API TA
    app = payload.get("app", "") or ""
    ds = payload.get("dataSources", "") or ""
    sc4s_in_spl = bool(re.search(r'sourcetype\s*=\s*"?meraki"?(?!\:)', spl))
    api_ta_in_app = "5580" in app or "Cisco Meraki Add-on" in app
    sc4s_in_ds = re.search(r'\bSC4S\b', ds, re.IGNORECASE)
    if sc4s_in_spl and api_ta_in_app and not sc4s_in_ds:
        flagged.append("narrative_app_vs_sc4s_mismatch")
    elif sc4s_in_spl and api_ta_in_app and sc4s_in_ds and "SC4S" not in app:
        # Like UC-5.1.51 before fix — already cleaned up there but check rest
        flagged.append("narrative_app_says_api_only_but_spl_uses_syslog")
    return flagged


def main() -> None:
    records = []
    by_sourcetype: dict[str, list[str]] = defaultdict(list)
    for path in sorted(CONTENT.glob("cat-*/UC-*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not is_meraki_uc(payload):
            continue
        rel = str(path.relative_to(REPO))
        spl = payload.get("spl", "") or ""
        sts = referenced_sourcetypes(spl)
        idxs = referenced_indexes(spl)
        bugs = detect_bugs(payload)
        record = {
            "path": rel,
            "id": payload.get("id"),
            "title": payload.get("title"),
            "indexes": idxs,
            "sourcetypes": sts,
            "bugs": bugs,
            "app": (payload.get("app") or "")[:200],
            "dataSources": (payload.get("dataSources") or "")[:300],
        }
        records.append(record)
        for st in sts or ["<no-sourcetype>"]:
            by_sourcetype[st].append(rel)
    Path("/tmp/meraki-inventory.json").write_text(
        json.dumps(records, indent=2), encoding="utf-8"
    )
    Path("/tmp/meraki-by-sourcetype.json").write_text(
        json.dumps(by_sourcetype, indent=2), encoding="utf-8"
    )
    n_with_bugs = sum(1 for r in records if r["bugs"])
    print(f"Total Meraki UCs scanned: {len(records)}")
    print(f"UCs with at least one suspected bug: {n_with_bugs}")
    print()
    print("=== Top sourcetypes by UC count ===")
    for st, paths in sorted(by_sourcetype.items(), key=lambda kv: -len(kv[1]))[:25]:
        print(f"  {len(paths):3d}  {st}")
    print()
    print("=== Bug class distribution ===")
    classes: dict[str, int] = defaultdict(int)
    for r in records:
        for b in r["bugs"]:
            classes[b] += 1
    for cls, n in sorted(classes.items(), key=lambda kv: -kv[1]):
        print(f"  {n:3d}  {cls}")
    print()
    print(f"Inventory written to /tmp/meraki-inventory.json")
    print(f"Sourcetype index written to /tmp/meraki-by-sourcetype.json")


if __name__ == "__main__":
    main()
