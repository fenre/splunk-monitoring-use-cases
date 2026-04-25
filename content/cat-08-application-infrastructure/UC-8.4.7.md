<!-- AUTO-GENERATED from UC-8.4.7.json — DO NOT EDIT -->

---
id: "8.4.7"
title: "API Consumer Usage Tracking"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.4.7 · API Consumer Usage Tracking

## Description

Usage tracking per API consumer enables billing, quota management, and partner relationship management.

## Value

Usage tracking per API consumer enables billing, quota management, and partner relationship management.

## Implementation

Ensure API gateway logs include consumer identity. Aggregate usage by consumer, endpoint, and time period. Create monthly usage reports for billing/chargeback. Track usage trends per consumer for capacity planning.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Gateway access logs.
• Ensure the following data sources are available: API gateway logs with consumer identification (API key, OAuth client ID).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ensure API gateway logs include consumer identity. Aggregate usage by consumer, endpoint, and time period. Create monthly usage reports for billing/chargeback. Track usage trends per consumer for capacity planning.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=api sourcetype="kong:access"
| stats count, sum(request_size) as total_bytes, avg(latency) as avg_latency by consumer_id
| sort -count
```

Understanding this SPL

**API Consumer Usage Tracking** — Usage tracking per API consumer enables billing, quota management, and partner relationship management.

Documented **Data sources**: API gateway logs with consumer identification (API key, OAuth client ID). **App/TA** (typical add-on context): Gateway access logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: api; **sourcetype**: kong:access. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=api, sourcetype="kong:access". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by consumer_id** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.



Step 3 — Validate
Compare with the API gateway or mesh admin (Kong, Apigee, AWS API Gateway, etc.) and a raw log tail for the same time range.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (consumer usage summary), Bar chart (top consumers), Line chart (usage trends per consumer), Pie chart (traffic by consumer).

## SPL

```spl
index=api sourcetype="kong:access"
| stats count, sum(request_size) as total_bytes, avg(latency) as avg_latency by consumer_id
| sort -count
```

## Visualization

Table (consumer usage summary), Bar chart (top consumers), Line chart (usage trends per consumer), Pie chart (traffic by consumer).

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
