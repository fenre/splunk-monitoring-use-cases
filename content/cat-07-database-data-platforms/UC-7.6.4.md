---
id: "7.6.4"
title: "Database Backup Size Trending"
criticality: "medium"
splunkPillar: "Security"
---

# UC-7.6.4 · Database Backup Size Trending

## Description

Monthly backup size growth forecasts storage for backup appliances and cloud object storage costs. Anomalous jumps can indicate bulk data loads, failed truncations, or ransomware preparation worth investigating.

## Value

Monthly backup size growth forecasts storage for backup appliances and cloud object storage costs. Anomalous jumps can indicate bulk data loads, failed truncations, or ransomware preparation worth investigating.

## Implementation

Deduplicate overlapping full/diff/incremental jobs with `backup_type`. Include compression ratio if logged for better capacity forecasting. Tag cloud vs on-prem targets separately. Alert on failed backups via a companion search; this UC focuses on growth trend only.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: RMAN, SQL Server backup history, mysqldump / Percona log parsers, cloud backup APIs.
• Ensure the following data sources are available: `index=db` `sourcetype=mssql:backup`, `sourcetype=mysql:backup`, `sourcetype=oracle:rman`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deduplicate overlapping full/diff/incremental jobs with `backup_type`. Include compression ratio if logged for better capacity forecasting. Tag cloud vs on-prem targets separately. Alert on failed backups via a companion search; this UC focuses on growth trend only.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=db sourcetype IN ("mssql:backup","mysql:backup","oracle:rman","postgresql:backup")
| eval size_gb=coalesce(backup_size_gb, round(backup_size_bytes/1073741824,3))
| where backup_status IN ("success","Success","completed") OR isnull(backup_status)
| bin _time span=1mon
| stats max(size_gb) as backup_size_gb by _time, database_name
| timechart span=1mon sum(backup_size_gb) as total_backup_gb by database_name limit=10
```

Understanding this SPL

**Database Backup Size Trending** — Monthly backup size growth forecasts storage for backup appliances and cloud object storage costs. Anomalous jumps can indicate bulk data loads, failed truncations, or ransomware preparation worth investigating.

Documented **Data sources**: `index=db` `sourcetype=mssql:backup`, `sourcetype=mysql:backup`, `sourcetype=oracle:rman`. **App/TA** (typical add-on context): RMAN, SQL Server backup history, mysqldump / Percona log parsers, cloud backup APIs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: db.

**Pipeline walkthrough**

• Scopes the data: index=db. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **size_gb** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where backup_status IN ("success","Success","completed") OR isnull(backup_status)` — typically the threshold or rule expression for this monitoring goal.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by _time, database_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `timechart` plots the metric over time using **span=1mon** buckets with a separate series **by database_name limit=10** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (backup size GB over months), column chart (month-over-month growth %), table (largest databases).

## SPL

```spl
index=db sourcetype IN ("mssql:backup","mysql:backup","oracle:rman","postgresql:backup")
| eval size_gb=coalesce(backup_size_gb, round(backup_size_bytes/1073741824,3))
| where backup_status IN ("success","Success","completed") OR isnull(backup_status)
| bin _time span=1mon
| stats max(size_gb) as backup_size_gb by _time, database_name
| timechart span=1mon sum(backup_size_gb) as total_backup_gb by database_name limit=10
```

## Visualization

Line chart (backup size GB over months), column chart (month-over-month growth %), table (largest databases).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
