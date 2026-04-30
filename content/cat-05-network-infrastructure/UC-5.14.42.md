<!-- AUTO-GENERATED from UC-5.14.42.json — DO NOT EDIT -->

---
id: "5.14.42"
title: "Envoy ext_authz Latency and Denials"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.42 · Envoy ext_authz Latency and Denials

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Security, Performance &middot; **Status:** Draft

*We watch envoy ext_authz latency and denials and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Authz latency becomes user latency on every request.

## Value

Keeps zero-trust gates fast and observable.

## Implementation

Avoid logging tokens; use separate debug index for authz bodies.

## SPL

```spl
index=proxy sourcetype="envoy:access"
| eval dur=tonumber(duration_ms)
| where response_code IN (401,403) OR match(response_flags, "UAEX")
| timechart span=5m perc95(dur) as p95_ms count by cluster_name
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Envoy ext_authz Latency and Denials» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/ext_authz_filter)
