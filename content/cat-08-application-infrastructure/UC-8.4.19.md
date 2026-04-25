<!-- AUTO-GENERATED from UC-8.4.19.json — DO NOT EDIT -->

---
id: "8.4.19"
title: "Traefik Per-Service Request Rate for Capacity Planning"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.4.19 · Traefik Per-Service Request Rate for Capacity Planning

## Description

Hourly request volume by `ServiceName` reveals which backends need horizontal scaling before CPU limits hit.

## Value

Supports FinOps and ingress capacity reviews.

## Implementation

Ensure `ServiceName` is populated; fall back to `RouterName` if null.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Add On for Traefik Proxy (Splunkbase app 6733).
• Ensure the following data sources are available: `index=web` `sourcetype=traefik:access`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Tune multipliers for seasonal businesses.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=web sourcetype="traefik:access"
| bin _time span=1h
| stats count as rph by ServiceName, _time
| eventstats avg(rph) as baseline by ServiceName
| where rph > baseline * 1.5 AND rph > 1000
```

Understanding this SPL

**Traefik Per-Service Request Rate for Capacity Planning** — See the description and value fields in this use case JSON.

Documented **Data sources**: `index=web` `sourcetype=traefik:access`. **App/TA**: Add On for Traefik Proxy (Splunkbase app 6733). Rename `index=` / `sourcetype=` to match your deployment.

**Pipeline walkthrough**

• Scope to the documented index and sourcetype, then apply transforms, thresholds, and `timechart`/`stats` as in the SPL above.


Step 3 — Validate
Compare with the API gateway or mesh admin (Kong, Apigee, AWS API Gateway, etc.) and a raw log tail for the same time range.


Step 4 — Operationalize
Add to a dashboard or alert; document ownership. Suggested visuals: Line chart (RPH), baseline overlay, table (growth %)..

## SPL

```spl
index=web sourcetype="traefik:access"
| bin _time span=1h
| stats count as rph by ServiceName, _time
| eventstats avg(rph) as baseline by ServiceName
| where rph > baseline * 1.5 AND rph > 1000
```

## CIM SPL

```spl
| tstats `summariesonly` count as events
  from datamodel=Web.Web
  by Web.http_method Web.dest span=1d
| sort -events
```

## Visualization

Line chart (RPH), baseline overlay, table (growth %).

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
- [Add On for Traefik Proxy (Splunkbase)](https://splunkbase.splunk.com/app/6733)
