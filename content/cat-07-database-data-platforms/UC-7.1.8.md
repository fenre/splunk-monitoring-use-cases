---
id: "7.1.8"
title: "Long-Running Transaction Detection"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.8 · Long-Running Transaction Detection

## Description

Long transactions hold locks, causing blocking chains that degrade application performance for many users.

## Value

Long transactions hold locks, causing blocking chains that degrade application performance for many users.

## Implementation

Poll active transactions via DB Connect every 5 minutes. Alert when any transaction exceeds 5 minutes. Include SQL text and blocking information. Escalate transactions blocking other sessions.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: DB Connect.
• Ensure the following data sources are available: `sys.dm_exec_requests` (SQL Server), `pg_stat_activity` (PostgreSQL), Oracle `v$transaction`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll active transactions via DB Connect every 5 minutes. Alert when any transaction exceeds 5 minutes. Include SQL text and blocking information. Escalate transactions blocking other sessions.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="dbconnect:active_transactions"
| where transaction_duration_sec > 300
| table _time, server, database_name, user, transaction_duration_sec, sql_text
| sort -transaction_duration_sec
```

Understanding this SPL

**Long-Running Transaction Detection** — Long transactions hold locks, causing blocking chains that degrade application performance for many users.

Documented **Data sources**: `sys.dm_exec_requests` (SQL Server), `pg_stat_activity` (PostgreSQL), Oracle `v$transaction`. **App/TA** (typical add-on context): DB Connect. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: dbconnect:active_transactions. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="dbconnect:active_transactions". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where transaction_duration_sec > 300` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Long-Running Transaction Detection**): table _time, server, database_name, user, transaction_duration_sec, sql_text
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.host, Query.action | sort - count
```

Understanding this CIM / accelerated SPL

**Long-Running Transaction Detection** — Long transactions hold locks, causing blocking chains that degrade application performance for many users.

Documented **Data sources**: `sys.dm_exec_requests` (SQL Server), `pg_stat_activity` (PostgreSQL), Oracle `v$transaction`. **App/TA** (typical add-on context): DB Connect. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Databases.Query` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (active long transactions), Single value (longest active transaction), Timeline (long transaction events).

## SPL

```spl
index=database sourcetype="dbconnect:active_transactions"
| where transaction_duration_sec > 300
| table _time, server, database_name, user, transaction_duration_sec, sql_text
| sort -transaction_duration_sec
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.host, Query.action | sort - count
```

## Visualization

Table (active long transactions), Single value (longest active transaction), Timeline (long transaction events).

## References

- [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)
