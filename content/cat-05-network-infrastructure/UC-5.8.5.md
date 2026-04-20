---
id: "5.8.5"
title: "Network Device Backup Compliance"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.8.5 · Network Device Backup Compliance

## Description

Missing backups mean a failed device requires manual rebuilding. Tracking backup success ensures rapid disaster recovery.

## Value

Missing backups mean a failed device requires manual rebuilding. Tracking backup success ensures rapid disaster recovery.

## Implementation

Integrate config backup tool (Oxidized/RANCID) logs into Splunk. Track success/failure per device. Alert when a device hasn't been backed up in >7 days.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: RANCID/Oxidized logs, SolarWinds NCM, custom scripts.
• Ensure the following data sources are available: `sourcetype=rancid`, `sourcetype=oxidized`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Integrate config backup tool (Oxidized/RANCID) logs into Splunk. Track success/failure per device. Alert when a device hasn't been backed up in >7 days.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="oxidized"
| stats latest(status) as backup_status, latest(_time) as last_backup by device
| eval days_since=round((now()-last_backup)/86400,0)
| where backup_status!="success" OR days_since > 7
| sort -days_since
```

Understanding this SPL

**Network Device Backup Compliance** — Missing backups mean a failed device requires manual rebuilding. Tracking backup success ensures rapid disaster recovery.

Documented **Data sources**: `sourcetype=rancid`, `sourcetype=oxidized`. **App/TA** (typical add-on context): RANCID/Oxidized logs, SolarWinds NCM, custom scripts. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: oxidized. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="oxidized". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by device** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **days_since** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where backup_status!="success" OR days_since > 7` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (device, status, days since backup), Single value (compliance %), Status grid.

## SPL

```spl
index=network sourcetype="oxidized"
| stats latest(status) as backup_status, latest(_time) as last_backup by device
| eval days_since=round((now()-last_backup)/86400,0)
| where backup_status!="success" OR days_since > 7
| sort -days_since
```

## Visualization

Table (device, status, days since backup), Single value (compliance %), Status grid.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
