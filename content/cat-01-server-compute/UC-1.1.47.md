<!-- AUTO-GENERATED from UC-1.1.47.json — DO NOT EDIT -->

---
id: "1.1.47"
title: "Page Cache Pressure and Reclaim Activity"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.47 · Page Cache Pressure and Reclaim Activity

## Description

Flags hosts where the kernel is spending a high share of direct reclaim scans on successful steals, a sign the system is under real memory pressure and stealing pages from the page cache aggressively.

## Value

Spotting reclaim-heavy periods early helps you add RAM, tune workloads, or fix leaks before latency spreads to databases, batch jobs, and user-facing services on the same box.

## Implementation

Ship time-delta’d `/proc/vmstat` metrics as `pgscan_direct` and `pgsteal_direct`. Alert when the ratio of steals to scans stays above 0.7 for the analysis window, indicating the host is doing heavy direct reclaim.

## Detailed Implementation

Prerequisites
• Install `Splunk_TA_nix` and add a scripted input (or an extension) that records `/proc/vmstat` on an interval and emits **delta** values for `pgscan_direct` and `pgsteal_direct` or absolute counters your SPL differences correctly.
• Ensure the fields used in the search exist in the chosen sourcetype.
• See docs/implementation-guide.md for inputs.conf layout.

Step 1 — Configure data collection
Parse `/proc/vmstat` on a fixed schedule; compute per-interval deltas in the script or in SPL before this alert. Point events at `index=os` and your agreed sourcetype (here `custom:meminfo_delta`).

Step 2 — Create the search and alert

```spl
index=os sourcetype=custom:meminfo_delta host=*
| stats avg(pgscan_direct) as scan_avg, avg(pgsteal_direct) as steal_avg by host
| eval steal_ratio=if(scan_avg>0, steal_avg/scan_avg, null())
| where steal_ratio > 0.7
```

**Understanding this SPL** — Averages the delta rates per host, forms `steal_ratio`, and flags hosts where a large share of direct scans result in a steal, which is typical of memory pressure. Add `scan_avg>0` in the `where` if you want to drop idle hosts.


Step 3 — Validate
On the host, run `vmstat 1` and watch `si`/`so` and overall memory behavior; use `cat /proc/vmstat | egrep 'pgsteal|pgscan'` to sanity-check the same counters your script ships.

Step 4 — Operationalize
Chart steal ratio on a host dashboard, tie alerts to the owning app team, and document when to add RAM versus tune application cache settings.



## SPL

```spl
index=os sourcetype=custom:meminfo_delta host=*
| stats avg(pgscan_direct) as scan_avg, avg(pgsteal_direct) as steal_avg by host
| eval steal_ratio=if(scan_avg>0, steal_avg/scan_avg, null())
| where scan_avg>0 AND steal_ratio > 0.7
```

## Visualization

Timechart, Single Value

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
