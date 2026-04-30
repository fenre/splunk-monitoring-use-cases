<!-- AUTO-GENERATED from UC-5.14.12.json — DO NOT EDIT -->

---
id: "5.14.12"
title: "Varnish LRU Nuked Objects Rate"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.12 · Varnish LRU Nuked Objects Rate

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Capacity &middot; **Status:** Draft

*We watch varnish lru nuked objects rate and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Rising nukes predict hit ratio collapse and origin storms.

## Value

Informs malloc/file storage sizing decisions.

## Implementation

Correlate spikes with origin load; revisit storage size and TTL policies.

## SPL

```spl
index=proxy sourcetype="varnish:stats"
| eval nuked=tonumber(n_lru_nuked)
| sort 0 host _time
| streamstats window=2 global=f last(nuked) as p_n by host
| eval d=nuked-p_n
| timechart span=5m sum(d) as lru_nukes by host
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Varnish LRU Nuked Objects Rate» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://varnish-cache.org/docs/trunk/users-guide/storage-backends.html)
