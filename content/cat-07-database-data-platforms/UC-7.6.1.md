---
id: "7.6.1"
title: "Database Connection Pool Utilization Trending"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.6.1 · Database Connection Pool Utilization Trending

## Description

Peak connection pool utilization over 30 days shows how close applications are to exhausting database sessions. Rising peaks justify pool tuning, connection string fixes, or server scale-up before login storms cause outages.

## Value

Peak connection pool utilization over 30 days shows how close applications are to exhausting database sessions. Rising peaks justify pool tuning, connection string fixes, or server scale-up before login storms cause outages.

## Implementation

Map instance identifiers consistently (`host` + `port` + `db_name`). For PgBouncer or RDS proxy, track pool versus backend limits separately. Alert on sustained peaks above policy (for example 80%). Combine with application-side pool settings to find mismatches. Use `perc95` if peaks are noisy from batch jobs only.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk DB Connect, vendor DB TAs (MySQL Enterprise, PostgreSQL, Oracle, SQL Server), application pool metrics if forwarded.
• Ensure the following data sources are available: `index=db` `sourcetype=mysql:status`, `sourcetype=postgresql:metrics`, `sourcetype=mssql:perf`, `sourcetype=oracle:session`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Map instance identifiers consistently (`host` + `port` + `db_name`). For PgBouncer or RDS proxy, track pool versus backend limits separately. Alert on sustained peaks above policy (for example 80%). Combine with application-side pool settings to find mismatches. Use `perc95` if peaks are noisy from batch jobs only.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=db (sourcetype="mysql:status" OR sourcetype="postgresql:metrics" OR sourcetype="mssql:perf" OR sourcetype="oracle:session")
| eval active=coalesce(threads_connected, numbackends, active_sessions, session_count)
| eval max_conn=coalesce(max_connections, max_connections_setting, session_limit)
| eval pool_pct=if(max_conn>0, round(100*active/max_conn,2), null())
| timechart span=1d max(pool_pct) as peak_pool_util_pct by instance
```

Understanding this SPL

**Database Connection Pool Utilization Trending** — Peak connection pool utilization over 30 days shows how close applications are to exhausting database sessions. Rising peaks justify pool tuning, connection string fixes, or server scale-up before login storms cause outages.

Documented **Data sources**: `index=db` `sourcetype=mysql:status`, `sourcetype=postgresql:metrics`, `sourcetype=mssql:perf`, `sourcetype=oracle:session`. **App/TA** (typical add-on context): Splunk DB Connect, vendor DB TAs (MySQL Enterprise, PostgreSQL, Oracle, SQL Server), application pool metrics if forwarded. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: db; **sourcetype**: mysql:status, postgresql:metrics, mssql:perf, oracle:session. Those sourcetypes align with what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=db, sourcetype="mysql:status". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **active** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **max_conn** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **pool_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=1d** buckets with a separate series **by instance** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (peak pool % by instance), column chart (30-day max), table (instances over threshold).

## SPL

```spl
index=db (sourcetype="mysql:status" OR sourcetype="postgresql:metrics" OR sourcetype="mssql:perf" OR sourcetype="oracle:session")
| eval active=coalesce(threads_connected, numbackends, active_sessions, session_count)
| eval max_conn=coalesce(max_connections, max_connections_setting, session_limit)
| eval pool_pct=if(max_conn>0, round(100*active/max_conn,2), null())
| timechart span=1d max(pool_pct) as peak_pool_util_pct by instance
```

## Visualization

Line chart (peak pool % by instance), column chart (30-day max), table (instances over threshold).

## References

- [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)
