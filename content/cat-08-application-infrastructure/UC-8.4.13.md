<!-- AUTO-GENERATED from UC-8.4.13.json — DO NOT EDIT -->

---
id: "8.4.13"
title: "API Response Time SLA Breaches"
criticality: "critical"
splunkPillar: "Security"
---

# UC-8.4.13 · API Response Time SLA Breaches

## Description

p95/p99 latency from gateway access logs vs documented SLA per route (`/api/v1/orders`). Complements UC-8.4.2 with SLA lookup join.

## Value

p95/p99 latency from gateway access logs vs documented SLA per route (`/api/v1/orders`). Complements UC-8.4.2 with SLA lookup join.

## Implementation

Maintain SLA lookup per route. Run every 15m. Alert on breach for 3 consecutive windows. Exclude OPTIONS from stats.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Kong, Envoy, AWS API GW access logs.
• Ensure the following data sources are available: `latency`, `request_uri`, `route_id`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Maintain SLA lookup per route. Run every 15m. Alert on breach for 3 consecutive windows. Exclude OPTIONS from stats.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=api sourcetype="kong:access"
| lookup api_route_sla route_uri OUTPUT p95_ms_sla
| stats perc95(latency) as p95 by route_uri
| where p95 > p95_ms_sla
| table route_uri p95 p95_ms_sla
```

Understanding this SPL

**API Response Time SLA Breaches** — p95/p99 latency from gateway access logs vs documented SLA per route (`/api/v1/orders`). Complements UC-8.4.2 with SLA lookup join.

Documented **Data sources**: `latency`, `request_uri`, `route_id`. **App/TA** (typical add-on context): Kong, Envoy, AWS API GW access logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: api; **sourcetype**: kong:access. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=api, sourcetype="kong:access". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• `stats` rolls up events into metrics; results are split **by route_uri** so each row reflects one combination of those dimensions.
• Filters the current rows with `where p95 > p95_ms_sla` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **API Response Time SLA Breaches**): table route_uri p95 p95_ms_sla


Step 3 — Validate
Compare with the API gateway or mesh admin (Kong, Apigee, AWS API Gateway, etc.) and a raw log tail for the same time range.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (p95 vs SLA), Table (breached routes), Heatmap (route × hour).

## SPL

```spl
index=api sourcetype="kong:access"
| lookup api_route_sla route_uri OUTPUT p95_ms_sla
| stats perc95(latency) as p95 by route_uri
| where p95 > p95_ms_sla
| table route_uri p95 p95_ms_sla
```

## CIM SPL

```spl
| tstats `summariesonly` perc95(Web.duration) as p95_ms avg(Web.duration) as avg_ms
  from datamodel=Web.Web
  by Web.dest Web.uri_path span=5m
| where p95_ms > 2000
```

## Visualization

Line chart (p95 vs SLA), Table (breached routes), Heatmap (route × hour).

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
