---
id: "7.1.32"
title: "Database Backup Chain Validation"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.1.32 · Database Backup Chain Validation

## Description

Verifies full→diff→log chain continuity (SQL Server LSN chain, Oracle archivelog sequence) to detect missing backups before restore drills fail.

## Value

Verifies full→diff→log chain continuity (SQL Server LSN chain, Oracle archivelog sequence) to detect missing backups before restore drills fail.

## Implementation

Custom SQL to flag LSN gaps. For Oracle, check archivelog sequence continuity. Alert on any break in chain for production databases.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: DB Connect, backup vendor logs.
• Ensure the following data sources are available: `msdb.dbo.backupset` (first_lsn, last_lsn, type), RMAN backup pieces.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Custom SQL to flag LSN gaps. For Oracle, check archivelog sequence continuity. Alert on any break in chain for production databases.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="dbconnect:backup_chain"
| sort database_name, backup_finish_date
| streamstats window=2 previous(last_lsn) as prev_last by database_name
| where isnotnull(prev_last) AND first_lsn!=prev_last AND type!=1
| table database_name backup_finish_date type first_lsn prev_last
```

Understanding this SPL

**Database Backup Chain Validation** — Verifies full→diff→log chain continuity (SQL Server LSN chain, Oracle archivelog sequence) to detect missing backups before restore drills fail.

Documented **Data sources**: `msdb.dbo.backupset` (first_lsn, last_lsn, type), RMAN backup pieces. **App/TA** (typical add-on context): DB Connect, backup vendor logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: dbconnect:backup_chain. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="dbconnect:backup_chain". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• `streamstats` rolls up events into metrics; results are split **by database_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where isnotnull(prev_last) AND first_lsn!=prev_last AND type!=1` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Database Backup Chain Validation**): table database_name backup_finish_date type first_lsn prev_last

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Databases.Instance_Stats by Instance_Stats.host, Instance_Stats.action | sort - count
```

Understanding this CIM / accelerated SPL

**Database Backup Chain Validation** — Verifies full→diff→log chain continuity (SQL Server LSN chain, Oracle archivelog sequence) to detect missing backups before restore drills fail.

Documented **Data sources**: `msdb.dbo.backupset` (first_lsn, last_lsn, type), RMAN backup pieces. **App/TA** (typical add-on context): DB Connect, backup vendor logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Databases.Instance_Stats` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (broken chains), Timeline (backup types), Single value (databases with gaps).

## SPL

```spl
index=database sourcetype="dbconnect:backup_chain"
| sort database_name, backup_finish_date
| streamstats window=2 previous(last_lsn) as prev_last by database_name
| where isnotnull(prev_last) AND first_lsn!=prev_last AND type!=1
| table database_name backup_finish_date type first_lsn prev_last
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Databases.Instance_Stats by Instance_Stats.host, Instance_Stats.action | sort - count
```

## Visualization

Table (broken chains), Timeline (backup types), Single value (databases with gaps).

## References

- [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)
