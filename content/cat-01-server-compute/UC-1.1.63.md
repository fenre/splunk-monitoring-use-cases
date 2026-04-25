<!-- AUTO-GENERATED from UC-1.1.63.json — DO NOT EDIT -->

---
id: "1.1.63"
title: "Dropped Packets by Network Interface"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.1.63 · Dropped Packets by Network Interface

## Description

Surfaces interfaces where the cumulative **dropped** counters are non-zero in the lookback, then trends the maximum of the combined in+out drop count in each bucket so you can see whether the condition persists.

## Value

Packet drops on the host precede many application time-outs; this view nudges you toward buffer, ring, and coalesce tuning with NIC vendor guidance before the problem scales up.

## Implementation

Not every `interfaces` build exposes per-interface drop fields—confirm with **Fieldsummary** in Search. If fields are missing, add a `custom:ethtool` or `nstat` script for the counters you need instead of this exact SPL.

## Detailed Implementation

Prerequisites
• Fields **dropped_in** and **dropped_out** (or renames) must exist. If the TA’s **interfaces** sample omits them, extend the scripted input to parse `rx_dropped` / `tx_dropped` from `ip -s link` or `/proc/net/dev`.

Step 1 — Configure data collection
Prefer a steady poll so **latest** per host+interface in the **stats** is meaningful. For alerts, you often want **delta** drops per interval instead of a never-decreasing counter; use `delta` + `where increase>0` in a follow-on iteration.

Step 2 — Create the search and report
`timechart` is ideal for a dashboard; add `| where max>0` in an alert with `bucket`ed five-minute **stats** for paging.

**CIM note** — Standard **All_Traffic** does not carry Linux **drop** counters; this UC stays on raw **interfaces** until you model drops into a custom data model or metric store.


Step 3 — Validate
`ethtool -S iface` and `nstat` / `ss -i` (tooling varies) on the host; for drivers with **ring** size controls, also capture `ethtool -g` before/after tuning.

Step 4 — Operationalize
Route NIC drops with the same timeline as switch **CRC** and **error** counters for fabric-side proof.



## SPL

```spl
index=os sourcetype=interfaces host=*
| bin _time span=5m
| stats max(dropped_in) as di max(dropped_out) as do by host, interface, _time
| eval total_dropped=di+do
| where total_dropped>0
| timechart max(total_dropped) by host, interface
```

## Visualization

Timechart, Alert

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
