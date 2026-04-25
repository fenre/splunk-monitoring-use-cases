<!-- AUTO-GENERATED from UC-4.4.20.json — DO NOT EDIT -->

---
id: "4.4.20"
title: "Multi-Cloud DNS Resolution Latency"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-4.4.20 · Multi-Cloud DNS Resolution Latency

## Description

Cross-provider DNS query performance comparison. Slow or failed resolution causes application timeouts and user experience degradation.

## Value

Cross-provider DNS query performance comparison. Slow or failed resolution causes application timeouts and user experience degradation.

## Implementation

Run periodic DNS probes (dig, nslookup, or custom script) from Lambda, Azure Functions, Cloud Functions, or on-prem agents. Measure resolution time per domain. Ingest results via HEC with fields: provider, vantage_point, domain, resolution_ms, success. Alert when avg latency exceeds 200ms or failure rate > 5%. Compare providers for DNS migration decisions.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (dig, nslookup).
• Ensure the following data sources are available: DNS query timing from multiple vantage points (AWS, Azure, GCP, on-prem).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Run periodic DNS probes (dig, nslookup, or custom script) from Lambda, Azure Functions, Cloud Functions, or on-prem agents. Measure resolution time per domain. Ingest results via HEC with fields: provider, vantage_point, domain, resolution_ms, success. Alert when avg latency exceeds 200ms or failure rate > 5%. Compare providers for DNS migration decisions.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cloud sourcetype="dns:resolution" 
| stats avg(resolution_ms) as avg_ms, max(resolution_ms) as max_ms, count as queries by provider, vantage_point, domain
| where avg_ms > 200 OR max_ms > 1000
| eval avg_ms=round(avg_ms, 1), max_ms=round(max_ms, 1)
| table provider vantage_point domain queries avg_ms max_ms
| sort -avg_ms
```

Understanding this SPL

**Multi-Cloud DNS Resolution Latency** — Cross-provider DNS query performance comparison. Slow or failed resolution causes application timeouts and user experience degradation.

Documented **Data sources**: DNS query timing from multiple vantage points (AWS, Azure, GCP, on-prem). **App/TA** (typical add-on context): Custom scripted input (dig, nslookup). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cloud; **sourcetype**: dns:resolution. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=cloud, sourcetype="dns:resolution". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by provider, vantage_point, domain** so each row reflects one combination of those dimensions.
• Filters the current rows with `where avg_ms > 200 OR max_ms > 1000` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **avg_ms** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **Multi-Cloud DNS Resolution Latency**): table provider vantage_point domain queries avg_ms max_ms
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (resolution latency by provider and domain over time), Table (provider, domain, avg ms), Heat map (provider vs domain).

## SPL

```spl
index=cloud sourcetype="dns:resolution" 
| stats avg(resolution_ms) as avg_ms, max(resolution_ms) as max_ms, count as queries by provider, vantage_point, domain
| where avg_ms > 200 OR max_ms > 1000
| eval avg_ms=round(avg_ms, 1), max_ms=round(max_ms, 1)
| table provider vantage_point domain queries avg_ms max_ms
| sort -avg_ms
```

## Visualization

Line chart (resolution latency by provider and domain over time), Table (provider, domain, avg ms), Heat map (provider vs domain).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
