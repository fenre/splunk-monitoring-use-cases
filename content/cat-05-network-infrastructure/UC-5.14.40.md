<!-- AUTO-GENERATED from UC-5.14.40.json — DO NOT EDIT -->

---
id: "5.14.40"
title: "Envoy Upstream Connection Pool Overflow"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.14.40 · Envoy Upstream Connection Pool Overflow

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

## References

- [Vendor documentation](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/connection_pooling)
