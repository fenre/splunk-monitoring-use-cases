<!-- AUTO-GENERATED from UC-5.14.41.json — DO NOT EDIT -->

---
id: "5.14.41"
title: "Envoy Active Health Check Failure Spike"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.41 · Envoy Active Health Check Failure Spike

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Availability &middot; **Status:** Draft

*We watch envoy active health check failure spike and catch issues early, before they turn into outages for the people who rely on the network.*

---

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

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Envoy Active Health Check Failure Spike» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/health_checking)
