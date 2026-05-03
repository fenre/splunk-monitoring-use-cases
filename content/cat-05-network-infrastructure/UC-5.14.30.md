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

Operations teams compare Squid memory cache hits vs disk cache hits, optimizing the cache_mem allocation to maximize fast in-memory serving of frequently requested objects.

## Implementation

Tune `cache_mem` versus disk to shift hot objects to RAM.

## Detailed Implementation

### Prerequisites
* Squid statistics for memory vs disk cache. Data from `squidclient mgr:info` forwarded to Splunk. `sourcetype=squid:stats` in `index=proxy`. Key metrics: `mem_hdr_pool`, `mem_pool_allocated`, TCP_MEM_HIT vs TCP_HIT vs TCP_DISK_HIT in access log.
* Memory cache (`cache_mem`): hot objects stored in RAM for fastest access. Disk cache (`cache_dir`): larger capacity but slower. Ideal: frequently requested objects in memory, less popular objects on disk. `cache_mem` sets max in-memory cache size (default 256 MB).

### Step 1 — - Configure data collection
```
# squid.conf
cache_mem 512 MB
maximum_object_size_in_memory 1 MB
```
Verify:
```spl
index=proxy sourcetype="squid:access" earliest=-4h
| eval hit_type=case(match(squid_request_status, "TCP_MEM_HIT"), "MEMORY", match(squid_request_status, "TCP_HIT|TCP_DISK_HIT"), "DISK", 1==1, null())
| where isnotnull(hit_type)
| stats count by hit_type
```

### Step 2 — - Create the search and alert

**Primary search -- Memory vs disk hit distribution:**
```spl
index=proxy sourcetype="squid:access" earliest=-4h
| eval hit_type=case(match(squid_request_status, "TCP_MEM_HIT"), "MEMORY_HIT", match(squid_request_status, "TCP_HIT"), "DISK_HIT", match(squid_request_status, "TCP_MISS"), "MISS", 1==1, null())
| where isnotnull(hit_type)
| bin _time span=15m
| stats count(eval(hit_type="MEMORY_HIT")) as mem_hits count(eval(hit_type="DISK_HIT")) as disk_hits count(eval(hit_type="MISS")) as misses count as total by _time
| eval mem_hit_pct=round(100*mem_hits/(mem_hits+disk_hits+misses), 2)
| eval disk_hit_pct=round(100*disk_hits/(mem_hits+disk_hits+misses), 2)
| eval total_hit_pct=round(100*(mem_hits+disk_hits)/(mem_hits+disk_hits+misses), 2)
| table _time, total, mem_hits, mem_hit_pct, disk_hits, disk_hit_pct, misses, total_hit_pct
```

### Step 3 — - Validate
(a) `squidclient mgr:info | grep -i "memory"` -- shows memory usage.
(b) Request a small object twice rapidly -- second request should be TCP_MEM_HIT.
(c) Compare: `squidclient mgr:mem` for detailed memory pool stats.

### Step 4 — - Operationalize
Dashboard ("Squid -- Cache Tier Distribution"):
* Row 1 -- Single-value: "Memory hit %", "Disk hit %", "Total hit %".
* Row 2 -- Hit distribution timechart.

### Step 5 — - Troubleshooting

* **Low memory hit ratio** -- `cache_mem` may be too small for the working set. Increase if RAM is available. Also check `maximum_object_size_in_memory` -- if too small, popular objects don't fit in memory.

* **No memory hits at all** -- Verify `cache_mem` is > 0 and the directive is active. Default is 256 MB. Also check `memory_replacement_policy` (lru is default, heap GDSF is recommended for web traffic).

* **Memory cache thrashing** -- Too many objects competing for limited memory. Tune `memory_replacement_policy heap GDSF` to favor small, frequently requested objects.

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
