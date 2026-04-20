---
id: "7.1.3"
title: "Connection Pool Exhaustion"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.1.3 · Connection Pool Exhaustion

## Description

Exhausted connection pools cause application failures. Monitoring prevents outages and guides pool sizing decisions.

## Value

Exhausted connection pools cause application failures. Monitoring prevents outages and guides pool sizing decisions.

## Implementation

Poll connection counts via DB Connect every 5 minutes. Compare against configured maximum. Alert at 80% and 95% thresholds. Track by application/user to identify connection leaks.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: DB Connect, performance counters.
• Ensure the following data sources are available: SQL Server DMVs (`sys.dm_exec_connections`), PostgreSQL `pg_stat_activity`, app server connection pool metrics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll connection counts via DB Connect every 5 minutes. Compare against configured maximum. Alert at 80% and 95% thresholds. Track by application/user to identify connection leaks.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="dbconnect:mssql_connections"
| timechart span=5m max(active_connections) as active, max(max_connections) as max_limit
| eval pct_used=round(active/max_limit*100,1)
| where pct_used > 80
```

Understanding this SPL

**Connection Pool Exhaustion** — Exhausted connection pools cause application failures. Monitoring prevents outages and guides pool sizing decisions.

Documented **Data sources**: SQL Server DMVs (`sys.dm_exec_connections`), PostgreSQL `pg_stat_activity`, app server connection pool metrics. **App/TA** (typical add-on context): DB Connect, performance counters. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: dbconnect:mssql_connections. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="dbconnect:mssql_connections". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets — ideal for trending and alerting on this use case.
• `eval` defines or adjusts **pct_used** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where pct_used > 80` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.host, Query.action span=5m | sort - count
```

Understanding this CIM / accelerated SPL

**Connection Pool Exhaustion** — Exhausted connection pools cause application failures. Monitoring prevents outages and guides pool sizing decisions.

Documented **Data sources**: SQL Server DMVs (`sys.dm_exec_connections`), PostgreSQL `pg_stat_activity`, app server connection pool metrics. **App/TA** (typical add-on context): DB Connect, performance counters. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Databases.Query` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (% connections used), Line chart (connections over time), Table (connections by application).

## SPL

```spl
index=database sourcetype="dbconnect:mssql_connections"
| timechart span=5m max(active_connections) as active, max(max_connections) as max_limit
| eval pct_used=round(active/max_limit*100,1)
| where pct_used > 80
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.host, Query.action span=5m | sort - count
```

## Visualization

Gauge (% connections used), Line chart (connections over time), Table (connections by application).

## References

- [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)
