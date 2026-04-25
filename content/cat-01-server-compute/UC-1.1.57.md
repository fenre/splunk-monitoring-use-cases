<!-- AUTO-GENERATED from UC-1.1.57.json — DO NOT EDIT -->

---
id: "1.1.57"
title: "ARP Table Overflow Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.1.57 · ARP Table Overflow Detection

## Description

Compares the live ARP cache size to a configured or sampled maximum, alerting when the table is most of the way to exhaustion—whether from scans, virtual churn, or mis-set limits.

## Value

A full ARP table stops new on-net conversations cold; this control buys time to raise `gc_thresh*`, find spoofing, or break L2 storms before a host goes dark.

## Implementation

Count non-header lines in `/proc/net/arp` (or your script’s equivalent) into `arp_entry_count`. Set `max_entries` from a maintained lookup or from `/proc/sys/net/ipv4/neigh/default/gc_thresh3` on hosts where that maps to your policy; the sample SPL used a static `max_entries=1024` before—prefer dynamic `max_entries` to avoid one-size-fits-all false work.

## Detailed Implementation

Prerequisites
• Provide both **arp_entry_count** and a realistic **max_entries** per host class (lookup CSV or field from the same script that reads `gc_thresh` values).

Step 1 — Configure data collection
Run every minute on hypervisors and routers where ARP pressure first appears. Document IPv4 vs IPv6 if you split families.

Step 2 — Create the search and alert
The SPL in the JSON body expects both fields. If you still use a static max, set `| eval max_entries=coalesce(max_entries,1024)` after **stats**.

**Understanding this SPL** — Simple utilization check with guard `max_entries>0` to avoid divide-by-zero artifacts.


Step 3 — Validate
Compare `arp_entry_count` to `wc -l /proc/net/arp` minus the header, and to `ip neigh show | wc` for humans on the same second.

Step 4 — Operationalize
When paging, also capture `dmesg` for **neighbour table overflow** lines and work with the network team on VLAN design or storm control.



## SPL

```spl
index=os sourcetype=custom:arp host=*
| stats latest(arp_entry_count) as arp_entry_count, latest(max_entries) as max_entries by host
| eval max_entries=coalesce(max_entries, 1024)
| where arp_entry_count > (max_entries * 0.8)
```

## Visualization

Gauge, Alert

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
