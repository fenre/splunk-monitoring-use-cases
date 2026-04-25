<!-- AUTO-GENERATED from UC-2.2.2.json — DO NOT EDIT -->

---
id: "2.2.2"
title: "Hyper-V Replication Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.2.2 · Hyper-V Replication Health

## Description

Replication lag means your DR site is behind. If replication breaks, you lose your recovery point objective (RPO).

## Value

Replication lag means your DR site is behind. If replication breaks, you lose your recovery point objective (RPO).

## Implementation

Enable Hyper-V VMMS event log collection. Also create a PowerShell scripted input: `Get-VMReplication | Select VMName, State, Health, LastReplicationTime`. Alert on replication state != Normal or health != Normal.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows` (Hyper-V).
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-Hyper-V-VMMS-Admin`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Hyper-V VMMS event log collection. Also create a PowerShell scripted input: `Get-VMReplication | Select VMName, State, Health, LastReplicationTime`. Alert on replication state != Normal or health != Normal.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-Hyper-V-VMMS-Admin" ("replication" AND ("error" OR "warning" OR "critical" OR "failed"))
| stats count by host, EventCode, Message
| sort -count
```

Understanding this SPL

**Hyper-V Replication Health** — Replication lag means your DR site is behind. If replication breaks, you lose your recovery point objective (RPO).

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-Hyper-V-VMMS-Admin`. **App/TA** (typical add-on context): `Splunk_TA_windows` (Hyper-V). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Microsoft-Windows-Hyper-V-VMMS-Admin. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Microsoft-Windows-Hyper-V-VMMS-Admin". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, EventCode, Message** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (VM, replication state, health, last sync), Status indicators, Events list.

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
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-Hyper-V-VMMS-Admin" ("replication" AND ("error" OR "warning" OR "critical" OR "failed"))
| stats count by host, EventCode, Message
| sort -count
```

## Visualization

Table (VM, replication state, health, last sync), Status indicators, Events list.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
