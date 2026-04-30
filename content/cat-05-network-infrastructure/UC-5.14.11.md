<!-- AUTO-GENERATED from UC-5.14.11.json — DO NOT EDIT -->

---
id: "5.14.11"
title: "Varnish Thread Pool Queue Length (thread_queue_len)"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.11 · Varnish Thread Pool Queue Length (thread_queue_len)

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Status:** Draft

*We watch varnish thread pool queue length (thread_queue_len) and catch issues early, before they turn into outages for the people who rely on the network.*

---

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

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Varnish Thread Pool Queue Length (thread_queue_len)» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://varnish-cache.org/docs/trunk/reference/varnishstat.html)
