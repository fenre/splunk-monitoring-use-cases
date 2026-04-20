---
id: "7.1.33"
title: "Long-Running Query Detection (Active Sessions)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.33 · Long-Running Query Detection (Active Sessions)

## Description

Surfaces currently running queries exceeding elapsed threshold with SQL hash and wait type—faster triage than transaction-only UC-7.1.8.

## Value

Surfaces currently running queries exceeding elapsed threshold with SQL hash and wait type—faster triage than transaction-only UC-7.1.8.

## Implementation

Poll every 2m. Exclude known batch accounts via lookup. Alert when max_sec >900 for OLTP. Include optional `sql_text` sampling for compliance.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: DB Connect.
• Ensure the following data sources are available: `sys.dm_exec_requests`, `pg_stat_activity`, `V$SESSION` + `V$SQL`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll every 2m. Exclude known batch accounts via lookup. Alert when max_sec >900 for OLTP. Include optional `sql_text` sampling for compliance.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="dbconnect:active_requests"
| where elapsed_sec > 300 AND status="running"
| stats max(elapsed_sec) as max_sec by session_id, database_name, sql_hash
| table session_id database_name sql_hash max_sec wait_type
```

Understanding this SPL

**Long-Running Query Detection (Active Sessions)** — Surfaces currently running queries exceeding elapsed threshold with SQL hash and wait type—faster triage than transaction-only UC-7.1.8.

Documented **Data sources**: `sys.dm_exec_requests`, `pg_stat_activity`, `V$SESSION` + `V$SQL`. **App/TA** (typical add-on context): DB Connect. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: dbconnect:active_requests. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="dbconnect:active_requests". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where elapsed_sec > 300 AND status="running"` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by session_id, database_name, sql_hash** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Pipeline stage (see **Long-Running Query Detection (Active Sessions)**): table session_id database_name sql_hash max_sec wait_type

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.host, Query.action | sort - count
```

Understanding this CIM / accelerated SPL

**Long-Running Query Detection (Active Sessions)** — Surfaces currently running queries exceeding elapsed threshold with SQL hash and wait type—faster triage than transaction-only UC-7.1.8.

Documented **Data sources**: `sys.dm_exec_requests`, `pg_stat_activity`, `V$SESSION` + `V$SQL`. **App/TA** (typical add-on context): DB Connect. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Databases.Query` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (long-running sessions), Line chart (count of long queries), Single value (longest elapsed sec).

## SPL

```spl
index=database sourcetype="dbconnect:active_requests"
| where elapsed_sec > 300 AND status="running"
| stats max(elapsed_sec) as max_sec by session_id, database_name, sql_hash
| table session_id database_name sql_hash max_sec wait_type
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.host, Query.action | sort - count
```

## Visualization

Table (long-running sessions), Line chart (count of long queries), Single value (longest elapsed sec).

## References

- [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)
