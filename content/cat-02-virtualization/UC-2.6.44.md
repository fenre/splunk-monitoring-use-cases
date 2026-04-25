<!-- AUTO-GENERATED from UC-2.6.44.json — DO NOT EDIT -->

---
id: "2.6.44"
title: "VDA Disk IOPS and Write Cache Utilization"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.6.44 · VDA Disk IOPS and Write Cache Utilization

## Description

MCS, image management service I/O optimization, and PVS all rely on local cache volumes. When the write cache fills or RAM cache spills to disk under burst load, users see freezes, logon failures, and even blue screens. Tracking per-host disk read/write IOPS, queue time, and write-cache utilization on session hosts shows capacity and misconfiguration (undersized cache disk, wrong cache mode, storage latency) before user-visible outages. Combine endpoint metrics with PVS or MCS-specific events to explain growth versus a noisy neighbor on shared storage.

## Value

MCS, image management service I/O optimization, and PVS all rely on local cache volumes. When the write cache fills or RAM cache spills to disk under burst load, users see freezes, logon failures, and even blue screens. Tracking per-host disk read/write IOPS, queue time, and write-cache utilization on session hosts shows capacity and misconfiguration (undersized cache disk, wrong cache mode, storage latency) before user-visible outages. Combine endpoint metrics with PVS or MCS-specific events to explain growth versus a noisy neighbor on shared storage.

## Implementation

Deploy uberAgent on session hosts. Confirm `uberAgent:Volume:DiskPerformance` (or the equivalent volume performance sourcetype in your build) lands in `index=uberagent`. Add optional scripted or log collection for VDA and PVS cache messages into `index=xd`. Create rolling baselines per hardware tier. Alert when write-cache use crosses a two-tier threshold (for example, 60% warning, 80% critical) or when IOPS and disk busy time together indicate saturation. Group by host and catalog to find mis-sized machines.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: uberAgent UXM (Splunkbase 1448) on all session hosts; optional forwarder parsing for `citrix:vda:events` and PVS stream metrics.
• Ensure the following data sources are available: `index=uberagent` volume performance; `index=xd` `citrix:vda:events` for cache and MCS messages where collected.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
License uberAgent for disk and volume performance. If field names in your build differ from `ReadIops` / `WriteIops` / `WriteCacheUtilizationPct`, add calculated fields. For PVS-only farms, add `citrix:pvs:stream` as in related use cases and align host naming.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; replace metric field names to match your uberAgent build):

```spl
index=uberagent sourcetype="uberAgent:Volume:DiskPerformance"
| where match(VolumeName, "Cache|WCD|MCS|WriteCache|PVS|Differencing", "i") OR 1=1
| bin _time span=15m
| stats avg(ReadIops) as read_iops, avg(WriteIops) as write_iops, avg(PercentDiskTime) as pct_busy, latest(WriteCacheUtilizationPct) as write_cache_util by host, VolumeName, _time
| where write_cache_util > 80 OR read_iops > 20000 OR write_iops > 15000 OR pct_busy > 85
| table _time, host, VolumeName, read_iops, write_iops, pct_busy, write_cache_util
```

**VDA Disk IOPS and Write Cache Utilization** — The search flags volumes that are hot or nearly full. Tune thresholds to your storage class. Join to catalog or delivery group if you add those fields in uberAgent or a lookup.

Step 3 — Validate
Compare with native OS metrics and hypervisor storage charts for a sample host. Induce a controlled cache write in a lab (large temp files) and confirm utilization climbs in the search.

Step 4 — Operationalize
Publish a dashboard for capacity planning. Open tickets when sustained high IOPS plus high cache use predict exhaustion within the business day. Document remediation: expand cache volume, change cache type, or rebalance virtual machines on storage.


## SPL

```spl
index=uberagent sourcetype="uberAgent:Volume:DiskPerformance"
| where match(VolumeName, "Cache|WCD|MCS|WriteCache|PVS|Differencing", "i") OR 1=1
| bin _time span=15m
| stats avg(ReadIops) as read_iops, avg(WriteIops) as write_iops, avg(PercentDiskTime) as pct_busy, latest(WriteCacheUtilizationPct) as write_cache_util by host, VolumeName, _time
| where write_cache_util > 80 OR read_iops > 20000 OR write_iops > 15000 OR pct_busy > 85
| table _time, host, VolumeName, read_iops, write_iops, pct_busy, write_cache_util
```

## Visualization

Timechart of read/write IOPS and disk busy %, single value for max write-cache use in fleet, table of worst hosts with volume name and cache utilization.

## References

- [uberAgent volume and disk performance](https://docs.uberagent.com/)
- [Cache for MCS — Citrix CVAD](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops-service/manage-deployment/mcs/mcs-storage.html)
