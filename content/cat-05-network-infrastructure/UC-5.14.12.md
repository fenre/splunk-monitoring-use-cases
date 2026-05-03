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

Operations teams track Varnish LRU eviction rates to detect cache undersizing where the working set exceeds available storage, causing premature object eviction and increased backend load.

## Implementation

Correlate spikes with origin load; revisit storage size and TTL policies.

## Detailed Implementation

### Prerequisites
* Varnish statistics including LRU eviction counters. Key counters: `MAIN.n_lru_nuked` (objects evicted from cache to make room), `MAIN.n_lru_moved` (objects moved on LRU list), `MAIN.n_object` (current object count), `SMA.s0.g_bytes` or `SMF.s0.g_bytes` (storage bytes used). Data in `index=proxy` with `sourcetype=varnish:stats`.
* LRU nuking: when cache storage is full and a new object needs to be stored, Varnish evicts the least-recently-used object. High nuke rate means the cache is too small for the working set. Nuked objects that were still popular will cause cache misses.

### Step 1 — - Configure data collection
Same as UC-5.14.11 (varnishstat collection). Verify:
```spl
index=proxy sourcetype="varnish:stats" earliest=-4h
| spath input=_raw path="MAIN.n_lru_nuked.value" output=nuked
| spath input=_raw path="MAIN.n_object.value" output=objects
| stats latest(nuked) as total_nuked latest(objects) as current_objects
```

### Step 2 — - Create the search and alert

**Primary search -- LRU nuke rate and cache pressure:**
```spl
index=proxy sourcetype="varnish:stats" earliest=-4h
| spath input=_raw path="MAIN.n_lru_nuked.value" output=nuked
| spath input=_raw path="MAIN.n_object.value" output=objects
| spath input=_raw path="SMA.s0.g_bytes.value" output=storage_used
| spath input=_raw path="SMA.s0.g_space.value" output=storage_free
| eval nuked=tonumber(nuked), objects=tonumber(objects), storage_used=tonumber(storage_used), storage_free=tonumber(storage_free)
| eval storage_pct=round(100*storage_used/(storage_used+storage_free), 1)
| bin _time span=5m
| stats latest(nuked) as nuked latest(objects) as objects latest(storage_pct) as storage_pct by _time
| streamstats current=f last(nuked) as prev_nuked
| eval nuke_rate=nuked - prev_nuked
| where isnotnull(nuke_rate)
| eval severity=case(nuke_rate > 1000, "CRITICAL -- >1000 nukes/interval", nuke_rate > 100, "HIGH -- significant eviction rate", storage_pct > 95, "WARNING -- storage >95% full", 1==1, "OK")
| where severity != "OK"
| table _time, objects, storage_pct, nuke_rate, severity
```

### Step 3 — - Validate
(a) `varnishstat -1 | grep -E "n_lru_nuked|n_object|g_bytes|g_space"`.
(b) Reduce storage size temporarily (`-s malloc,100M`) and load test -- nuke rate should spike.
(c) Verify nuke rate correlates with miss rate from UC-5.14.9.

### Step 4 — - Operationalize
Dashboard ("Varnish -- Cache Storage"):
* Row 1 -- Single-value: "Nuke rate (/5m)", "Objects in cache", "Storage utilization".
* Row 2 -- Nuke rate vs miss rate timechart overlay.

Alerting:
* Critical (nuke rate > 1000/5m): cache thrashing -- most objects evicted before reuse.
* Warning (storage > 95%): cache nearly full.

### Step 5 — - Troubleshooting

* **High nuke rate** -- Cache storage is too small for the working set. Options: (1) increase `-s malloc,SIZE`, (2) reduce TTLs on less important objects, (3) use `beresp.uncacheable = true` for objects that are rarely re-requested.

* **Nuke rate spikes at specific times** -- Correlate with traffic patterns or cache purge events. A ban or purge that removes many objects triggers refetch storms.

* **Storage utilization low but nukes happening** -- Check for maximum object count limits. `MAIN.n_objectcore` vs `varnishadm param.show workspace_backend` -- workspace limits can prevent storage of large objects.

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
