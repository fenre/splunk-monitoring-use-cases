<!-- AUTO-GENERATED from UC-8.4.20.json — DO NOT EDIT -->

---
id: "8.4.20"
title: "Memcached Connection Count Versus maxconn"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.4.20 · Memcached Connection Count Versus maxconn

## Description

Approaching `max_connections` risks refused sockets even when memory is healthy.

## Value

Prevents connection storms from taking down shared caches.

## Implementation

Some builds omit `max_connections`—derive from config via lookup if needed.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input.
• Ensure the following data sources are available: `index=cache` `sourcetype=memcached:stats` (`curr_connections`, `max_connections`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Confirm `STAT curr_connections` maps to numeric fields.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cache sourcetype="memcached:stats"
| eval conn_pct=if(max_connections>0, round(100*curr_connections/max_connections,1), null())
| where conn_pct > 80
| timechart span=5m max(conn_pct) as used_pct by host
```

Understanding this SPL

**Memcached Connection Count Versus maxconn** — See the description and value fields in this use case JSON.

Documented **Data sources**: `index=cache` `sourcetype=memcached:stats` (`curr_connections`, `max_connections`). **App/TA**: Custom scripted input. Rename `index=` / `sourcetype=` to match your deployment.

**Pipeline walkthrough**

• Scope to the documented index and sourcetype, then apply transforms, thresholds, and `timechart`/`stats` as in the SPL above.

Step 3 — Validate
Compare with the API gateway or mesh admin (Kong, Apigee, AWS API Gateway, etc.) and a raw log tail for the same time range.


Step 4 — Operationalize
Add to a dashboard or alert; document ownership. Suggested visuals: Gauge, line chart, alert when >80% for 15m..

## SPL

```spl
index=cache sourcetype="memcached:stats"
| eval conn_pct=if(max_connections>0, round(100*curr_connections/max_connections,1), null())
| where conn_pct > 80
| timechart span=5m max(conn_pct) as used_pct by host
```

## Visualization

Gauge, line chart, alert when >80% for 15m.

## References

- [Memcached protocol — Statistics](https://github.com/memcached/memcached/blob/master/doc/protocol.txt)
