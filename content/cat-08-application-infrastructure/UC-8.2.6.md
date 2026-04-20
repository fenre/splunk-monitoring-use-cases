---
id: "8.2.6"
title: "Connection Pool Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.2.6 · Connection Pool Monitoring

## Description

Exhausted JDBC/database connection pools cause application errors and cascading failures. Monitoring prevents connection starvation.

## Value

Exhausted JDBC/database connection pools cause application errors and cascading failures. Monitoring prevents connection starvation.

## Implementation

Poll JDBC connection pool MBeans via JMX. Track active, idle, and waiting connections. Alert at 80% pool utilization. Monitor connection wait time — high wait times indicate pool exhaustion even before 100%. Correlate with database latency.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `TA-jmx`, application metrics.
• Ensure the following data sources are available: JMX DataSource MBeans, HikariCP metrics, application framework metrics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll JDBC connection pool MBeans via JMX. Track active, idle, and waiting connections. Alert at 80% pool utilization. Monitor connection wait time — high wait times indicate pool exhaustion even before 100%. Correlate with database latency.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=jmx sourcetype="jmx:datasource"
| eval pct_used=round(numActive/maxTotal*100,1)
| timechart span=5m max(pct_used) as pool_pct by host, pool_name
| where pool_pct > 80
```

Understanding this SPL

**Connection Pool Monitoring** — Exhausted JDBC/database connection pools cause application errors and cascading failures. Monitoring prevents connection starvation.

Documented **Data sources**: JMX DataSource MBeans, HikariCP metrics, application framework metrics. **App/TA** (typical add-on context): `TA-jmx`, application metrics. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: jmx; **sourcetype**: jmx:datasource. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=jmx, sourcetype="jmx:datasource". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **pct_used** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by host, pool_name** — ideal for trending and alerting on this use case.
• Filters the current rows with `where pool_pct > 80` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (% pool used), Line chart (pool utilization over time), Table (pools approaching limits).

## SPL

```spl
index=jmx sourcetype="jmx:datasource"
| eval pct_used=round(numActive/maxTotal*100,1)
| timechart span=5m max(pct_used) as pool_pct by host, pool_name
| where pool_pct > 80
```

## Visualization

Gauge (% pool used), Line chart (pool utilization over time), Table (pools approaching limits).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
