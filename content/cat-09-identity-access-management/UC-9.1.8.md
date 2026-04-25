<!-- AUTO-GENERATED from UC-9.1.8.json — DO NOT EDIT -->

---
id: "9.1.8"
title: "AD Replication Monitoring"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.1.8 · AD Replication Monitoring

## Description

Replication failures cause authentication issues, stale group memberships, and inconsistent policy application across sites.

## Value

Replication failures cause authentication issues, stale group memberships, and inconsistent policy application across sites.

## Implementation

Forward Directory Service event logs from DCs. Run `repadmin /showrepl` via scripted input daily. Alert on replication failures (Event IDs 1864, 2042, 2087). Track replication latency between sites.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`, `repadmin` scripted input.
• Ensure the following data sources are available: Directory Service event log, `repadmin /showrepl` output.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward Directory Service event logs from DCs. Run `repadmin /showrepl` via scripted input daily. Alert on replication failures (Event IDs 1864, 2042, 2087). Track replication latency between sites.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Directory Service" EventCode IN (1864,1865,2042,2087)
| table _time, ComputerName, EventCode, Message
| sort -_time
```

Understanding this SPL

**AD Replication Monitoring** — Replication failures cause authentication issues, stale group memberships, and inconsistent policy application across sites.

Documented **Data sources**: Directory Service event log, `repadmin /showrepl` output. **App/TA** (typical add-on context): `Splunk_TA_windows`, `repadmin` scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Directory Service. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Directory Service". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **AD Replication Monitoring**): table _time, ComputerName, EventCode, Message
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare with Event Viewer on domain controllers (or exported Security logs) and with Active Directory Users and Computers for the same objects and time window.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (replication status by DC pair), Status grid (DC × replication health), Timeline (failure events).

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
index=wineventlog sourcetype="WinEventLog:Directory Service" EventCode IN (1864,1865,2042,2087)
| table _time, ComputerName, EventCode, Message
| sort -_time
```

## Visualization

Table (replication status by DC pair), Status grid (DC × replication health), Timeline (failure events).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
