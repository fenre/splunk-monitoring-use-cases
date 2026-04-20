---
id: "7.4.5"
title: "Warehouse Utilization"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.4.5 · Warehouse Utilization

## Description

Right-sizing warehouses reduces cost while maintaining performance. Utilization data drives scaling policy decisions.

## Value

Right-sizing warehouses reduces cost while maintaining performance. Utilization data drives scaling policy decisions.

## Implementation

Poll warehouse utilization metrics every 15 minutes. Track running vs queued queries. Alert when queuing occurs consistently (indicates undersized warehouse). Identify idle warehouses for auto-suspend policy adjustment.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom API input.
• Ensure the following data sources are available: Snowflake `WAREHOUSE_LOAD_HISTORY`, Redshift `WLM_QUEUE_STATE`, BigQuery reservation utilization.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll warehouse utilization metrics every 15 minutes. Track running vs queued queries. Alert when queuing occurs consistently (indicates undersized warehouse). Identify idle warehouses for auto-suspend policy adjustment.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=datawarehouse sourcetype="snowflake:warehouse_load"
| timechart span=15m avg(AVG_RUNNING) as avg_queries, avg(AVG_QUEUED_LOAD) as avg_queued by WAREHOUSE_NAME
| where avg_queued > 1
```

Understanding this SPL

**Warehouse Utilization** — Right-sizing warehouses reduces cost while maintaining performance. Utilization data drives scaling policy decisions.

Documented **Data sources**: Snowflake `WAREHOUSE_LOAD_HISTORY`, Redshift `WLM_QUEUE_STATE`, BigQuery reservation utilization. **App/TA** (typical add-on context): Custom API input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: datawarehouse; **sourcetype**: snowflake:warehouse_load. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=datawarehouse, sourcetype="snowflake:warehouse_load". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=15m** buckets with a separate series **by WAREHOUSE_NAME** — ideal for trending and alerting on this use case.
• Filters the current rows with `where avg_queued > 1` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (running vs queued queries), Heatmap (warehouse × hour utilization), Table (underutilized warehouses), Bar chart (utilization by warehouse).

## SPL

```spl
index=datawarehouse sourcetype="snowflake:warehouse_load"
| timechart span=15m avg(AVG_RUNNING) as avg_queries, avg(AVG_QUEUED_LOAD) as avg_queued by WAREHOUSE_NAME
| where avg_queued > 1
```

## Visualization

Line chart (running vs queued queries), Heatmap (warehouse × hour utilization), Table (underutilized warehouses), Bar chart (utilization by warehouse).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
