---
id: "1.4.2"
title: "RAID Degradation Alerts"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-1.4.2 · RAID Degradation Alerts

## Description

A degraded RAID has lost redundancy — another disk failure means data loss. Requires immediate attention.

## Value

A degraded RAID has lost redundancy — another disk failure means data loss. Requires immediate attention.

## Implementation

Create scripted input for the RAID controller CLI tool: `storcli /c0/v0 show` or `megacli -LDInfo -Lall -aAll`. Run every 300 seconds. Alert immediately on any non-Optimal state.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (`megacli`, `storcli`, `ssacli`).
• Ensure the following data sources are available: Custom sourcetype (RAID controller output).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create scripted input for the RAID controller CLI tool: `storcli /c0/v0 show` or `megacli -LDInfo -Lall -aAll`. Run every 300 seconds. Alert immediately on any non-Optimal state.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=hardware sourcetype=raid_status
| where state!="Optimal" AND state!="Online"
| table _time host vd_name state disks_failed
| sort -_time
```

Understanding this SPL

**RAID Degradation Alerts** — A degraded RAID has lost redundancy — another disk failure means data loss. Requires immediate attention.

Documented **Data sources**: Custom sourcetype (RAID controller output). **App/TA** (typical add-on context): Custom scripted input (`megacli`, `storcli`, `ssacli`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: hardware; **sourcetype**: raid_status. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=hardware, sourcetype=raid_status. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where state!="Optimal" AND state!="Online"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **RAID Degradation Alerts**): table _time host vd_name state disks_failed
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status indicator per array, Table, Alert panel (critical).

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
index=hardware sourcetype=raid_status
| where state!="Optimal" AND state!="Online"
| table _time host vd_name state disks_failed
| sort -_time
```

## Visualization

Status indicator per array, Table, Alert panel (critical).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
