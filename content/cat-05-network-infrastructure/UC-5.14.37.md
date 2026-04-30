<!-- AUTO-GENERATED from UC-5.14.37.json — DO NOT EDIT -->

---
id: "5.14.37"
title: "Envoy Outlier Detection Ejection Events"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.37 · Envoy Outlier Detection Ejection Events

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Resilience, Performance &middot; **Status:** Draft

*We watch envoy outlier detection ejection events and catch issues early, before they turn into outages for the people who rely on the network.*

---

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

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Envoy Outlier Detection Ejection Events» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/outlier)
