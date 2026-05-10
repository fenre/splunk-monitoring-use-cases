#!/usr/bin/env python3
"""Fetch a field manifest from the live Splunk server for every Meraki sourcetype
that the catalog references AND that has data. Cache to /tmp/meraki-field-manifests.json
for the linter to compare against.

We deliberately do NOT call the Splunk MCP from this script — the MCP runs
as a tool from the agent. This script only EMITS the list of sourcetypes
that need a field manifest. The agent then runs ONE splunk_run_query per
sourcetype using a templated probe and writes the results back here.

Probe template (per sourcetype X):
    index=meraki sourcetype=X | head 1 | fieldsummary
       | table field count distinct_count values

Output schema:
{
  "<sourcetype>": {
    "has_data": true|false,
    "fields": ["<field-name>", ...],
    "sample_values": {"<field>": "<value>", ...}
  }
}
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

INVENTORY = Path("/tmp/meraki-inventory.json")
OUT = Path("/tmp/meraki-sourcetypes-to-probe.txt")


def main() -> None:
    if not INVENTORY.exists():
        print("ERROR: run scripts/_meraki_inventory.py first", file=sys.stderr)
        sys.exit(1)
    records = json.loads(INVENTORY.read_text())
    sts: set[str] = set()
    for r in records:
        for st in r.get("sourcetypes", []):
            if st.startswith("meraki"):
                sts.add(st)
    OUT.write_text("\n".join(sorted(sts)) + "\n")
    print(f"Wrote {len(sts)} sourcetypes to {OUT}")
    for st in sorted(sts):
        print(f"  {st}")


if __name__ == "__main__":
    main()
