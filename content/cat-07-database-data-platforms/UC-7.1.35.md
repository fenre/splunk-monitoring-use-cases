---
id: "7.1.35"
title: "Connection Pool Exhaustion (Application vs Database Limit)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.1.35 · Connection Pool Exhaustion (Application vs Database Limit)

## Description

Joins app pool `activeThreads`/`waiting` with DB `session_count` to distinguish app-side pool starvation from DB `max_connections` hits.

## Value

Joins app pool `activeThreads`/`waiting` with DB `session_count` to distinguish app-side pool starvation from DB `max_connections` hits.

## Implementation

Ingest both sides; use `transaction` or `join` on host+service. Alert when either side >90%. Dashboard side-by-side.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: OpenTelemetry, DB Connect.
• Ensure the following data sources are available: HikariCP metrics, `pg_stat_activity` count, `sys.dm_exec_connections`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest both sides; use `transaction` or `join` on host+service. Alert when either side >90%. Dashboard side-by-side.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=application sourcetype="hikaricp:metrics"
| eval pct=round(active_connections/max_connections*100,1)
| where pct > 90 OR threads_awaiting_connection > 5
| table host pool_name pct threads_awaiting_connection active_connections max_connections
```

Understanding this SPL

**Connection Pool Exhaustion (Application vs Database Limit)** — Joins app pool `activeThreads`/`waiting` with DB `session_count` to distinguish app-side pool starvation from DB `max_connections` hits.

Documented **Data sources**: HikariCP metrics, `pg_stat_activity` count, `sys.dm_exec_connections`. **App/TA** (typical add-on context): OpenTelemetry, DB Connect. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: application; **sourcetype**: hikaricp:metrics. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=application, sourcetype="hikaricp:metrics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where pct > 90 OR threads_awaiting_connection > 5` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Connection Pool Exhaustion (Application vs Database Limit)**): table host pool_name pct threads_awaiting_connection active_connections max_connections

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Databases.Session_Info by Session_Info.host, Session_Info.action | sort - count
```

Understanding this CIM / accelerated SPL

**Connection Pool Exhaustion (Application vs Database Limit)** — Joins app pool `activeThreads`/`waiting` with DB `session_count` to distinguish app-side pool starvation from DB `max_connections` hits.

Documented **Data sources**: HikariCP metrics, `pg_stat_activity` count, `sys.dm_exec_connections`. **App/TA** (typical add-on context): OpenTelemetry, DB Connect. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Databases.Session_Info` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (app pool vs DB sessions), Line chart (pct over time), Table (hosts in danger).

## SPL

```spl
index=application sourcetype="hikaricp:metrics"
| eval pct=round(active_connections/max_connections*100,1)
| where pct > 90 OR threads_awaiting_connection > 5
| table host pool_name pct threads_awaiting_connection active_connections max_connections
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Databases.Session_Info by Session_Info.host, Session_Info.action | sort - count
```

## Visualization

Gauge (app pool vs DB sessions), Line chart (pct over time), Table (hosts in danger).

## References

- [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)
