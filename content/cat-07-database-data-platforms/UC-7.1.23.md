---
id: "7.1.23"
title: "PostgreSQL Vacuum Activity"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.23 · PostgreSQL Vacuum Activity

## Description

Autovacuum running, dead tuples, and table bloat affect query performance. Monitoring ensures vacuum keeps pace with write workload and prevents bloat.

## Value

Autovacuum running, dead tuples, and table bloat affect query performance. Monitoring ensures vacuum keeps pace with write workload and prevents bloat.

## Implementation

Poll `pg_stat_user_tables` via DB Connect every hour. Extract `n_dead_tup`, `n_live_tup`, `last_autovacuum`. Compute dead tuple ratio and time since last vacuum. Alert when dead_ratio >5% or n_dead_tup >10000 for critical tables. Alert when last_autovacuum is >24 hours for high-churn tables. Track autovacuum runs from `pg_stat_progress_vacuum` if available.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk DB Connect or custom scripted input.
• Ensure the following data sources are available: `pg_stat_user_tables` (n_dead_tup, n_live_tup, last_autovacuum, last_vacuum).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll `pg_stat_user_tables` via DB Connect every hour. Extract `n_dead_tup`, `n_live_tup`, `last_autovacuum`. Compute dead tuple ratio and time since last vacuum. Alert when dead_ratio >5% or n_dead_tup >10000 for critical tables. Alert when last_autovacuum is >24 hours for high-churn tables. Track autovacuum runs from `pg_stat_progress_vacuum` if available.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="dbconnect:pg_stat_user_tables"
| eval dead_ratio=round(n_dead_tup/nullif(n_live_tup,0)*100, 2)
| where dead_ratio > 5 OR n_dead_tup > 10000
| eval hours_since_vacuum=round((now()-strptime(last_autovacuum,"%Y-%m-%d %H:%M:%S"))/3600, 1)
| table schemaname, relname, n_dead_tup, n_live_tup, dead_ratio, last_autovacuum, hours_since_vacuum
| sort -n_dead_tup
```

Understanding this SPL

**PostgreSQL Vacuum Activity** — Autovacuum running, dead tuples, and table bloat affect query performance. Monitoring ensures vacuum keeps pace with write workload and prevents bloat.

Documented **Data sources**: `pg_stat_user_tables` (n_dead_tup, n_live_tup, last_autovacuum, last_vacuum). **App/TA** (typical add-on context): Splunk DB Connect or custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: dbconnect:pg_stat_user_tables. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="dbconnect:pg_stat_user_tables". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **dead_ratio** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where dead_ratio > 5 OR n_dead_tup > 10000` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **hours_since_vacuum** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **PostgreSQL Vacuum Activity**): table schemaname, relname, n_dead_tup, n_live_tup, dead_ratio, last_autovacuum, hours_since_vacuum
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Databases.Instance_Stats by Instance_Stats.host, Instance_Stats.action | sort - count
```

Understanding this CIM / accelerated SPL

**PostgreSQL Vacuum Activity** — Autovacuum running, dead tuples, and table bloat affect query performance. Monitoring ensures vacuum keeps pace with write workload and prevents bloat.

Documented **Data sources**: `pg_stat_user_tables` (n_dead_tup, n_live_tup, last_autovacuum, last_vacuum). **App/TA** (typical add-on context): Splunk DB Connect or custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Databases.Instance_Stats` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (tables with bloat risk), Bar chart (dead tuples by table), Line chart (dead tuple ratio trend), Single value (tables overdue for vacuum).

## SPL

```spl
index=database sourcetype="dbconnect:pg_stat_user_tables"
| eval dead_ratio=round(n_dead_tup/nullif(n_live_tup,0)*100, 2)
| where dead_ratio > 5 OR n_dead_tup > 10000
| eval hours_since_vacuum=round((now()-strptime(last_autovacuum,"%Y-%m-%d %H:%M:%S"))/3600, 1)
| table schemaname, relname, n_dead_tup, n_live_tup, dead_ratio, last_autovacuum, hours_since_vacuum
| sort -n_dead_tup
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Databases.Instance_Stats by Instance_Stats.host, Instance_Stats.action | sort - count
```

## Visualization

Table (tables with bloat risk), Bar chart (dead tuples by table), Line chart (dead tuple ratio trend), Single value (tables overdue for vacuum).

## References

- [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)
- [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)
