<!-- AUTO-GENERATED from UC-5.14.39.json — DO NOT EDIT -->

---
id: "5.14.39"
title: "Envoy HTTP Rate Limit Filter 429 Rate"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.39 · Envoy HTTP Rate Limit Filter 429 Rate

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Security, Performance &middot; **Status:** Draft

*We watch envoy http rate limit filter 429 rate and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

429 spikes indicate abuse or mis-set quotas.

## Value

Balances protection versus legitimate burst traffic.

## Implementation

Ensure xDS pushes consistent descriptors; log external RL service errors separately.

## SPL

```spl
index=proxy sourcetype="envoy:access"
| where response_code==429 OR match(response_flags, "RL")
| stats count by route_name, cluster_name
| sort - count
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Envoy HTTP Rate Limit Filter 429 Rate» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/rate_limit_filter)
