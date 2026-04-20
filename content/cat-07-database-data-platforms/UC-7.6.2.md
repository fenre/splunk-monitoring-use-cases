---
id: "7.6.2"
title: "Slow Query Volume Trending"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.6.2 · Slow Query Volume Trending

## Description

Counting queries exceeding a duration threshold per day quantifies database pain for developers and DBAs. Upward trends after releases often indicate missing indexes or plan regressions before p95 latency alerts fire.

## Value

Counting queries exceeding a duration threshold per day quantifies database pain for developers and DBAs. Upward trends after releases often indicate missing indexes or plan regressions before p95 latency alerts fire.

## Implementation

Tune the millisecond threshold per environment (OLTP vs reporting). Hash or truncate SQL text for cardinality control. Exclude known batch accounts via `user` lookup. Join top patterns to `EXPLAIN` workflow or query store IDs when available. Retention on verbose logs may require summary indexing to `sourcetype=stash`.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Native slow logs, Percona, `pg_stat_statements` export, SQL Server extended events.
• Ensure the following data sources are available: `index=db` `sourcetype=mysql:slow`, `sourcetype=postgresql:log`, `sourcetype=mssql:query`, `sourcetype=oracle:audit`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Tune the millisecond threshold per environment (OLTP vs reporting). Hash or truncate SQL text for cardinality control. Exclude known batch accounts via `user` lookup. Join top patterns to `EXPLAIN` workflow or query store IDs when available. Retention on verbose logs may require summary indexing to `sourcetype=stash`.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=db sourcetype IN ("mysql:slow","postgresql:log","mssql:query","oracle:sql")
| eval dur_ms=coalesce(query_time_ms, duration_ms, query_duration*1000)
| where dur_ms > 1000
| bin _time span=1d
| stats count as slow_queries by _time, db_name
| timechart span=1d sum(slow_queries) as daily_slow_queries by db_name limit=12
```

Understanding this SPL

**Slow Query Volume Trending** — Counting queries exceeding a duration threshold per day quantifies database pain for developers and DBAs. Upward trends after releases often indicate missing indexes or plan regressions before p95 latency alerts fire.

Documented **Data sources**: `index=db` `sourcetype=mysql:slow`, `sourcetype=postgresql:log`, `sourcetype=mssql:query`, `sourcetype=oracle:audit`. **App/TA** (typical add-on context): Native slow logs, Percona, `pg_stat_statements` export, SQL Server extended events. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: db.

**Pipeline walkthrough**

• Scopes the data: index=db. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **dur_ms** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where dur_ms > 1000` — typically the threshold or rule expression for this monitoring goal.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by _time, db_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `timechart` plots the metric over time using **span=1d** buckets with a separate series **by db_name limit=12** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Stacked column chart (slow queries per day by database), line chart (total slow count), table (top normalized query signatures).

## SPL

```spl
index=db sourcetype IN ("mysql:slow","postgresql:log","mssql:query","oracle:sql")
| eval dur_ms=coalesce(query_time_ms, duration_ms, query_duration*1000)
| where dur_ms > 1000
| bin _time span=1d
| stats count as slow_queries by _time, db_name
| timechart span=1d sum(slow_queries) as daily_slow_queries by db_name limit=12
```

## Visualization

Stacked column chart (slow queries per day by database), line chart (total slow count), table (top normalized query signatures).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
