<!-- AUTO-GENERATED from UC-5.14.11.json — DO NOT EDIT -->

---
id: "5.14.11"
title: "Varnish Thread Pool Queue Length (thread_queue_len)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.11 · Varnish Thread Pool Queue Length (thread_queue_len)

## Description

Queued threads mean requests wait before VCL runs.

## Value

Early warning for thread pool misconfiguration or CPU starvation.

## Implementation

Poll every 30s via scripted input to HEC; flatten counter names per version.

## SPL

```spl
index=proxy sourcetype="varnish:stats"
| eval tql=tonumber(thread_queue_len)
| where tql > 0
| timechart span=1m max(tql) as thread_queue_len by host
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## References

- [Vendor documentation](https://varnish-cache.org/docs/trunk/reference/varnishstat.html)
