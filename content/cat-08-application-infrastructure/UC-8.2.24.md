<!-- AUTO-GENERATED from UC-8.2.24.json — DO NOT EDIT -->

---
id: "8.2.24"
title: "Traefik Backend Gateway Errors (502–504)"
status: "draft"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.2.24 · Traefik Backend Gateway Errors (502–504)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability, Fault &middot; **Status:** Draft

*We use this to shortens MTTR when ingress shows gateways while Kubernetes events lag.*

---

## Description

502–504 from Traefik indicate unreachable pods, bad TLS to backends, or overloaded upstream sockets.

## Value

Shortens MTTR when ingress shows gateways while Kubernetes events lag.

## Implementation

Ensure `ServiceName` or backend fields exist in JSON logs; alert on sustained counts, not single blips.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: Add On for Traefik Proxy (Splunkbase app 6733).
- Ensure the following data sources are available: `index=web` `sourcetype=traefik:access` `DownstreamStatus`.
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
If `DownstreamStatus` is not extracted, use `spath` or `rex` on JSON `_raw`.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=web sourcetype="traefik:access"
| where DownstreamStatus >= 502 AND DownstreamStatus <= 504
| bin _time span=5m
| stats count by ServiceName, DownstreamStatus, _time
| where count >= 10
```

#### Understanding this SPL

**Traefik Backend Gateway Errors (502–504)** — See the description and value fields in this use case JSON.

Documented **Data sources**: `index=web` `sourcetype=traefik:access` `DownstreamStatus`. **App/TA**: Add On for Traefik Proxy (Splunkbase app 6733). Rename `index=` / `sourcetype=` to match your deployment.

**Pipeline walkthrough**

- Scope to the documented index and sourcetype, then apply transforms, thresholds, and `timechart`/`stats` as in the SPL above.


### Step 3 — Validate
Compare with JBoss, WebLogic, or Tomcat admin consoles, or `catalina` / server logs on the host, for the same window. Confirm hostnames and fields match the vendor UI.


### Step 4 — Operationalize
Add to a dashboard or alert; document ownership. Suggested visuals: Timechart (502–504/min), breakdown by service, geomap if client IP is logged..

## SPL

```spl
index=web sourcetype="traefik:access"
| where DownstreamStatus >= 502 AND DownstreamStatus <= 504
| bin _time span=5m
| stats count by ServiceName, DownstreamStatus, _time
| where count >= 10
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Web.Web
  where Web.status>=500
  by Web.dest Web.uri_path Web.status span=5m
| sort -count
```

## Visualization

Timechart (502–504/min), breakdown by service, geomap if client IP is logged.

## Known False Positives

5xx errors spike during deployment rollouts, restart sequences, or backend service maintenance. Health-check noise and synthetic traffic can add false volume if not filtered.

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
- [Add On for Traefik Proxy (Splunkbase)](https://splunkbase.splunk.com/app/6733)
- [Traefik — Logs and Access Logs](https://doc.traefik.io/traefik/observability/logs-and-access-logs/)
