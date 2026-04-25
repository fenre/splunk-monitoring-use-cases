<!-- AUTO-GENERATED from UC-5.14.36.json — DO NOT EDIT -->

---
id: "5.14.36"
title: "Envoy Circuit Breaker Open Events by Cluster"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.14.36 · Envoy Circuit Breaker Open Events by Cluster

## Description

Open breakers shed load but indicate real upstream pain.

## Value

Prioritizes which service mesh cluster needs attention.

## Implementation

Scrape via OpenTelemetry Collector or Telegraf; normalize `cluster_name` label.

## SPL

```spl
index=proxy sourcetype="envoy:stats"
| search metric_name="*circuit_breakers*open*" OR metric_name="*cx_open*"
| eval v=tonumber(metric_value)
| where v > 0
| timechart span=1m max(v) by cluster_name
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## References

- [Vendor documentation](https://www.envoyproxy.io/docs/envoy/latest/configuration/upstream/cluster_manager/cluster_circuit_breakers)
