<!-- AUTO-GENERATED from UC-5.8.19.json — DO NOT EDIT -->

---
id: "5.8.19"
title: "Multi-Organization Comparison and Benchmarking (Meraki)"
criticality: "low"
splunkPillar: "Observability"
---

# UC-5.8.19 · Multi-Organization Comparison and Benchmarking (Meraki)

## Description

Compares metrics across organizations to identify best practices and outliers.

## Value

Compares metrics across organizations to identify best practices and outliers.

## Implementation

Aggregate metrics across multiple organizations. Create comparison views.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki:api`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Aggregate metrics across multiple organizations. Create comparison views.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki:api"
| stats avg(health_score) as avg_health, count as device_count by organization
| sort - avg_health
```

Understanding this SPL

**Multi-Organization Comparison and Benchmarking (Meraki)** — Compares metrics across organizations to identify best practices and outliers.

Documented **Data sources**: `sourcetype=meraki:api`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki:api. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki:api". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by organization** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
In Meraki Dashboard, open the same organization or network, compare the metric (status, event feed, or admin log) to the Splunk result, and confirm the TA’s API key, org ID, and optional syslog reach the same index and sourcetype you used in the search.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Organization comparison bar chart; health rank table; benchmark line chart.

## SPL

```spl
index=cisco_network sourcetype="meraki:api"
| stats avg(health_score) as avg_health, count as device_count by organization
| sort - avg_health
```

## Visualization

Organization comparison bar chart; health rank table; benchmark line chart.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
