<!-- AUTO-GENERATED from UC-9.1.27.json — DO NOT EDIT -->

---
id: "9.1.27"
title: "Active Directory Replication"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.1.27 · Active Directory Replication

## Description

AD replication failures cause authentication inconsistencies — users locked out in one site but not another, stale GPOs, and split-brain scenarios.

## Value

AD replication failures cause authentication inconsistencies — users locked out in one site but not another, stale GPOs, and split-brain scenarios.

## Implementation

Collect Directory Service event log from all DCs. Create scripted input running `repadmin /replsummary /csv` daily. Alert on any replication failure events. Critical alert on EventCode 2042 (tombstone lifetime exceeded).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Directory Service`, custom scripted input (`repadmin /replsummary`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect Directory Service event log from all DCs. Create scripted input running `repadmin /replsummary /csv` daily. Alert on any replication failure events. Critical alert on EventCode 2042 (tombstone lifetime exceeded).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=ad sourcetype=repadmin_replsummary
| where failures > 0
| table source_dc dest_dc failures last_failure last_success
```

Understanding this SPL

**Active Directory Replication** — AD replication failures cause authentication inconsistencies — users locked out in one site but not another, stale GPOs, and split-brain scenarios.

Documented **Data sources**: `sourcetype=WinEventLog:Directory Service`, custom scripted input (`repadmin /replsummary`). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: ad; **sourcetype**: repadmin_replsummary. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=ad, sourcetype=repadmin_replsummary. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where failures > 0` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Active Directory Replication**): table source_dc dest_dc failures last_failure last_success


Step 3 — Validate
Compare with Event Viewer on domain controllers (or exported Security logs) and with Active Directory Users and Computers for the same objects and time window.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of replication partners with status, Events timeline, Network diagram of DC replication.

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
index=ad sourcetype=repadmin_replsummary
| where failures > 0
| table source_dc dest_dc failures last_failure last_success
```

## Visualization

Table of replication partners with status, Events timeline, Network diagram of DC replication.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
