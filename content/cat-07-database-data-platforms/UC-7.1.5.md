---
id: "7.1.5"
title: "Tablespace / Data File Growth"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.5 · Tablespace / Data File Growth

## Description

Uncontrolled database growth leads to disk space exhaustion and outages. Trending enables proactive storage provisioning.

## Value

Uncontrolled database growth leads to disk space exhaustion and outages. Trending enables proactive storage provisioning.

## Implementation

Poll database size metrics via DB Connect daily. Track growth rate per database. Use `predict` command for 30-day forecast. Alert when projected size exceeds available disk. Report top growing databases.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: DB Connect.
• Ensure the following data sources are available: `sys.database_files` (SQL Server), `dba_tablespaces` (Oracle), `pg_database_size()` (PostgreSQL).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll database size metrics via DB Connect daily. Track growth rate per database. Use `predict` command for 30-day forecast. Alert when projected size exceeds available disk. Report top growing databases.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="dbconnect:db_size"
| timechart span=1d latest(size_gb) as db_size by database_name
| predict db_size as predicted future_timespan=30
```

Understanding this SPL

**Tablespace / Data File Growth** — Uncontrolled database growth leads to disk space exhaustion and outages. Trending enables proactive storage provisioning.

Documented **Data sources**: `sys.database_files` (SQL Server), `dba_tablespaces` (Oracle), `pg_database_size()` (PostgreSQL). **App/TA** (typical add-on context): DB Connect. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: dbconnect:db_size. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="dbconnect:db_size". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1d** buckets with a separate series **by database_name** — ideal for trending and alerting on this use case.
• Pipeline stage (see **Tablespace / Data File Growth**): predict db_size as predicted future_timespan=30

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Databases.Instance_Stats by Instance_Stats.host, Instance_Stats.action span=1d | sort - count
```

Understanding this CIM / accelerated SPL

**Tablespace / Data File Growth** — Uncontrolled database growth leads to disk space exhaustion and outages. Trending enables proactive storage provisioning.

Documented **Data sources**: `sys.database_files` (SQL Server), `dba_tablespaces` (Oracle), `pg_database_size()` (PostgreSQL). **App/TA** (typical add-on context): DB Connect. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Databases.Instance_Stats` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (size trend with prediction), Table (databases with growth rate), Bar chart (top databases by size).

## SPL

```spl
index=database sourcetype="dbconnect:db_size"
| timechart span=1d latest(size_gb) as db_size by database_name
| predict db_size as predicted future_timespan=30
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Databases.Instance_Stats by Instance_Stats.host, Instance_Stats.action span=1d | sort - count
```

## Visualization

Line chart (size trend with prediction), Table (databases with growth rate), Bar chart (top databases by size).

## References

- [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)
