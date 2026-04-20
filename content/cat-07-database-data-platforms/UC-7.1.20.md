---
id: "7.1.20"
title: "Database Backup and Archive Log Retention Verification"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.1.20 · Database Backup and Archive Log Retention Verification

## Description

Failed or missing backups and unarchived redo logs risk data loss and prevent point-in-time recovery. Verifying backup success and archive log retention ensures RPO is met.

## Value

Failed or missing backups and unarchived redo logs risk data loss and prevent point-in-time recovery. Verifying backup success and archive log retention ensures RPO is met.

## Implementation

Ingest backup job status (RMAN, SQL Server backup history, or backup vendor logs). Alert on any failed or incomplete backup. Track archive log destination space and retention; alert when space is low or retention is below policy.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `splunk_app_db_connect`, backup job logs.
• Ensure the following data sources are available: Oracle RMAN output, SQL Server msdb backup history, PostgreSQL pg_backup (or vendor logs).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest backup job status (RMAN, SQL Server backup history, or backup vendor logs). Alert on any failed or incomplete backup. Track archive log destination space and retention; alert when space is low or retention is below policy.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
| dbxquery connection="oracle_prod" query="SELECT status, start_time, end_time, output_bytes FROM v\$rman_backup_job_details WHERE start_time > SYSDATE-1 ORDER BY start_time DESC"
| search status!="COMPLETED"
| table status start_time end_time output_bytes
```

Understanding this SPL

**Database Backup and Archive Log Retention Verification** — Failed or missing backups and unarchived redo logs risk data loss and prevent point-in-time recovery. Verifying backup success and archive log retention ensures RPO is met.

Documented **Data sources**: Oracle RMAN output, SQL Server msdb backup history, PostgreSQL pg_backup (or vendor logs). **App/TA** (typical add-on context): `splunk_app_db_connect`, backup job logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Pipeline stage (see **Database Backup and Archive Log Retention Verification**): dbxquery connection="oracle_prod" query="SELECT status, start_time, end_time, output_bytes FROM v\$rman_backup_job_details WHERE start_ti…
• Applies an explicit `search` filter to narrow the current result set.
• Pipeline stage (see **Database Backup and Archive Log Retention Verification**): table status start_time end_time output_bytes


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (last backup, status, duration), Gauge (backup success %), Timeline of backup jobs.

## SPL

```spl
| dbxquery connection="oracle_prod" query="SELECT status, start_time, end_time, output_bytes FROM v\$rman_backup_job_details WHERE start_time > SYSDATE-1 ORDER BY start_time DESC"
| search status!="COMPLETED"
| table status start_time end_time output_bytes
```

## Visualization

Table (last backup, status, duration), Gauge (backup success %), Timeline of backup jobs.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
