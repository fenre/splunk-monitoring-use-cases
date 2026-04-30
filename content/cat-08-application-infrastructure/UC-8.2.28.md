<!-- AUTO-GENERATED from UC-8.2.28.json — DO NOT EDIT -->

---
id: "8.2.28"
title: "Varnish Worker Thread Allocation Failures"
status: "draft"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.2.28 · Varnish Worker Thread Allocation Failures

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Availability &middot; **Status:** Draft

*We watch for signs that early warning before requests are dropped without obvious backend errors.*

---

## Description

`n_wrk_failed` counts times Varnish could not create a worker thread—often during overload or OS resource limits.

## Value

Early warning before requests are dropped without obvious backend errors.

## Implementation

Poll frequently; investigate with `varnishlog` tagged `Error` on the host when deltas appear.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: Custom scripted input (`varnishstat -j`).
- Ensure the following data sources are available: `index=cache` `sourcetype=varnish:stats` (`MAIN.n_wrk_failed` / `n_wrk_failed`).
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
Confirm counter name in your JSON (`MAIN.n_wrk_failed`).

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cache sourcetype="varnish:stats"
| sort 0 _time
| delta n_wrk_failed as fail_delta
| where fail_delta > 0
| table _time, host, n_wrk_failed, fail_delta
```

#### Understanding this SPL

**Varnish Worker Thread Allocation Failures** — See the description and value fields in this use case JSON.

Documented **Data sources**: `index=cache` `sourcetype=varnish:stats` (`MAIN.n_wrk_failed` / `n_wrk_failed`). **App/TA**: Custom scripted input (`varnishstat -j`). Rename `index=` / `sourcetype=` to match your deployment.

**Pipeline walkthrough**

- Scope to the documented index and sourcetype, then apply transforms, thresholds, and `timechart`/`stats` as in the SPL above.

### Step 3 — Validate
Compare with JBoss, WebLogic, or Tomcat admin consoles, or `catalina` / server logs on the host, for the same window. Confirm hostnames and fields match the vendor UI.


### Step 4 — Operationalize
Add to a dashboard or alert; document ownership. Suggested visuals: Single value (failures/hour), timeline, host matrix..

## SPL

```spl
index=cache sourcetype="varnish:stats"
| sort 0 _time
| delta n_wrk_failed as fail_delta
| where fail_delta > 0
| table _time, host, n_wrk_failed, fail_delta
```

## Visualization

Single value (failures/hour), timeline, host matrix.

## Known False Positives

Spikes or gaps can follow approved maintenance, load tests, or short collection outages. We add a second signal and a change window before escalating.

## References

- [varnishstat — Varnish reference](https://varnish-cache.org/docs/trunk/reference/varnishstat.html)
