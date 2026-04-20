---
id: "4.2.19"
title: "Azure Front Door / CDN Origin Errors and Cache Hit"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.2.19 · Azure Front Door / CDN Origin Errors and Cache Hit

## Description

Origin errors and low cache hit ratio impact latency and origin load. Essential for CDN and global app performance.

## Value

Origin errors and low cache hit ratio impact latency and origin load. Essential for CDN and global app performance.

## Implementation

Collect Front Door/CDN metrics. Alert when BackendHealthPercentage < 100%. Track RequestCount vs BackendRequestCount for cache hit ratio. Enable diagnostic logs for request-level analysis.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: Azure Monitor Front Door metrics (BackendHealthPercentage, RequestCount, BackendRequestCount).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect Front Door/CDN metrics. Alert when BackendHealthPercentage < 100%. Track RequestCount vs BackendRequestCount for cache hit ratio. Enable diagnostic logs for request-level analysis.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:metrics" namespace="Microsoft.Cdn/profiles" metricName="BackendHealthPercentage"
| where average < 100
| table _time resourceId endpoint average
```

Understanding this SPL

**Azure Front Door / CDN Origin Errors and Cache Hit** — Origin errors and low cache hit ratio impact latency and origin load. Essential for CDN and global app performance.

Documented **Data sources**: Azure Monitor Front Door metrics (BackendHealthPercentage, RequestCount, BackendRequestCount). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:metrics. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:metrics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where average < 100` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Azure Front Door / CDN Origin Errors and Cache Hit**): table _time resourceId endpoint average


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (origin health, request count), Table (endpoint, health %, cache hit), Gauge (cache hit %).

## SPL

```spl
index=azure sourcetype="mscs:azure:metrics" namespace="Microsoft.Cdn/profiles" metricName="BackendHealthPercentage"
| where average < 100
| table _time resourceId endpoint average
```

## Visualization

Line chart (origin health, request count), Table (endpoint, health %, cache hit), Gauge (cache hit %).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
