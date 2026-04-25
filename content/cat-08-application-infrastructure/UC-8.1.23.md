<!-- AUTO-GENERATED from UC-8.1.23.json — DO NOT EDIT -->

---
id: "8.1.23"
title: "Traefik JSON Access Log Request Duration"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.1.23 · Traefik JSON Access Log Request Duration

## Description

Traefik access logs expose `Duration` per request. P95 by `RouterName` or `ServiceName` isolates slow routes and backends.

## Value

Pinpoints which Traefik routers degrade first during incidents.

## Implementation

Enable JSON access logs; install the Traefik add-on or parse `Duration`, `DownstreamStatus`, and router fields at ingest.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Add On for Traefik Proxy (Splunkbase app 6733).
• Ensure the following data sources are available: `index=web` `sourcetype=traefik:access` JSON access log (`Duration` in nanoseconds).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Use JSON access format; if fields are in `_raw`, add `spath` or KV extraction for `Duration`.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=web sourcetype="traefik:access"
| eval dur_ms=round(Duration/1000000, 3)
| timechart span=5m perc95(dur_ms) as p95_ms by RouterName
| where p95_ms > 1500
```

Understanding this SPL

**Traefik JSON Access Log Request Duration** — See the description and value fields in this use case JSON.

Documented **Data sources**: `index=web` `sourcetype=traefik:access` JSON access log (`Duration` in nanoseconds). **App/TA**: Add On for Traefik Proxy (Splunkbase app 6733). Rename `index=` / `sourcetype=` to match your deployment.

**Pipeline walkthrough**

• Scope to the documented index and sourcetype, then apply transforms, thresholds, and `timechart`/`stats` as in the SPL above.


Step 3 — Validate
Compare with web server access logs on disk (Apache, NGINX, or W3C) for the same time range, or tail the same sourcetype in Search, to confirm status codes, URIs, and counts.


Step 4 — Operationalize
Add to a dashboard or alert; document ownership. Suggested visuals: Line chart (P95 per router), table (worst services), histogram of durations..

## SPL

```spl
index=web sourcetype="traefik:access"
| eval dur_ms=round(Duration/1000000, 3)
| timechart span=5m perc95(dur_ms) as p95_ms by RouterName
| where p95_ms > 1500
```

## CIM SPL

```spl
| tstats `summariesonly` perc95(Web.duration) as p95_ms avg(Web.duration) as avg_ms
  from datamodel=Web.Web
  by Web.dest Web.uri_path span=5m
| where p95_ms > 1500
```

## Visualization

Line chart (P95 per router), table (worst services), histogram of durations.

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
- [Add On for Traefik Proxy (Splunkbase)](https://splunkbase.splunk.com/app/6733)
- [Traefik — Logs and Access Logs](https://doc.traefik.io/traefik/observability/logs-and-access-logs/)
