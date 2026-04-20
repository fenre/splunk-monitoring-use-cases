---
id: "3.6.6"
title: "Ingress Traffic Volume Trending"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.6.6 · Ingress Traffic Volume Trending

## Description

Ingress requests per second trended weekly shows growth in user load, campaign effects, or misconfigured clients hammering APIs. Supports capacity planning for ingress controllers and upstream services.

## Value

Ingress requests per second trended weekly shows growth in user load, campaign effects, or misconfigured clients hammering APIs. Supports capacity planning for ingress controllers and upstream services.

## Implementation

Prefer RED metrics from the service mesh or ingress controller scraped into Splunk metrics. If only access logs exist, each log line represents one request. Use span=1w for medium-term trending. Tag by ingress or virtual host for breakdowns. Correlate traffic spikes with marketing campaigns or releases.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: NGINX Ingress Controller / Istio Ingress Gateway logs forwarded to Splunk.
• Ensure the following data sources are available: `index=containers sourcetype=nginx:ingress` or `sourcetype=istio:ingress`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Prefer RED metrics from the service mesh or ingress controller scraped into Splunk metrics. If only access logs exist, each log line represents one request. Use span=1w for medium-term trending. Tag by ingress or virtual host for breakdowns. Correlate traffic spikes with marketing campaigns or releases.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype IN ("nginx:ingress", "istio:ingress")
| timechart span=1w count as weekly_requests
| eval avg_rps=round(weekly_requests/(7*86400), 2)
| trendline sma4(avg_rps) as rps_trend
```

Understanding this SPL

**Ingress Traffic Volume Trending** — Ingress requests per second trended weekly shows growth in user load, campaign effects, or misconfigured clients hammering APIs. Supports capacity planning for ingress controllers and upstream services.

Documented **Data sources**: `index=containers sourcetype=nginx:ingress` or `sourcetype=istio:ingress`. **App/TA** (typical add-on context): NGINX Ingress Controller / Istio Ingress Gateway logs forwarded to Splunk. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers.

**Pipeline walkthrough**

• Scopes the data: index=containers. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1w** buckets — ideal for trending and alerting on this use case.
• `eval` defines or adjusts **avg_rps** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **Ingress Traffic Volume Trending**): trendline sma4(avg_rps) as rps_trend


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (weekly average RPS with 4-week SMA), optional breakdown by ingress class or hostname.

## SPL

```spl
index=containers sourcetype IN ("nginx:ingress", "istio:ingress")
| timechart span=1w count as weekly_requests
| eval avg_rps=round(weekly_requests/(7*86400), 2)
| trendline sma4(avg_rps) as rps_trend
```

## Visualization

Line chart (weekly average RPS with 4-week SMA), optional breakdown by ingress class or hostname.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
