<!-- AUTO-GENERATED from UC-5.14.10.json — DO NOT EDIT -->

---
id: "5.14.10"
title: "Varnish Backend Health Probe and Fetch Failures"
status: "draft"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.14.10 · Varnish Backend Health Probe and Fetch Failures

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability &middot; **Status:** Draft

*We watch varnish backend health probe and fetch failures and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Probe failures starve users even when edge CPUs look idle.

## Value

Triggers fast failover or capacity before SLAs breach.

## Implementation

Enable backend polling; include `Backend` VSL tags in forwarded logs.

## SPL

```spl
index=proxy sourcetype="varnish:vsl"
| regex _raw="(?i)(Backend fetch failed|FetchError|no healthy backend)"
| stats count by backend
| sort - count
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Varnish Backend Health Probe and Fetch Failures» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://varnish-cache.org/docs/trunk/reference/vcl-backend-health.html)
