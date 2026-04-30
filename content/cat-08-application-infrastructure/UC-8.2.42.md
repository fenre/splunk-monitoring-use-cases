<!-- AUTO-GENERATED from UC-8.2.42.json — DO NOT EDIT -->

---
id: "8.2.42"
title: "Microsoft IIS HTTP.sys Request Queue Length per Application Pool"
status: "draft"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.2.42 · Microsoft IIS HTTP.sys Request Queue Length per Application Pool

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance, Availability &middot; **Status:** Draft

*We watch for signs that explains latency that application profilers miss and speeds isolation between network, kernel, and code paths.*

---

## Description

HTTP.sys queues requests before IIS worker threads dequeue them. Queue growth often appears before application-level latency and implicates kernel-layer throttling, thread starvation, or SYN floods.

## Value

Explains latency that application profilers miss and speeds isolation between network, kernel, and code paths.

## Implementation

Collect Perfmon every 60s; map `instance` to site/app pool. Alert when queue sustained above baseline.

## SPL

```spl
index=windows sourcetype="Perfmon:IIS" OR sourcetype="perfmon"
| search object="HTTP Service Request Queue" OR counter="CurrentQueueSize"
| eval qsize=tonumber(Value)
| where qsize > 100
| timechart span=1m max(qsize) by instance
```

## Visualization

Stacked bars for status/substatus, Perfmon timecharts, top client tables.

## Known False Positives

Spikes or gaps can follow approved maintenance, load tests, or short collection outages. We add a second signal and a change window before escalating.

## References

- [Microsoft IIS documentation](https://learn.microsoft.com/en-us/windows/win32/http/http-sys-performance-counters)
