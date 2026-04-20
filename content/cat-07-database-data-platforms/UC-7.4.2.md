---
id: "7.4.2"
title: "Cluster Scaling Events"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.4.2 · Cluster Scaling Events

## Description

Tracks auto-scaling decisions for cost optimization. Identifies whether current scaling policies match workload patterns.

## Value

Tracks auto-scaling decisions for cost optimization. Identifies whether current scaling policies match workload patterns.

## Implementation

Poll warehouse event history. Track resume/suspend/scaling frequency. Correlate with query concurrency to validate scaling policies. Alert on unexpected scaling events outside business hours.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom API input, cloud provider TAs.
• Ensure the following data sources are available: Snowflake `WAREHOUSE_EVENTS_HISTORY`, Redshift resize events, BigQuery slot utilization.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll warehouse event history. Track resume/suspend/scaling frequency. Correlate with query concurrency to validate scaling policies. Alert on unexpected scaling events outside business hours.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=datawarehouse sourcetype="snowflake:warehouse_events"
| search event_name IN ("RESIZE_CLUSTER","SUSPEND_CLUSTER","RESUME_CLUSTER")
| timechart span=1h count by event_name, warehouse_name
```

Understanding this SPL

**Cluster Scaling Events** — Tracks auto-scaling decisions for cost optimization. Identifies whether current scaling policies match workload patterns.

Documented **Data sources**: Snowflake `WAREHOUSE_EVENTS_HISTORY`, Redshift resize events, BigQuery slot utilization. **App/TA** (typical add-on context): Custom API input, cloud provider TAs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: datawarehouse; **sourcetype**: snowflake:warehouse_events. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=datawarehouse, sourcetype="snowflake:warehouse_events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• `timechart` plots the metric over time using **span=1h** buckets with a separate series **by event_name, warehouse_name** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (scaling events), Stacked bar (events by type per day), Table (warehouse scaling summary).

## SPL

```spl
index=datawarehouse sourcetype="snowflake:warehouse_events"
| search event_name IN ("RESIZE_CLUSTER","SUSPEND_CLUSTER","RESUME_CLUSTER")
| timechart span=1h count by event_name, warehouse_name
```

## Visualization

Timeline (scaling events), Stacked bar (events by type per day), Table (warehouse scaling summary).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
