---
id: "1.1.60"
title: "MTU Mismatch Detection"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.60 · MTU Mismatch Detection

## Description

MTU mismatches cause fragmentation and performance issues, especially with jumbo frame configurations.

## Value

MTU mismatches cause fragmentation and performance issues, especially with jumbo frame configurations.

## Implementation

Create a scripted input that runs 'ip link show' and parses MTU values per interface. Alert when mixed MTUs are detected on a host, indicating potential mismatch with switch/network.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=custom:mtu, ip link show output`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create a scripted input that runs 'ip link show' and parses MTU values per interface. Alert when mixed MTUs are detected on a host, indicating potential mismatch with switch/network.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=custom:mtu host=*
| stats latest(mtu) as interface_mtu by host, interface
| stats values(interface_mtu) as mtus by host
| where mvcount(mtus) > 1
```

Understanding this SPL

**MTU Mismatch Detection** — MTU mismatches cause fragmentation and performance issues, especially with jumbo frame configurations.

Documented **Data sources**: `sourcetype=custom:mtu, ip link show output`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: custom:mtu. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=custom:mtu. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, interface** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where mvcount(mtus) > 1` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table, Alert

Scripted input (generic example)
This use case relies on a scripted input. In the app's local/inputs.conf add a stanza such as:

```ini
[script://$SPLUNK_HOME/etc/apps/YourApp/bin/collect.sh]
interval = 300
sourcetype = your_sourcetype
index = main
disabled = 0
```

The script should print one event per line (e.g. key=value). Example minimal script (bash):

```bash
#!/usr/bin/env bash
# Output metrics or events, one per line
echo "metric=value timestamp=$(date +%s)"
```

For full details (paths, scheduling, permissions), see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=os sourcetype=custom:mtu host=*
| stats latest(mtu) as interface_mtu by host, interface
| stats values(interface_mtu) as mtus by host
| where mvcount(mtus) > 1
```

## Visualization

Table, Alert

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
