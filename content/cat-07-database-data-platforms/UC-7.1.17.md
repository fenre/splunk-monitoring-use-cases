---
id: "7.1.17"
title: "Database Connection Pool Exhaustion"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.1.17 · Database Connection Pool Exhaustion

## Description

When the application connection pool or database max_connections is exhausted, new requests fail with connection errors. Detecting high connection count and pool saturation prevents outages.

## Value

When the application connection pool or database max_connections is exhausted, new requests fail with connection errors. Detecting high connection count and pool saturation prevents outages.

## Implementation

Use DB Connect to poll session/connection count every 1–5 minutes. Compare to max_connections (or pool size). Alert when utilization exceeds 85%. Correlate with application logs for connection leak or traffic spike.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `splunk_app_db_connect`, database performance views.
• Ensure the following data sources are available: Oracle `V$SESSION`/`V$PROCESS`, PostgreSQL `pg_stat_activity`, MySQL `SHOW PROCESSLIST`, SQL Server `sys.dm_exec_connections`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Use DB Connect to poll session/connection count every 1–5 minutes. Compare to max_connections (or pool size). Alert when utilization exceeds 85%. Correlate with application logs for connection leak or traffic spike.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
| dbxquery connection="oracle_prod" query="SELECT COUNT(*) AS conn_count FROM v\$session WHERE type='USER'"
| eval usage_pct=round(conn_count/400*100, 1)
| where usage_pct > 85
| table conn_count usage_pct
```

Understanding this SPL

**Database Connection Pool Exhaustion** — When the application connection pool or database max_connections is exhausted, new requests fail with connection errors. Detecting high connection count and pool saturation prevents outages.

Documented **Data sources**: Oracle `V$SESSION`/`V$PROCESS`, PostgreSQL `pg_stat_activity`, MySQL `SHOW PROCESSLIST`, SQL Server `sys.dm_exec_connections`. **App/TA** (typical add-on context): `splunk_app_db_connect`, database performance views. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Pipeline stage (see **Database Connection Pool Exhaustion**): dbxquery connection="oracle_prod" query="SELECT COUNT(*) AS conn_count FROM v\$session WHERE type='USER'"
• `eval` defines or adjusts **usage_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where usage_pct > 85` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Database Connection Pool Exhaustion**): table conn_count usage_pct


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (connection count vs max), Line chart (connections over time), Table (by program/user).

## SPL

```spl
| dbxquery connection="oracle_prod" query="SELECT COUNT(*) AS conn_count FROM v\$session WHERE type='USER'"
| eval usage_pct=round(conn_count/400*100, 1)
| where usage_pct > 85
| table conn_count usage_pct
```

## Visualization

Gauge (connection count vs max), Line chart (connections over time), Table (by program/user).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
