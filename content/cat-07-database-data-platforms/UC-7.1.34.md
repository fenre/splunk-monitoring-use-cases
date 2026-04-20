---
id: "7.1.34"
title: "Deadlock Frequency by Database"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.34 · Deadlock Frequency by Database

## Description

Counts deadlocks per hour/database to detect code regressions after releases. Complements UC-7.1.2 event search with KPIs.

## Value

Counts deadlocks per hour/database to detect code regressions after releases. Complements UC-7.1.2 event search with KPIs.

## Implementation

Parse database name from deadlock XML if available. Alert when hourly deadlocks exceed baseline. Tie to release markers.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Error log ingestion, extended events.
• Ensure the following data sources are available: SQL Server errorlog deadlock graph frequency, PostgreSQL `log_lock_waits`, Oracle ORA-00060.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Parse database name from deadlock XML if available. Alert when hourly deadlocks exceed baseline. Tie to release markers.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="mssql:errorlog"
| search deadlock OR "Deadlock"
| bucket _time span=1h
| stats count as deadlocks by database_name, _time
| where deadlocks > 5
```

Understanding this SPL

**Deadlock Frequency by Database** — Counts deadlocks per hour/database to detect code regressions after releases. Complements UC-7.1.2 event search with KPIs.

Documented **Data sources**: SQL Server errorlog deadlock graph frequency, PostgreSQL `log_lock_waits`, Oracle ORA-00060. **App/TA** (typical add-on context): Error log ingestion, extended events. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: mssql:errorlog. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="mssql:errorlog". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by database_name, _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where deadlocks > 5` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.host, Query.action | sort - count
```

Understanding this CIM / accelerated SPL

**Deadlock Frequency by Database** — Counts deadlocks per hour/database to detect code regressions after releases. Complements UC-7.1.2 event search with KPIs.

Documented **Data sources**: SQL Server errorlog deadlock graph frequency, PostgreSQL `log_lock_waits`, Oracle ORA-00060. **App/TA** (typical add-on context): Error log ingestion, extended events. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Databases.Query` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (deadlocks over time), Bar chart (by database), Single value (deadlocks today).

## SPL

```spl
index=database sourcetype="mssql:errorlog"
| search deadlock OR "Deadlock"
| bucket _time span=1h
| stats count as deadlocks by database_name, _time
| where deadlocks > 5
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.host, Query.action | sort - count
```

## Visualization

Line chart (deadlocks over time), Bar chart (by database), Single value (deadlocks today).

## References

- [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)
