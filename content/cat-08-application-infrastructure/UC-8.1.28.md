<!-- AUTO-GENERATED from UC-8.1.28.json — DO NOT EDIT -->

---
id: "8.1.28"
title: "Envoy Downstream HTTP 429 Local Rate Limit"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.1.28 · Envoy Downstream HTTP 429 Local Rate Limit

## Description

429 responses from local rate limits protect upstreams but can signal abuse, mis-tuned quotas, or partner traffic spikes.

## Value

Balances protection with customer impact when throttling engages.

## Implementation

Scrape Prometheus text or stats lines; ensure listener dimensions are parsed. Correlate with `envoy.access` logs if enabled.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Envoy admin `/stats`, OpenTelemetry Collector, or Prometheus scraper to Splunk.
• Ensure the following data sources are available: `index=mesh` `sourcetype=envoy:stats` (`http.*.downstream_rq_429` counters).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Metric naming varies by Envoy version; broaden search to `*rq_429*` if your scrape format differs.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=mesh sourcetype="envoy:stats"
| search "downstream_rq_429"
| rex "http\\.(?<listener>[^.]+)\\.downstream_rq_429=(?<v>\d+)"
| stats latest(v) as rq_429 by listener
| where rq_429 > 0
```

Understanding this SPL

**Envoy Downstream HTTP 429 Local Rate Limit** — See the description and value fields in this use case JSON.

Documented **Data sources**: `index=mesh` `sourcetype=envoy:stats` (`http.*.downstream_rq_429` counters). **App/TA**: Envoy admin `/stats`, OpenTelemetry Collector, or Prometheus scraper to Splunk. Rename `index=` / `sourcetype=` to match your deployment.

**Pipeline walkthrough**

• Scope to the documented index and sourcetype, then apply transforms, thresholds, and `timechart`/`stats` as in the SPL above.

Step 3 — Validate
Compare with web server access logs on disk (Apache, NGINX, or W3C) for the same time range, or tail the same sourcetype in Search, to confirm status codes, URIs, and counts.


Step 4 — Operationalize
Add to a dashboard or alert; document ownership. Suggested visuals: Single value (429 rate), line chart per listener, table (cluster × route)..

## SPL

```spl
index=mesh sourcetype="envoy:stats"
| search "downstream_rq_429"
| rex "http\\.(?<listener>[^.]+)\\.downstream_rq_429=(?<v>\d+)"
| stats latest(v) as rq_429 by listener
| where rq_429 > 0
```

## Visualization

Single value (429 rate), line chart per listener, table (cluster × route).

## References

- [Envoy — Statistics overview](https://www.envoyproxy.io/docs/envoy/latest/operations/statistics)
