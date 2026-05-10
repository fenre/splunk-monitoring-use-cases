#!/usr/bin/env python3
"""Fix invalid ``type=`` filters in SC4S Meraki UCs.

The Meraki SC4S vendor pack normalises Meraki syslog into a small set of
message types (per the SC4S docs and Meraki syslog reference):

    events                       VPN, DHCP, association, deauth, uplink,
                                 content_filtering, configuration_changed,
                                 port_status_changed, etc.
    security_event               IDS / malicious-file events
    ids-alerts                   IDS signature matches (NOTE: hyphen + plural)
    urls                         HTTP GET access
    flows                        L3 firewall flow records (deprecated MX18.101+)
    firewall                     replaces flows on MX18.101+
    vpn_firewall                 site-to-site VPN firewall
    cellular_firewall            cellular firewall
    bridge_anyconnect_client_vpn_firewall
    airmarshal_events            rogue AP detection (NOTE: plural, no underscore)

The original UCs invent ``type=vpn``, ``type=flow``, ``type=ids_alert``,
``type=access``, ``type=air_marshal`` etc. None of these exist in the
SC4S-normalised event stream. This script rewrites each UC's ``spl`` and
the embedded SPL fence in ``detailedImplementation`` to use the correct
type filter.

Usage:
    python3 scripts/fix_meraki_sc4s_types.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONTENT = REPO / "content"


# Per-UC fix table. Key = relative path, value = dict with `type_replacements`
# (literal substring replacements applied to spl + detailedImplementation SPL
# fence) and optional ``rationale`` for human review of the audit log.
FIXES: dict[str, dict] = {
    # 5.2.19 — VPN tunnel status. Real path: type=events filtered by VPN messages.
    # The Meraki "events" sourcetype carries connection/disconnect lines like
    # `vpn_connectivity_change Auto VPN tunnel ... up/down`.
    "content/cat-05-network-infrastructure/UC-5.2.19.json": {
        "type_replacements": [
            ('type=vpn\n',
             'type=events (vpn_connectivity_change OR "vpn") \n'),
        ],
    },
    # 5.2.21 — IDS/IPS alert analysis. Real type is "ids-alerts" (hyphen, plural)
    # or "security_event". The TA documents ids-alerts; either works.
    "content/cat-05-network-infrastructure/UC-5.2.21.json": {
        "type_replacements": [
            ('type=ids_alert\n', 'type=ids-alerts\n'),
        ],
    },
    # 5.2.23, 5.2.24, 5.2.31, 5.2.32, 5.2.38 — flow/firewall analytics.
    # Old firmware: type=flows (plural). New (MX18.101+): type=firewall.
    # Use an OR to cover both.
    "content/cat-05-network-infrastructure/UC-5.2.23.json": {
        "type_replacements": [
            ('type=flow ', '(type=flows OR type=firewall) '),
        ],
    },
    "content/cat-05-network-infrastructure/UC-5.2.24.json": {
        "type_replacements": [
            ('type=flow ', '(type=flows OR type=firewall) '),
        ],
    },
    # 5.2.25 — VPN latency: similar to 5.2.19 but adds latency=*.
    "content/cat-05-network-infrastructure/UC-5.2.25.json": {
        "type_replacements": [
            ('type=vpn latency=*',
             'type=events (vpn_connectivity_change OR "Auto VPN") latency=*'),
        ],
    },
    # 5.2.26 — Client VPN. Real path: type=events with "client_vpn" keyword.
    "content/cat-05-network-infrastructure/UC-5.2.26.json": {
        "type_replacements": [
            ('type=vpn client_vpn=true',
             'type=events ("client_vpn_connect" OR "client_vpn_disconnect")'),
        ],
    },
    # 5.2.29 — composite security search.
    "content/cat-05-network-infrastructure/UC-5.2.29.json": {
        "type_replacements": [
            ('type=security_event OR type=urls OR type=flow',
             'type=security_event OR type=urls OR type=flows OR type=firewall OR type=ids-alerts'),
        ],
    },
    "content/cat-05-network-infrastructure/UC-5.2.31.json": {
        "type_replacements": [
            ('type=flow application=*',
             '(type=flows OR type=firewall) application=*'),
        ],
    },
    "content/cat-05-network-infrastructure/UC-5.2.32.json": {
        "type_replacements": [
            ('type=flow\n',
             '(type=flows OR type=firewall)\n'),
        ],
    },
    # 5.2.37 — Auto VPN path changes — events stream, filter by "Auto VPN" or
    # "path change" via the existing signature filter.
    "content/cat-05-network-infrastructure/UC-5.2.37.json": {
        "type_replacements": [
            ('type=vpn ', 'type=events '),
        ],
    },
    "content/cat-05-network-infrastructure/UC-5.2.38.json": {
        "type_replacements": [
            ('type=flow protocol="tcp"',
             '(type=flows OR type=firewall) protocol="tcp"'),
        ],
    },
    # 5.4.1 — AP went offline / unreachable. Use type=events.
    "content/cat-05-network-infrastructure/UC-5.4.1.json": {
        "type_replacements": [
            ('type="access point"', 'type=events'),
        ],
    },
    # 5.4.17 — Air Marshal. Real type is "airmarshal_events" (no underscore between
    # "air" and "marshal"; plural).
    "content/cat-05-network-infrastructure/UC-5.4.17.json": {
        "type_replacements": [
            ('type=air_marshal ', 'type=airmarshal_events '),
        ],
    },
    "content/cat-05-network-infrastructure/UC-5.4.23.json": {
        "type_replacements": [
            ('type=flow dest=', '(type=flows OR type=firewall) dest='),
        ],
    },
    "content/cat-05-network-infrastructure/UC-5.4.26.json": {
        "type_replacements": [
            ('type=flow\n',
             '(type=flows OR type=firewall)\n'),
        ],
    },
}


def apply_fixes_to_str(s: str, replacements: list[tuple[str, str]]) -> tuple[str, int]:
    """Substring-replace inside a single Python string (no JSON escaping)."""
    total = 0
    for old, new in replacements:
        if old in s:
            total += s.count(old)
            s = s.replace(old, new)
    return s, total


def main() -> int:
    changed = 0
    for rel, spec in FIXES.items():
        path = REPO / rel
        if not path.exists():
            print(f"  MISS {rel}")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"  ERROR {rel}: cannot parse JSON: {exc}")
            continue
        total = 0
        for field in ("spl", "implementation", "detailedImplementation", "dataSources"):
            if field not in data:
                continue
            new_value, count = apply_fixes_to_str(data[field], spec["type_replacements"])
            if count:
                data[field] = new_value
                total += count
        if not total:
            print(f"  -- {rel} (no match)")
            continue
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        changed += 1
        print(f"  OK {rel} ({total} replacement{'s' if total != 1 else ''})")
    print()
    print(f"Fixed {changed} of {len(FIXES)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
