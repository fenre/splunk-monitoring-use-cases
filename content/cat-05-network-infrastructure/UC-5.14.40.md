<!-- AUTO-GENERATED from UC-5.14.40.json — DO NOT EDIT -->

---
id: "5.14.40"
title: "Envoy Upstream Connection Pool Overflow"
status: "draft"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.14.40 · Envoy Upstream Connection Pool Overflow

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Availability, Capacity &middot; **Status:** Draft

*We watch envoy upstream connection pool overflow and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Pool overflow produces 503s without obvious CPU load.

## Value

Prevents mesh-wide retry storms.

## Implementation

Increase `max_connections` and `max_pending_requests` carefully; verify upstream capacity.

## SPL

```spl
index=proxy sourcetype="envoy:stats"
| search metric_name="*overflow*" OR metric_name="*pending_requests*"
| eval v=tonumber(metric_value)
| where v > 0
| timechart span=1m sum(v) by cluster_name
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Envoy Upstream Connection Pool Overflow» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/connection_pooling)
