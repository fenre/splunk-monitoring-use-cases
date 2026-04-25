<!-- AUTO-GENERATED from UC-8.1.27.json — DO NOT EDIT -->

---
id: "8.1.27"
title: "IIS W3C Time-Taken Latency Percentiles"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.1.27 · IIS W3C Time-Taken Latency Percentiles

## Description

The W3C `time-taken` field is the authoritative IIS request duration. P95 by site highlights slow apps, ARR backends, or cold .NET startup.

## Value

Surfaces latency regressions that status-code-only dashboards miss.

## Implementation

Enable `time-taken` in IIS logging; use `ms:iis:auto`. Exclude static content if needed via `cs-uri-stem` filters.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for Microsoft IIS (Splunkbase app 3185).
• Ensure the following data sources are available: `index=web` `sourcetype=ms:iis:auto` with `time-taken` field (milliseconds).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Confirm `time-taken` is enabled in the IIS logging field list.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=web sourcetype="ms:iis:auto"
| eval tt=coalesce('time-taken', time_taken)
| where isnotnull(tt) AND tt>=0
| timechart span=5m perc95(tt) as p95_ms by s_sitename
| where p95_ms > 3000
```

Understanding this SPL

**IIS W3C Time-Taken Latency Percentiles** — See the description and value fields in this use case JSON.

Documented **Data sources**: `index=web` `sourcetype=ms:iis:auto` with `time-taken` field (milliseconds). **App/TA**: Splunk Add-on for Microsoft IIS (Splunkbase app 3185). Rename `index=` / `sourcetype=` to match your deployment.

**Pipeline walkthrough**

• Scope to the documented index and sourcetype, then apply transforms, thresholds, and `timechart`/`stats` as in the SPL above.


Step 3 — Validate
Compare a sample of alert results to IIS W3C extended logs on the server (or a one-off export of the same file) and, when applicable, the IIS Manager site. Confirm `sc-status`, time-taken, and URI fields match what you expect.


Step 4 — Operationalize
Add to a dashboard or alert; document ownership. Suggested visuals: Line chart (P95 per site), table (top URIs using separate drilldown search), compare to app pool recycle windows..

## SPL

```spl
index=web sourcetype="ms:iis:auto"
| eval tt=coalesce('time-taken', time_taken)
| where isnotnull(tt) AND tt>=0
| timechart span=5m perc95(tt) as p95_ms by s_sitename
| where p95_ms > 3000
```

## CIM SPL

```spl
| tstats `summariesonly` perc95(Web.duration) as p95_ms avg(Web.duration) as avg_ms
  from datamodel=Web.Web
  by Web.dest Web.uri_path span=5m
| where p95_ms > 3000
```

## Visualization

Line chart (P95 per site), table (top URIs using separate drilldown search), compare to app pool recycle windows.

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
- [Splunk Add-on for Microsoft IIS (Splunkbase)](https://splunkbase.splunk.com/app/3185)
