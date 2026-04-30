<!-- AUTO-GENERATED from UC-5.14.36.json — DO NOT EDIT -->

---
id: "5.14.36"
title: "Envoy Circuit Breaker Open Events by Cluster"
status: "draft"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.14.36 · Envoy Circuit Breaker Open Events by Cluster

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Resilience, Availability &middot; **Status:** Draft

*We watch envoy circuit breaker open events by cluster and catch issues early, before they turn into outages for the people who rely on the network.*

---

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

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Envoy Circuit Breaker Open Events by Cluster» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://www.envoyproxy.io/docs/envoy/latest/configuration/upstream/cluster_manager/cluster_circuit_breakers)
