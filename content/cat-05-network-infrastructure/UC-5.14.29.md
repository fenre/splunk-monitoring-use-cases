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

Operations teams monitor Squid disk cache (swap) utilization against configured high/low watermarks, detecting when the cache directory approaches capacity and triggers object purging.

## Implementation

Poll cachemgr over loopback; alert when swap usage crosses `cache_swap_high`.

## Detailed Implementation

### Prerequisites
* Squid cache manager statistics for disk cache (swap). Data from `squidclient mgr:storedir` or `squidclient mgr:info` forwarded to Splunk. `sourcetype=squid:cache` or `sourcetype=squid:stats` in `index=proxy`. Key metrics: swap size (total/used), object count, swap-in/swap-out rates.
* Squid disk cache: configured with `cache_dir ufs /var/spool/squid 10000 16 256` (10GB, 16 L1 dirs, 256 L2 dirs). When disk cache fills to `cache_swap_high` watermark (default 95%), Squid starts purging until `cache_swap_low` (default 90%). If swap fills completely, no new objects can be cached to disk.

### Step 1 — - Configure data collection
Scripted input for cache stats:
```bash
#!/bin/bash
# /opt/splunk/etc/apps/TA-squid/bin/squid_storedir.sh
squidclient mgr:storedir 2>/dev/null
```
```
# inputs.conf
[script:///opt/splunk/etc/apps/TA-squid/bin/squid_storedir.sh]
interval = 300
sourcetype = squid:storedir
index = proxy
```
Verify:
```spl
index=proxy sourcetype="squid:storedir" earliest=-4h
| head 5
```

### Step 2 — - Create the search and alert

**Primary search -- Disk cache utilization:**
```spl
index=proxy (sourcetype="squid:storedir" OR sourcetype="squid:cache") earliest=-4h
| where match(_raw, "(?i)store.dir|swap.size|cache.dir|store.entries")
| rex "Swap size:\s+(?<swap_used_kb>\d+)\s+KB"
| rex "Maximum\s+Swap\s+Size:\s+(?<swap_max_kb>\d+)\s+KB"
| rex "store entries:\s+(?<object_count>\d+)"
| eval swap_used_gb=round(tonumber(swap_used_kb)/1048576, 2)
| eval swap_max_gb=round(tonumber(swap_max_kb)/1048576, 2)
| eval swap_pct=round(100*tonumber(swap_used_kb)/tonumber(swap_max_kb), 1)
| bin _time span=15m
| stats latest(swap_used_gb) as used_gb latest(swap_max_gb) as max_gb latest(swap_pct) as utilization_pct latest(object_count) as objects by _time
| eval severity=case(utilization_pct > 95, "CRITICAL -- swap nearly full (".utilization_pct."%)", utilization_pct > 85, "WARNING -- swap filling (".utilization_pct."%)", 1==1, "OK")
| where severity != "OK"
| table _time, used_gb, max_gb, utilization_pct, objects, severity
```

### Step 3 — - Validate
(a) `squidclient mgr:storedir` -- shows per-directory usage.
(b) `du -sh /var/spool/squid` -- verify disk usage matches Squid's reported swap size.
(c) Check thresholds: `squidclient mgr:info | grep -i swap`.

### Step 4 — - Operationalize
Dashboard ("Squid -- Disk Cache"):
* Row 1 -- Single-value: "Swap utilization (%)", "Used (GB)", "Max (GB)", "Objects".
* Row 2 -- Utilization timechart.

Alerting:
* Critical (swap > 95%): cache_swap_high reached, purging active.
* Warning (swap > 85%): approaching high watermark.

### Step 5 — - Troubleshooting

* **Swap at 95% constantly** -- Working set exceeds configured `cache_dir` size. Options: (1) increase `cache_dir` size, (2) reduce `maximum_object_size` to exclude large objects, (3) add additional `cache_dir` entries on different disks.

* **Swap I/O causing latency** -- `aufs` or `rock` cache types are faster than default `ufs` for high I/O workloads. Consider SSD storage for cache directory.

* **Objects count very high but utilization low** -- Many small objects. This is normal for web proxy workloads but can cause inode exhaustion. Check: `df -i /var/spool/squid`.

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
