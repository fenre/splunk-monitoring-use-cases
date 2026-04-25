<!-- AUTO-GENERATED from UC-5.14.41.json — DO NOT EDIT -->

---
id: "5.14.41"
title: "Envoy Active Health Check Failure Spike"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.41 · Envoy Active Health Check Failure Spike

## Description

Failing checks drain endpoints before user monitors react.

## Value

Aligns platform and service owner visibility.

## Implementation

Correlate with Kubernetes pod restart metrics and upstream deploys.

## SPL

```spl
index=proxy sourcetype="envoy:stats"
| search metric_name="*health_check*failure*" OR metric_name="*health_check*network_failure*"
| eval v=tonumber(metric_value)
| where v > 0
| timechart span=1m sum(v) by cluster_name
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## References

- [Vendor documentation](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/health_checking)
