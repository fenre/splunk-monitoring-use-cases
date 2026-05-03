<!-- AUTO-GENERATED from UC-5.14.19.json — DO NOT EDIT -->

---
id: "5.14.19"
title: "Varnish SMA Allocator Free Ratio Watch"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.19 · Varnish SMA Allocator Free Ratio Watch

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Capacity &middot; **Status:** Draft

*We watch varnish sma allocator free ratio watch and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Fragmentation silently shrinks effective cache space.

## Value

Operations teams track Varnish SMA memory allocator free ratio and allocation failures, detecting cache storage exhaustion that prevents new objects from being cached.

## Implementation

Map counter names per version; plan storage migration if chronic fragmentation.

## Detailed Implementation

### Prerequisites
* Varnish statistics for SMA (malloc) storage allocator. Key counters: `SMA.s0.g_bytes` (bytes used), `SMA.s0.g_space` (bytes free), `SMA.s0.g_alloc` (allocations), `SMA.s0.c_fail` (allocation failures). Data in `index=proxy` with `sourcetype=varnish:stats`.
* SMA is the default memory allocator (`-s malloc,SIZE`). When free space approaches zero, new objects can't be cached and LRU nuking increases. `c_fail > 0` means memory allocation failed -- Varnish couldn't cache the object.

### Step 1 — - Configure data collection
Same as UC-5.14.11. Verify:
```spl
index=proxy sourcetype="varnish:stats" earliest=-4h
| spath input=_raw path="SMA.s0.g_bytes.value" output=used
| spath input=_raw path="SMA.s0.g_space.value" output=free
| stats latest(used) as used latest(free) as free
| eval pct_used=round(100*used/(used+free), 1)
```

### Step 2 — - Create the search and alert

**Primary search -- SMA free ratio and allocation failures:**
```spl
index=proxy sourcetype="varnish:stats" earliest=-4h
| spath input=_raw path="SMA.s0.g_bytes.value" output=used_bytes
| spath input=_raw path="SMA.s0.g_space.value" output=free_bytes
| spath input=_raw path="SMA.s0.c_fail.value" output=alloc_fails
| eval used=tonumber(used_bytes), free=tonumber(free_bytes), fails=tonumber(alloc_fails)
| eval total=used + free
| eval free_pct=round(100*free/total, 1)
| eval used_gb=round(used/1073741824, 2)
| eval free_gb=round(free/1073741824, 2)
| bin _time span=5m
| stats latest(free_pct) as free_pct latest(used_gb) as used_gb latest(free_gb) as free_gb latest(fails) as alloc_fails by _time
| streamstats current=f last(alloc_fails) as prev_fails
| eval new_fails=alloc_fails - prev_fails
| eval severity=case(new_fails > 0, "CRITICAL -- allocation failures", free_pct < 5, "CRITICAL -- <5% free", free_pct < 15, "WARNING -- <15% free", 1==1, "OK")
| where severity != "OK"
| table _time, used_gb, free_gb, free_pct, new_fails, severity
```

### Step 3 — - Validate
(a) `varnishstat -1 | grep SMA`.
(b) Check configured storage: startup parameters include `-s malloc,2G` or similar.
(c) Correlate with LRU nuke rate (UC-5.14.12) -- both should increase as storage fills.

### Step 4 — - Operationalize
Dashboard ("Varnish -- Storage Allocator"):
* Row 1 -- Single-value: "Free %", "Used (GB)", "Allocation failures".
* Row 2 -- Storage utilization timechart.

Alerting:
* Critical (allocation failures or free < 5%): cache is effectively full.
* Warning (free < 15%): approaching capacity.

### Step 5 — - Troubleshooting

* **Free ratio dropping** -- Working set is growing. Options: (1) increase `-s malloc,SIZE` at startup, (2) reduce object TTLs to expire objects faster, (3) exclude large objects from caching.

* **Allocation failures but free space exists** -- The free space may be fragmented. Malloc can't find a contiguous block large enough. Consider restarting Varnish to defragment.

* **Should I use SMA or SMF (file)?** -- SMA (malloc) is faster but limited to available RAM. SMF (file) uses disk but is slower. Use SMA for primary cache, SMF for large-object overflow if needed.

## SPL

```spl
index=proxy sourcetype="varnish:stats"
| eval alloc=tonumber(sma_bytes_allocated), free=tonumber(sma_bytes_free)
| eval free_pct=if((alloc+free)>0, round(100*free/(alloc+free),1), null())
| where free_pct > 40
| table host, alloc, free, free_pct
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Varnish SMA Allocator Free Ratio Watch» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://varnish-cache.org/docs/trunk/users-guide/storage-backends.html)
