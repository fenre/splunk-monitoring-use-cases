<!-- AUTO-GENERATED from UC-5.14.17.json — DO NOT EDIT -->

---
id: "5.14.17"
title: "Varnish Object TTL Distribution Sampling"
status: "draft"
criticality: "low"
splunkPillar: "Observability"
---

# UC-5.14.17 · Varnish Object TTL Distribution Sampling

> **Criticality:** Low &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Analytics, Capacity &middot; **Status:** Draft

*We watch varnish object ttl distribution sampling and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

TTL spread explains hit ratio and origin offload variance.

## Value

Supports data-driven cache policy reviews.

## Implementation

Sample high-volume VSL 1:N to control license cost.

## SPL

```spl
index=proxy sourcetype="varnish:vsl"
| rex field=_raw "TTL:\s+(?<ttl>\d+)"
| where isnotnull(ttl)
| bin ttl span=30
| stats count by ttl
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Varnish Object TTL Distribution Sampling» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://varnish-cache.org/docs/trunk/users-guide/increasing-your-hitrate.html)
