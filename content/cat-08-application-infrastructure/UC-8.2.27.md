<!-- AUTO-GENERATED from UC-8.2.27.json — DO NOT EDIT -->

---
id: "8.2.27"
title: "Memcached listen_disabled_num Connection Overruns"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.2.27 · Memcached listen_disabled_num Connection Overruns

## Description

`listen_disabled_num` increments when connections are dropped because the listen backlog is full—clients experience timeouts.

## Value

Surfaces network or application storms exceeding Memcached accept capacity.

## Implementation

Alert on positive deltas; compare with `accepting_conns` and `curr_connections`. Scale out or raise backlog carefully with OS tuning.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (`stats`).
• Ensure the following data sources are available: `index=cache` `sourcetype=memcached:stats` (`listen_disabled_num`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Field must be extracted as numeric; some templates prefix `STAT`.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cache sourcetype="memcached:stats"
| sort 0 _time
| delta listen_disabled_num as ldd_delta
| where ldd_delta > 0
| table _time, host, listen_disabled_num, ldd_delta
```

Understanding this SPL

**Memcached listen_disabled_num Connection Overruns** — See the description and value fields in this use case JSON.

Documented **Data sources**: `index=cache` `sourcetype=memcached:stats` (`listen_disabled_num`). **App/TA**: Custom scripted input (`stats`). Rename `index=` / `sourcetype=` to match your deployment.

**Pipeline walkthrough**

• Scope to the documented index and sourcetype, then apply transforms, thresholds, and `timechart`/`stats` as in the SPL above.

Step 3 — Validate
Compare with JBoss, WebLogic, or Tomcat admin consoles, or `catalina` / server logs on the host, for the same window. Confirm hostnames and fields match the vendor UI.


Step 4 — Operationalize
Add to a dashboard or alert; document ownership. Suggested visuals: Line chart (counter), alert feed (delta>0), correlation with app deploys..

## SPL

```spl
index=cache sourcetype="memcached:stats"
| sort 0 _time
| delta listen_disabled_num as ldd_delta
| where ldd_delta > 0
| table _time, host, listen_disabled_num, ldd_delta
```

## Visualization

Line chart (counter), alert feed (delta>0), correlation with app deploys.

## References

- [Memcached protocol — Statistics](https://github.com/memcached/memcached/blob/master/doc/protocol.txt)
