<!-- AUTO-GENERATED from UC-8.4.2.json — DO NOT EDIT -->

---
id: "8.4.2"
title: "API Latency Percentiles"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.4.2 · API Latency Percentiles

## Description

P95/P99 latency reveals the experience of the slowest users. Averages hide tail latency problems.

## Value

P95/P99 latency reveals the experience of the slowest users. Averages hide tail latency problems.

## Implementation

Ensure gateway logs include request and upstream latency. Calculate p50/p95/p99 per endpoint. Alert when p95 exceeds SLA target. Track percentile trends to detect gradual degradation before it becomes critical.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom log input, gateway metrics.
• Ensure the following data sources are available: API gateway access logs with latency fields.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ensure gateway logs include request and upstream latency. Calculate p50/p95/p99 per endpoint. Alert when p95 exceeds SLA target. Track percentile trends to detect gradual degradation before it becomes critical.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=api sourcetype="kong:access"
| stats perc50(latency) as p50, perc95(latency) as p95, perc99(latency) as p99 by request_uri
| where p95 > 1000
| sort -p99
```

Understanding this SPL

**API Latency Percentiles** — P95/P99 latency reveals the experience of the slowest users. Averages hide tail latency problems.

Documented **Data sources**: API gateway access logs with latency fields. **App/TA** (typical add-on context): Custom log input, gateway metrics. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: api; **sourcetype**: kong:access. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=api, sourcetype="kong:access". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by request_uri** so each row reflects one combination of those dimensions.
• Filters the current rows with `where p95 > 1000` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare with the API gateway or mesh admin (Kong, Apigee, AWS API Gateway, etc.) and a raw log tail for the same time range.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (p50/p95/p99 over time), Table (endpoints with high latency), Histogram (latency distribution).

## SPL

```spl
index=api sourcetype="kong:access"
| stats perc50(latency) as p50, perc95(latency) as p95, perc99(latency) as p99 by request_uri
| where p95 > 1000
| sort -p99
```

## CIM SPL

```spl
| tstats `summariesonly` perc50(Web.duration) as p50 perc95(Web.duration) as p95 perc99(Web.duration) as p99
  from datamodel=Web.Web
  by Web.uri_path span=5m
| where p95 > 1000
```

## Visualization

Line chart (p50/p95/p99 over time), Table (endpoints with high latency), Histogram (latency distribution).

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
