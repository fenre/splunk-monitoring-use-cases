---
id: "5.8.24"
title: "Network Device Configuration Backup and Drift"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.8.24 · Network Device Configuration Backup and Drift

## Description

Missing or stale configuration backups complicate recovery after failure or bad change. Detecting backup failure or config drift supports change control and RTO.

## Value

Missing or stale configuration backups complicate recovery after failure or bad change. Detecting backup failure or config drift supports change control and RTO.

## Implementation

Run config backup (RANCID, Oxidized, or vendor API) on schedule. Ingest success/failure and timestamp. Alert when backup fails or last successful backup is older than 24 hours. Optionally diff current vs. last backup for drift.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: RANCID, Oxidized, custom scripted input.
• Ensure the following data sources are available: Backup job output, config repository (Git), device config fetch.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Run config backup (RANCID, Oxidized, or vendor API) on schedule. Ingest success/failure and timestamp. Alert when backup fails or last successful backup is older than 24 hours. Optionally diff current vs. last backup for drift.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype=config_backup
| stats latest(backup_ok) as ok, latest(backup_time) as last_backup by device_hostname
| where ok != 1 OR (now()-last_backup) > 86400
| table device_hostname ok last_backup
```

Understanding this SPL

**Network Device Configuration Backup and Drift** — Missing or stale configuration backups complicate recovery after failure or bad change. Detecting backup failure or config drift supports change control and RTO.

Documented **Data sources**: Backup job output, config repository (Git), device config fetch. **App/TA** (typical add-on context): RANCID, Oxidized, custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: config_backup. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype=config_backup. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by device_hostname** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where ok != 1 OR (now()-last_backup) > 86400` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Network Device Configuration Backup and Drift**): table device_hostname ok last_backup


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (device, last backup, status), Single value (devices without backup today), Timeline (backup runs).

## SPL

```spl
index=network sourcetype=config_backup
| stats latest(backup_ok) as ok, latest(backup_time) as last_backup by device_hostname
| where ok != 1 OR (now()-last_backup) > 86400
| table device_hostname ok last_backup
```

## Visualization

Table (device, last backup, status), Single value (devices without backup today), Timeline (backup runs).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
