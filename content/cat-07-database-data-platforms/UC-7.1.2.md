---
id: "7.1.2"
title: "Deadlock Monitoring"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.1.2 · Deadlock Monitoring

## Description

Deadlocks cause transaction failures and application errors. Rapid detection and root cause analysis minimizes impact.

## Value

Deadlocks cause transaction failures and application errors. Rapid detection and root cause analysis minimizes impact.

## Implementation

Enable trace flag 1222 for SQL Server deadlock graphs. For PostgreSQL, set `log_lock_waits=on` and `deadlock_timeout=1s`. Ingest error logs. Alert on any deadlock occurrence. Parse deadlock graphs for involved queries/objects.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk_TA_microsoft-sqlserver, database error logs.
• Ensure the following data sources are available: SQL Server error log (deadlock graph), PostgreSQL `log_lock_waits`, Oracle alert log.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable trace flag 1222 for SQL Server deadlock graphs. For PostgreSQL, set `log_lock_waits=on` and `deadlock_timeout=1s`. Ingest error logs. Alert on any deadlock occurrence. Parse deadlock graphs for involved queries/objects.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="mssql:errorlog"
| search "deadlock" OR "Deadlock"
| stats count by _time, database_name
| timechart span=1h sum(count) as deadlocks
```

Understanding this SPL

**Deadlock Monitoring** — Deadlocks cause transaction failures and application errors. Rapid detection and root cause analysis minimizes impact.

Documented **Data sources**: SQL Server error log (deadlock graph), PostgreSQL `log_lock_waits`, Oracle alert log. **App/TA** (typical add-on context): Splunk_TA_microsoft-sqlserver, database error logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: mssql:errorlog. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="mssql:errorlog". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• `stats` rolls up events into metrics; results are split **by _time, database_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `timechart` plots the metric over time using **span=1h** buckets — ideal for trending and alerting on this use case.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.host, Query.action span=1h | sort - count
```

Understanding this CIM / accelerated SPL

**Deadlock Monitoring** — Deadlocks cause transaction failures and application errors. Rapid detection and root cause analysis minimizes impact.

Documented **Data sources**: SQL Server error log (deadlock graph), PostgreSQL `log_lock_waits`, Oracle alert log. **App/TA** (typical add-on context): Splunk_TA_microsoft-sqlserver, database error logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Databases.Query` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (deadlocks over time), Table (deadlock details), Single value (deadlocks today).

## SPL

```spl
index=database sourcetype="mssql:errorlog"
| search "deadlock" OR "Deadlock"
| stats count by _time, database_name
| timechart span=1h sum(count) as deadlocks
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.host, Query.action span=1h | sort - count
```

## Visualization

Line chart (deadlocks over time), Table (deadlock details), Single value (deadlocks today).

## References

- [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)
