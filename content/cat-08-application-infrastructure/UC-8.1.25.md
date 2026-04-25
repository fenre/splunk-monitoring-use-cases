<!-- AUTO-GENERATED from UC-8.1.25.json — DO NOT EDIT -->

---
id: "8.1.25"
title: "WildFly HTTP Access Log Time-Taken Percentiles"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.1.25 · WildFly HTTP Access Log Time-Taken Percentiles

## Description

WildFly serves HTTP through Undertow; access logs with `%D` expose request duration. Rising P95 indicates servlet, EJB, or database contention.

## Value

Isolates slow Java EE traffic independent of generic JVM heap charts.

## Implementation

Configure Undertow `access-log` pattern to include `%D` (microseconds). Normalize to ms in SPL. Split by `virtual-host` if logged.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Undertow access logging + Splunk Universal Forwarder.
• Ensure the following data sources are available: `index=web` `sourcetype=wildfly:access` (Undertow access log with `%D` time).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Turn on Undertow access logs; verify whether `%D` is microseconds and divide by 1000 in `eval` if needed.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=web sourcetype="wildfly:access"
| eval elapsed_ms=coalesce(time_taken, 'time-taken', elapsed)
| where isnotnull(elapsed_ms)
| timechart span=5m perc95(elapsed_ms) as p95_ms by host
| where p95_ms > 2500
```

Understanding this SPL

**WildFly HTTP Access Log Time-Taken Percentiles** — See the description and value fields in this use case JSON.

Documented **Data sources**: `index=web` `sourcetype=wildfly:access` (Undertow access log with `%D` time). **App/TA**: Undertow access logging + Splunk Universal Forwarder. Rename `index=` / `sourcetype=` to match your deployment.

**Pipeline walkthrough**

• Scope to the documented index and sourcetype, then apply transforms, thresholds, and `timechart`/`stats` as in the SPL above.


Step 3 — Validate
Compare with web server access logs on disk (Apache, NGINX, or W3C) for the same time range, or tail the same sourcetype in Search, to confirm status codes, URIs, and counts.


Step 4 — Operationalize
Add to a dashboard or alert; document ownership. Suggested visuals: Line chart (P95), table (host × vhost), compare to datasource pool metrics..

## SPL

```spl
index=web sourcetype="wildfly:access"
| eval elapsed_ms=coalesce(time_taken, 'time-taken', elapsed)
| where isnotnull(elapsed_ms)
| timechart span=5m perc95(elapsed_ms) as p95_ms by host
| where p95_ms > 2500
```

## CIM SPL

```spl
| tstats `summariesonly` perc95(Web.duration) as p95_ms avg(Web.duration) as avg_ms
  from datamodel=Web.Web
  by Web.dest Web.uri_path span=5m
| where p95_ms > 2500
```

## Visualization

Line chart (P95), table (host × vhost), compare to datasource pool metrics.

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
- [WildFly Admin Guide — Access Logging](https://docs.wildfly.org/)
