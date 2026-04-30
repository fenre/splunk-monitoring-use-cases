<!-- AUTO-GENERATED from UC-5.14.30.json — DO NOT EDIT -->

---
id: "5.14.30"
title: "Squid Memory Hit vs Disk Hit Distribution"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.30 · Squid Memory Hit vs Disk Hit Distribution

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Status:** Draft

*We watch squid memory hit vs disk hit distribution and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Mis-tuned memory leaves performance on the table.

## Value

Improves latency for hot assets.

## Implementation

Tune `cache_mem` versus disk to shift hot objects to RAM.

## SPL

```spl
index=proxy sourcetype="squid:access"
| eval layer=case(match(code, "TCP_MEM_HIT"),"mem", match(code, "TCP_HIT|TCP_REFRESH_HIT"),"disk", true(), "other")
| bin _time span=15m
| stats count by layer, _time
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Squid Memory Hit vs Disk Hit Distribution» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](http://www.squid-cache.org/Doc/config/cache_mem/)
