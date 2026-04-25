<!-- AUTO-GENERATED from UC-8.7.7.json — DO NOT EDIT -->

---
id: "8.7.7"
title: "IIS Client Error Status Trending for Service Review"
criticality: "low"
splunkPillar: "IT Operations"
---

# UC-8.7.7 · IIS Client Error Status Trending for Service Review

## Description

4xx trends highlight broken deep links, API contract drift, and auth misconfigurations during audits of customer-facing portals.

## Value

Supports service owners reviewing quality alongside security teams.

## Implementation

Exclude health-probe URIs via lookup.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for Microsoft IIS.
• Ensure the following data sources are available: `index=web` `sourcetype=ms:iis:auto` (`sc-status` 4xx).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Pair with marketing campaign calendar to explain spikes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=web sourcetype="ms:iis:auto" earliest=-30d
| where sc_status >= 400 AND sc_status < 500
| timechart span=1d count by sc_status
```

Understanding this SPL

**IIS Client Error Status Trending for Service Review** — See the description and value fields in this use case JSON.

Documented **Data sources**: `index=web` `sourcetype=ms:iis:auto` (`sc-status` 4xx). **App/TA**: Splunk Add-on for Microsoft IIS. Rename `index=` / `sourcetype=` to match your deployment.

**Pipeline walkthrough**

• Scope to the documented index and sourcetype, then apply transforms, thresholds, and `timechart`/`stats` as in the SPL above.


Step 3 — Validate
Compare with the application or platform source of truth (logs, UI, or metrics) for the same time range, and with known change or maintenance windows.


Step 4 — Operationalize
Add to a dashboard or alert; document ownership. Suggested visuals: Stacked area (codes), executive summary panel..

## SPL

```spl
index=web sourcetype="ms:iis:auto" earliest=-30d
| where sc_status >= 400 AND sc_status < 500
| timechart span=1d count by sc_status
```

## CIM SPL

```spl
| tstats `summariesonly` count as events
  from datamodel=Web.Web
  by Web.http_method Web.dest span=5m
| sort -events
```

## Visualization

Stacked area (codes), executive summary panel.

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
- [Splunk Add-on for Microsoft IIS (Splunkbase)](https://splunkbase.splunk.com/app/3185)
