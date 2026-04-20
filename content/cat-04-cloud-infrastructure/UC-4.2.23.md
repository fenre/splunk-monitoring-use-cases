---
id: "4.2.23"
title: "Azure Database for MySQL/PostgreSQL Metrics"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.2.23 · Azure Database for MySQL/PostgreSQL Metrics

## Description

Managed MySQL/PostgreSQL CPU, storage, and connection metrics support capacity and performance management beyond Azure SQL.

## Value

Managed MySQL/PostgreSQL CPU, storage, and connection metrics support capacity and performance management beyond Azure SQL.

## Implementation

Collect Azure DB for MySQL/PostgreSQL metrics. Alert on CPU >80%, storage_percent >85%, or active_connections nearing max. Enable slow query log and ingest for query-level analysis.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: Azure Monitor metrics (percentage_cpu, storage_percent, active_connections).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect Azure DB for MySQL/PostgreSQL metrics. Alert on CPU >80%, storage_percent >85%, or active_connections nearing max. Enable slow query log and ingest for query-level analysis.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:metrics" namespace="Microsoft.DBforMySQL/servers" metricName="percentage_cpu"
| bin _time span=5m
| stats avg(average) as cpu_pct by _time, resourceId
| where cpu_pct > 80
```

Understanding this SPL

**Azure Database for MySQL/PostgreSQL Metrics** — Managed MySQL/PostgreSQL CPU, storage, and connection metrics support capacity and performance management beyond Azure SQL.

Documented **Data sources**: Azure Monitor metrics (percentage_cpu, storage_percent, active_connections). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:metrics. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:metrics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by _time, resourceId** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where cpu_pct > 80` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (CPU, storage, connections by server), Table (server, metrics), Gauge (storage %).

## SPL

```spl
index=azure sourcetype="mscs:azure:metrics" namespace="Microsoft.DBforMySQL/servers" metricName="percentage_cpu"
| bin _time span=5m
| stats avg(average) as cpu_pct by _time, resourceId
| where cpu_pct > 80
```

## Visualization

Line chart (CPU, storage, connections by server), Table (server, metrics), Gauge (storage %).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
