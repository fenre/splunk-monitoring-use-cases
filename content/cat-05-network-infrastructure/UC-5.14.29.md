<!-- AUTO-GENERATED from UC-5.14.29.json — DO NOT EDIT -->

---
id: "5.14.29"
title: "Squid Disk Cache Swap Utilization"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.29 · Squid Disk Cache Swap Utilization

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Capacity &middot; **Status:** Draft

*We watch squid disk cache swap utilization and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Disk full leads to excessive MISS and origin load.

## Value

Preserves browsing quality during traffic spikes.

## Implementation

Poll cachemgr over loopback; alert when swap usage crosses `cache_swap_high`.

## SPL

```spl
index=proxy sourcetype="squid:info"
| regex _raw="(?i)(store_swap_size|Swap capacity|disk cache)"
| rex field=_raw "(?<swap_mb>\d+(?:\.\d+)?)\s*(?:MB|GB)"
| table _time, host, swap_mb
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Squid Disk Cache Swap Utilization» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](http://www.squid-cache.org/Doc/config/cache_dir/)
