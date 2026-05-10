#!/usr/bin/env python3
"""Fix hallucinated Meraki sourcetypes in UC JSON files.

The catalog has ~141 Meraki-related UCs whose SPL invented a parallel
sourcetype scheme (`meraki:api:*`, `meraki:events`, `meraki:wireless:*`,
etc.) that does not exist anywhere. The real Meraki TA
(`Splunk_TA_cisco_meraki`, app 5580) ships ~35 specific API sourcetypes
(see `~/.cursor/skills/cisco-meraki-ta-setup/reference.md`), and the
SC4S Meraki vendor pack uses `meraki` (and the per-product variants
`meraki:accesspoints`, `meraki:securityappliances`, `meraki:switches`)
for syslog.

This script applies substitutions to the SPL, dataSources, cimSpl, and
detailedImplementation fields to normalize the sourcetype references.
It is conservative: only files that already mention "meraki" are
considered for the index substitution, and the substitutions preserve
JSON escaping.

Run:
    python3 scripts/fix_meraki_spl.py            # apply
    python3 scripts/fix_meraki_spl.py --dry-run  # report only
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONTENT = REPO / "content"

# Order matters: longer/more-specific patterns FIRST so we don't eat them
# with the shorter `meraki:api` pattern.
# Each entry is (compiled_pattern, replacement, label_for_reporting).
# The pattern matches just the sourcetype token (not the surrounding
# quotes / equals sign) so we can use it on raw text and in JSON-escaped
# strings alike.
SOURCETYPE_MAP: list[tuple[str, str]] = [
    # Wireless / AP
    ("meraki:wireless:airmarshal", "meraki:airmarshal"),
    ("meraki:api:airmarshal", "meraki:airmarshal"),
    ("meraki:api:wireless", "meraki:accesspoints"),
    ("meraki:api:ssids", "meraki:accesspoints"),
    ("meraki:wireless", "meraki:accesspoints"),
    # Switches
    ("meraki:api:switch:portstatus", "meraki:switchportsoverview"),
    ("meraki:api:switch:ports", "meraki:switchportsbyswitch"),
    ("meraki:api:switch:stack", "meraki:switches"),
    # Devices / firmware / availability
    ("meraki:api:device:performance", "meraki:devices"),
    ("meraki:api:device:status", "meraki:devicesavailabilities"),
    ("meraki:api:devices", "meraki:devices"),
    ("meraki:api:firmware", "meraki:firmwareupgrades"),
    ("meraki:api:networkHealth", "meraki:devicesavailabilities"),
    ("meraki:api:networkhealth", "meraki:devicesavailabilities"),
    ("meraki:api:networks", "meraki:organizationsnetworks"),
    # VPN / SD-WAN
    ("meraki:api:vpnstatus", "meraki:appliancesdwanstatuses"),
    ("meraki:api:vpn", "meraki:appliancesdwanstatuses"),
    # Uplinks
    ("meraki:api:uplinkstats", "meraki:devicesuplinkslossandlatency"),
    ("meraki:api:uplinks", "meraki:devicesuplinkslossandlatency"),
    # MX appliance / IDS / traffic shaping
    ("meraki:api:trafficshaping", "meraki:securityappliances"),
    ("meraki:api:appliance", "meraki:securityappliances"),
    # Audit / changelog / admins
    ("meraki:api:changelog", "meraki:audit"),
    ("meraki:api:admins", "meraki:audit"),
    ("meraki:api:audit", "meraki:audit"),
    ("meraki:config:backup", "meraki:audit"),
    # Sensor / camera / licenses / org
    ("meraki:api:sensor", "meraki:sensorreadingshistory"),
    ("meraki:api:licenses", "meraki:licensesoverview"),
    ("meraki:api:organization", "meraki:organizations"),
    # Alerts / webhooks
    ("meraki:api:webhooklogs", "meraki:webhooklogs:api"),
    ("meraki:api:alerts", "meraki:assurancealerts"),
    # Cellular - no real cellular sourcetype, MG data is in devices
    ("meraki:api:cellular:signal", "meraki:devices"),
    ("meraki:api:cellular:sim", "meraki:devices"),
    ("meraki:api:cellular:usage", "meraki:devices"),
    # Bluetooth / content filtering / clients / traffic - via syslog
    ("meraki:api:bluetooth", "meraki"),
    ("meraki:api:contentfiltering", "meraki"),
    ("meraki:api:clients", "meraki"),
    ("meraki:api:traffic", "meraki"),
    # Hallucinated syslog event-subtype "sourcetypes" -> SC4S `meraki`
    ("meraki:events", "meraki"),
    ("meraki:association", "meraki"),
    ("meraki:flows", "meraki"),
    ("meraki:ids", "meraki"),
    ("meraki:radio", "meraki"),
    ("meraki:scanning", "meraki"),
    ("meraki:cabletest", "meraki"),
    # Generic `meraki:api` (no subtype) -> safest default is device inventory
    # Wildcard variant `meraki:api:*` -> `meraki:*` (covers all real ones)
    ("meraki:api:*", "meraki:*"),
    ("meraki:api", "meraki:devices"),
]

# Compile substitutions as fixed-string substitutions with word boundaries.
# We need word-boundary on the right (so `meraki:api` doesn't eat
# `meraki:api:devices`) but the substitution list is ordered longest-first
# so this is mostly handled by ordering. The right boundary still matters
# inside docs where a sentence ends with the sourcetype, e.g.
# "...sourcetype=meraki:api." vs "...sourcetype=meraki:api:devices".
COMPILED_MAP: list[tuple[re.Pattern[str], str, str]] = []
for src, dst in SOURCETYPE_MAP:
    # Escape regex special chars in the source token
    src_re = re.escape(src)
    # Right boundary: end of token. The next char must not be a colon, an
    # alphanumeric, an asterisk, or an underscore (those would extend the
    # sourcetype name). Allow `*` to match wildcard variants only as the
    # whole token (already in the map order).
    pattern = re.compile(src_re + r"(?![\w:.*])")
    COMPILED_MAP.append((pattern, dst, f"{src} -> {dst}"))


def fix_text(text: str) -> tuple[str, Counter]:
    """Apply substitutions to a text blob. Returns (new_text, counts)."""
    counts: Counter = Counter()
    out = text
    for pattern, replacement, label in COMPILED_MAP:
        new_out, n = pattern.subn(replacement, out)
        if n:
            counts[label] += n
            out = new_out
    return out, counts


# Index substitution: cisco_network -> meraki, but only inside files that
# we already classify as Meraki-related. We do this AFTER the sourcetype
# fixes so we don't accidentally match anything weird.
INDEX_PATTERN = re.compile(r"index\s*=\s*cisco_network(?![A-Za-z0-9_])")
INDEX_REPLACEMENT = "index=meraki"


def fix_meraki_index(text: str, file_is_meraki: bool) -> tuple[str, int]:
    if not file_is_meraki:
        return text, 0
    new, n = INDEX_PATTERN.subn(INDEX_REPLACEMENT, text)
    return new, n


# Files we want to skip (none right now, but reserved)
SKIP_FILES: set[str] = set()


def file_is_meraki(text: str) -> bool:
    """Heuristic: does this UC look Meraki-centric?

    True if it:
      - has at least one `sourcetype=...meraki...` reference, or
      - has equipmentModels containing "cisco_meraki", or
      - explicitly mentions Meraki in the title.
    """
    low = text.lower()
    if "meraki" not in low and "cisco meraki" not in low:
        return False
    # Don't treat purely cross-vendor UCs as Meraki for index substitution
    # if they have a non-Meraki primary index already.
    return True


def process_file(path: Path, dry_run: bool) -> tuple[Counter, int]:
    text = path.read_text(encoding="utf-8")
    if "meraki" not in text.lower() and "Meraki" not in text:
        return Counter(), 0

    is_meraki = file_is_meraki(text)
    if not is_meraki:
        return Counter(), 0

    new_text, st_counts = fix_text(text)
    new_text, idx_count = fix_meraki_index(new_text, is_meraki)
    if idx_count:
        st_counts["index=cisco_network -> index=meraki"] = idx_count

    if new_text == text:
        return st_counts, 0

    # Validate JSON before writing
    try:
        json.loads(new_text)
    except json.JSONDecodeError as exc:
        print(f"  WARNING: JSON parse failed for {path} after substitution: {exc}")
        return st_counts, -1

    if not dry_run:
        path.write_text(new_text, encoding="utf-8")
    return st_counts, 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="Report changes without writing")
    ap.add_argument(
        "--paths",
        nargs="*",
        help="Specific files to process (default: all content/**/UC-*.json)",
    )
    args = ap.parse_args()

    if args.paths:
        files = [Path(p) for p in args.paths]
    else:
        files = sorted(CONTENT.rglob("UC-*.json"))

    total = Counter()
    files_changed = 0
    files_failed = 0
    files_visited = 0
    for p in files:
        if p.name in SKIP_FILES:
            continue
        files_visited += 1
        counts, status = process_file(p, args.dry_run)
        if status == 1:
            files_changed += 1
        elif status == -1:
            files_failed += 1
        total.update(counts)

    print("=" * 72)
    print("Meraki SPL fixer report")
    print("=" * 72)
    print(f"Files visited       : {files_visited}")
    print(f"Files changed       : {files_changed}{' (DRY RUN)' if args.dry_run else ''}")
    if files_failed:
        print(f"Files with errors   : {files_failed}")
    print()
    print("Substitutions applied:")
    for label, n in sorted(total.items(), key=lambda x: -x[1]):
        print(f"  {n:5d}  {label}")
    return 1 if files_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
