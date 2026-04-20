---
id: "7.1.1"
title: "Slow Query Detection"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.1.1 · Slow Query Detection

## Description

Slow queries at the P95/P99 level directly impact checkout, search, and reporting latency, hitting revenue and SLA commitments. They also hold locks and inflate CPU/IO, degrading performance for other tenants and queries. Prioritize fixes by business-critical endpoint and wait type, not just raw query duration.

## Value

Slow queries at the P95/P99 level directly impact checkout, search, and reporting latency, hitting revenue and SLA commitments. They also hold locks and inflate CPU/IO, degrading performance for other tenants and queries. Prioritize fixes by business-critical endpoint and wait type, not just raw query duration.

## Implementation

Enable MySQL slow query log (long_query_time=5). For SQL Server, poll DMVs via DB Connect. For PostgreSQL, enable `pg_stat_statements`. Ingest and alert on queries exceeding thresholds. Report top offenders weekly.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: DB Connect, Splunk_TA_microsoft-sqlserver, MySQL slow query log.
• Ensure the following data sources are available: Slow query logs, SQL Server DMVs (`sys.dm_exec_query_stats`), PostgreSQL `pg_stat_statements`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable MySQL slow query log (long_query_time=5). For SQL Server, poll DMVs via DB Connect. For PostgreSQL, enable `pg_stat_statements`. Ingest and alert on queries exceeding thresholds. Report top offenders weekly.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="mysql:slowquery"
| rex field=_raw "Query_time:\s+(?<query_time>[\d.]+)"
| where query_time > 5
| stats count, avg(query_time) as avg_time by db, user
| sort -avg_time
```

Understanding this SPL

**Slow Query Detection** — Slow queries at the P95/P99 level directly impact checkout, search, and reporting latency, hitting revenue and SLA commitments. They also hold locks and inflate CPU/IO, degrading performance for other tenants and queries. Prioritize fixes by business-critical endpoint and wait type, not just raw query duration.

Documented **Data sources**: Slow query logs, SQL Server DMVs (`sys.dm_exec_query_stats`), PostgreSQL `pg_stat_statements`. **App/TA** (typical add-on context): DB Connect, Splunk_TA_microsoft-sqlserver, MySQL slow query log. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: mysql:slowquery. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="mysql:slowquery". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• Filters the current rows with `where query_time > 5` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by db, user** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.host, Query.action | sort - count
```

Understanding this CIM / accelerated SPL

**Slow Query Detection** — Slow queries at the P95/P99 level directly impact checkout, search, and reporting latency, hitting revenue and SLA commitments. They also hold locks and inflate CPU/IO, degrading performance for other tenants and queries. Prioritize fixes by business-critical endpoint and wait type, not just raw query duration.

Documented **Data sources**: Slow query logs, SQL Server DMVs (`sys.dm_exec_query_stats`), PostgreSQL `pg_stat_statements`. **App/TA** (typical add-on context): DB Connect, Splunk_TA_microsoft-sqlserver, MySQL slow query log. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Databases.Query` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (slow queries with details), Bar chart (top slow queries by avg duration), Line chart (slow query count trend).

## SPL

```spl
index=database sourcetype="mysql:slowquery"
| rex field=_raw "Query_time:\s+(?<query_time>[\d.]+)"
| where query_time > 5
| stats count, avg(query_time) as avg_time by db, user
| sort -avg_time
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Databases.Query by Query.host, Query.action | sort - count
```

## Visualization

Table (slow queries with details), Bar chart (top slow queries by avg duration), Line chart (slow query count trend).

## References

- [CIM: Databases](https://docs.splunk.com/Documentation/CIM/latest/User/Databases)
