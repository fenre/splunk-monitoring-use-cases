---
id: "5.8.23"
title: "Dashboard Configuration and Export Backup (Meraki)"
criticality: "low"
splunkPillar: "Observability"
---

# UC-5.8.23 · Dashboard Configuration and Export Backup (Meraki)

## Description

Tracks dashboard configuration backups to enable disaster recovery and configuration review.

## Value

Tracks dashboard configuration backups to enable disaster recovery and configuration review.

## Implementation

Periodically backup organization configurations. Track backup history.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki:api`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Periodically backup organization configurations. Track backup history.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki:api" backup_timestamp=*
| stats latest(backup_timestamp) as last_backup, count as backup_count by organization
| eval backup_age_days=round((now()-strptime(backup_timestamp, "%Y-%m-%d"))/86400, 0)
| where backup_age_days > 7
```

Understanding this SPL

**Dashboard Configuration and Export Backup (Meraki)** — Tracks dashboard configuration backups to enable disaster recovery and configuration review.

Documented **Data sources**: `sourcetype=meraki:api`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki:api. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki:api". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by organization** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **backup_age_days** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where backup_age_days > 7` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Last backup timestamp by org; backup recency gauge; backup history timeline.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" backup_timestamp=*
| stats latest(backup_timestamp) as last_backup, count as backup_count by organization
| eval backup_age_days=round((now()-strptime(backup_timestamp, "%Y-%m-%d"))/86400, 0)
| where backup_age_days > 7
```

## Visualization

Last backup timestamp by org; backup recency gauge; backup history timeline.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
