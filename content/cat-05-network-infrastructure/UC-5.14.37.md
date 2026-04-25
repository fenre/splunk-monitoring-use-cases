<!-- AUTO-GENERATED from UC-5.14.37.json — DO NOT EDIT -->

---
id: "5.14.37"
title: "Envoy Outlier Detection Ejection Events"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.37 · Envoy Outlier Detection Ejection Events

## Description

Ejections explain uneven load and surprise latency.

## Value

Speeds kube workload investigations.

## Implementation

Tune outlier `consecutive_5xx`; confirm with periodic `/clusters` admin dumps (low volume).

## SPL

```spl
index=proxy sourcetype="envoy:access"
| where match(response_flags, "UH") OR match(response_flags, "UF") OR match(_raw, "(?i)eject")
| stats count by upstream_host, cluster_name
| where count > 5
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## References

- [Vendor documentation](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/outlier)
